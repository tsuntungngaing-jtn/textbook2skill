"""Evidence-linked graph. Validation checks structure, not source truth."""
from collections import deque
import re

NODE_TYPES = {"concept","formula","assumption","constraint","rule","procedure","case","evidence","script"}
RELATIONS = {"prerequisite_of","derived_from","depends_on","valid_under","applies_to","equivalent_to","contradicts","supported_by","implemented_by","related_to"}
STATES = {"candidate","reviewed","blocked"}

def index(rows, name):
    result={}
    for r in rows:
        key=r.get("id")
        if not isinstance(key,str) or not key.strip() or key in result:
            raise ValueError(f"Invalid or duplicate {name} ID: {key}")
        result[key]=r
    return result

def present(value):
    return isinstance(value,str) and bool(value.strip())

def validate(graph):
    sources=index(graph["sources"],"source")
    evidence=index(graph["evidence"],"evidence")
    nodes=index(graph["nodes"],"node")
    edges=index(graph["edges"],"edge")
    for s in sources.values():
        if not all(present(s.get(k)) for k in ("title","edition")):
            raise ValueError("Source title and edition required")
        if not re.fullmatch(r"[0-9a-f]{64}",str(s.get("sha256",""))):
            raise ValueError("Source SHA256 required")
    for e in evidence.values():
        if e.get("source_id") not in sources or not present(e.get("locator")) or not present(e.get("chapter")) or e.get("status") not in STATES:
            raise ValueError("Invalid evidence locator or status")
        if e["status"]=="reviewed" and not all(present(e.get(k)) for k in ("reviewer","review_log")):
            raise ValueError("Reviewed evidence needs reviewer and review log")
    def check_record(r):
        refs=r.get("evidence_ids")
        if r.get("status") not in STATES or not isinstance(refs,list) or any(x not in evidence for x in refs):
            raise ValueError("Invalid evidence references or status")
        if r["status"]=="reviewed" and (not refs or any(evidence[x]["status"]!="reviewed" for x in refs)):
            raise ValueError("Reviewed item requires reviewed evidence")
    for n in nodes.values():
        if n.get("type") not in NODE_TYPES or not present(n.get("title")):
            raise ValueError("Invalid node type/title")
        check_record(n)
    adj={n:[] for n in nodes}
    degree={n:0 for n in nodes}
    for e in edges.values():
        a,b=e.get("from"),e.get("to")
        if a not in nodes or b not in nodes or e.get("type") not in RELATIONS or not present(e.get("scope")):
            raise ValueError("Invalid edge endpoints/type/scope")
        check_record(e)
        if e["status"]=="reviewed" and any(nodes[x]["status"]!="reviewed" for x in (a,b)):
            raise ValueError("Reviewed relation requires reviewed endpoints")
        if e["type"]=="prerequisite_of" and e["status"]!="blocked":
            adj[a].append(b); degree[b]+=1
    q=deque(n for n in degree if degree[n]==0)
    count=0
    while q:
        a=q.popleft(); count+=1
        for b in adj[a]:
            degree[b]-=1
            if degree[b]==0: q.append(b)
    if count!=len(nodes):
        raise ValueError("Prerequisite cycle; adjudicate rather than delete evidence")
    return {"sources":len(sources),"evidence":len(evidence),"nodes":len(nodes),"edges":len(edges),"status":"STRUCTURE_PASS"}

def paths(graph, seeds, max_hops=3, limit=100, reviewed_only=True):
    """Bounded bidirectional traversal; preserve actual edge direction and evidence."""
    validate(graph)
    nodes=index(graph["nodes"],"node")
    if type(max_hops)!=int or not 0<=max_hops<=8 or type(limit)!=int or not 1<=limit<=10000:
        raise ValueError("Invalid traversal bounds")
    if any(s not in nodes for s in seeds):
        raise ValueError("Unknown seed")
    adj={n:[] for n in nodes}
    for e in sorted(graph["edges"],key=lambda x:x["id"]):
        if e["status"]=="blocked" or (reviewed_only and e["status"]!="reviewed"): continue
        adj[e["from"]].append((e["to"],e))
        adj[e["to"]].append((e["from"],e))
    q=deque((s,[],[s]) for s in sorted(set(seeds)) if nodes[s]["status"]!="blocked" and (not reviewed_only or nodes[s]["status"]=="reviewed"))
    out=[]
    while q and len(out)<limit:
        n,route,visited=q.popleft()
        out.append({"node":n,"path":route,"node_path":visited,"evidence_ids":sorted(set(nodes[n]["evidence_ids"]+[r for e in route for r in e["evidence_ids"]]))})
        if len(route)>=max_hops: continue
        for dest,e in adj[n]:
            if dest in visited or nodes[dest]["status"]=="blocked" or (reviewed_only and nodes[dest]["status"]!="reviewed"): continue
            if len(q)+len(out)>=limit: break
            q.append((dest,route+[e],visited+[dest]))
    return {"paths":out,"limit_reached":len(out)==limit,"status":"RETRIEVAL_NOT_VERIFICATION"}

def search_evidence(graph, query, limit=20):
    validate(graph)
    if not present(query) or type(limit)!=int or not 1<=limit<=1000:
        raise ValueError("Invalid query or limit")
    tokens=set(query.casefold().split())
    results=[]
    for e in graph["evidence"]:
        if e["status"]!="reviewed": continue
        text=" ".join(str(e.get(k,"")) for k in ("chapter","locator","summary","keywords")).casefold()
        score=sum(t in text for t in tokens)
        if score: results.append((score,e))
    results.sort(key=lambda pair:(-pair[0],pair[1]["id"]))
    return [{"score":s,"evidence":e} for s,e in results[:limit]]
