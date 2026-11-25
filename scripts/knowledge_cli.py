"""CLI for the v0.3.0 local knowledge tools."""
import argparse
import json
from pathlib import Path
from knowledge_graph import validate, paths, search_evidence
from knowledge_reasoning import decide, adjudicate, compare_quantities
from learning_state import new_state, ready_tasks, transition, save_checkpoint, ablation, fingerprint

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest="cmd",required=True)
    for cmd, fields in {
        "validate":["graph"],"paths":["graph","seed"],"search":["graph","query"],
        "decide":["graph","request"],"review":["graph","request"],"quantity":["request"],
        "init-state":["plan","state"],"ready":["plan","state","root"],
        "transition":["plan","state","root","request"],"ablation":["plan","baseline","candidate"],
        "hash-plan":["plan"]
    }.items():
        q=s.add_parser(cmd)
        for f in fields: q.add_argument(f)
        if cmd=="paths": q.add_argument("--hops",type=int,default=3)
    a=p.parse_args()
    if a.cmd=="validate": result=validate(load(a.graph))
    elif a.cmd=="paths": result=paths(load(a.graph),[a.seed],a.hops)
    elif a.cmd=="search": result=search_evidence(load(a.graph),a.query)
    elif a.cmd=="decide":
        r=load(a.request); result=decide(load(a.graph),r["rules"],r["facts"],r["scope"])
    elif a.cmd=="review":
        r=load(a.request); result=adjudicate(load(a.graph),r["claim"],r["reviews"])
    elif a.cmd=="quantity":
        r=load(a.request); result=compare_quantities(r["first"],r["second"],r.get("relative_tolerance",0),r.get("absolute_tolerance",0))
    elif a.cmd=="init-state":
        result=new_state(load(a.plan))
        with Path(a.state).open("x",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
    elif a.cmd=="ready": result=ready_tasks(load(a.plan),load(a.state),a.root)
    elif a.cmd=="transition":
        result=transition(load(a.plan),load(a.state),a.root,**load(a.request))
        save_checkpoint(a.state,result)
    elif a.cmd=="ablation": result=ablation(load(a.plan),load(a.baseline),load(a.candidate))
    else: result={"plan_sha256":fingerprint(load(a.plan))}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))

if __name__=="__main__": main()
