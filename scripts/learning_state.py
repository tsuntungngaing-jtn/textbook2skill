"""Local task ledger and paired ablation evaluator. Does not launch agents."""
import hashlib
import json
from pathlib import Path
import os
import tempfile
from knowledge_graph import index, present

ROLES={"extraction","chapter","graph","math","verification","conflict","adjudication","evaluation"}

def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def plan_tasks(plan):
    tasks=index(plan["tasks"],"task")
    for t in tasks.values():
        if t.get("role") not in ROLES or not present(t.get("scope")) or not isinstance(t.get("depends_on"),list) or any(d not in tasks or d==t["id"] for d in t["depends_on"]):
            raise ValueError("Invalid task role, scope or dependency")
    finished=set()
    while len(finished)<len(tasks):
        ready={i for i,t in tasks.items() if i not in finished and set(t["depends_on"])<=finished}
        if not ready: raise ValueError("Cyclic task dependencies")
        finished.update(ready)
    return tasks

def new_state(plan):
    tasks=plan_tasks(plan)
    return {"plan_sha256":fingerprint(plan),"tasks":{i:{"status":"PENDING"} for i in tasks}}

def artifact(root, relative):
    root=Path(root).resolve()
    if not present(relative) or Path(relative).is_absolute(): raise ValueError("Relative artifact path required")
    p=(root/relative).resolve()
    if not p.is_relative_to(root) or not p.is_file(): raise ValueError("Artifact missing or outside workspace")
    return p

def verify_state(plan,state,root):
    tasks=plan_tasks(plan)
    if state.get("plan_sha256")!=fingerprint(plan) or set(state["tasks"])!=set(tasks):
        raise ValueError("Plan/state mismatch")
    for i,r in state["tasks"].items():
        if r["status"] not in {"PENDING","RUNNING","DONE","FAILED","BLOCKED"}:
            raise ValueError("Invalid task state")
        if r["status"] in {"RUNNING","DONE"} and any(state["tasks"][d]["status"]!="DONE" for d in tasks[i]["depends_on"]):
            raise ValueError("Unfinished dependency")
        if r["status"]=="DONE":
            if not present(r.get("worker")) or not r.get("artifacts"): raise ValueError("Missing worker/artifacts")
            for a in r["artifacts"]:
                if file_hash(artifact(root,a["path"]))!=a["sha256"]:
                    raise ValueError("Artifact changed; invalidate downstream before resume")
    return tasks

def ready_tasks(plan,state,root):
    tasks=verify_state(plan,state,root)
    return [i for i,t in tasks.items() if state["tasks"][i]["status"]=="PENDING" and all(state["tasks"][d]["status"]=="DONE" for d in t["depends_on"])]

def transition(plan,state,root,task,status,worker=None,outputs=None,reason=None):
    tasks=verify_state(plan,state,root)
    old=state["tasks"][task]
    allowed={"PENDING":{"RUNNING","BLOCKED"},"RUNNING":{"DONE","FAILED","BLOCKED"},"FAILED":{"PENDING"},"BLOCKED":{"PENDING"},"DONE":set()}
    if status not in allowed[old["status"]]: raise ValueError("Invalid transition")
    if status=="RUNNING":
        if task not in ready_tasks(plan,state,root) or not present(worker): raise ValueError("Task not ready or worker missing")
        if tasks[task]["role"]=="verification":
            authors={r.get("worker") for i,r in state["tasks"].items() if tasks[i]["scope"]==tasks[task]["scope"] and tasks[i]["role"] in {"chapter","extraction","graph"} and r["status"]=="DONE"}
            if worker in authors: raise ValueError("Verifier must be separate from claim authors")
    if status=="DONE":
        if worker!=old.get("worker") or not outputs: raise ValueError("Worker mismatch or missing outputs")
        artifacts=[{"path":p,"sha256":file_hash(artifact(root,p))} for p in outputs]
        record={"status":status,"worker":worker,"artifacts":artifacts}
    elif status=="RUNNING": record={"status":status,"worker":worker}
    elif status in {"FAILED","BLOCKED","PENDING"}:
        if not present(reason): raise ValueError("Reason required")
        record={"status":status,"reason":reason}
    result=json.loads(json.dumps(state))
    result["tasks"][task]=record
    verify_state(plan,result,root)
    return result

def save_checkpoint(path,state):
    """Atomic replace; coordinator must be the only writer."""
    path=Path(path)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix=".checkpoint-")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(state,f,ensure_ascii=False,indent=2,allow_nan=False); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def ablation(plan,baseline,candidate):
    """Paired independent case scores; no dropping missing runs."""
    cases=index(plan["cases"],"case")
    metrics=plan["metrics"]
    if not cases or not metrics or len(set(metrics))!=len(metrics): raise ValueError("Empty or duplicate metrics")
    for c in cases.values():
        if c.get("split")!="holdout": raise ValueError("Holdout only")
    def read(run):
        if run.get("plan_sha256")!=fingerprint(plan) or not present(run.get("configuration")):
            raise ValueError("Run plan/configuration mismatch")
        rows=index(run["results"],"result")
        if set(rows)-set(cases): raise ValueError("Unknown result")
        for r in rows.values():
            if set(r["scores"])!=set(metrics) or any(type(v) not in (int,float) or not 0<=v<=1 for v in r["scores"].values()):
                raise ValueError("Scores must be in [0,1]")
        return rows
    a,b=read(baseline),read(candidate)
    # Missing cases are explicitly failures, not excluded.
    def val(rows,i,m): return rows[i]["scores"][m] if i in rows else 0
    return {"cases":len(cases),"missing_baseline":sorted(set(cases)-set(a)),"missing_candidate":sorted(set(cases)-set(b)),"metrics":{m:{"baseline":sum(val(a,i,m) for i in cases)/len(cases),"candidate":sum(val(b,i,m) for i in cases)/len(cases),"paired_delta":sum(val(b,i,m)-val(a,i,m) for i in cases)/len(cases)} for m in metrics},"status":"PAIRED_DESCRIPTIVE_NOT_CAUSAL"}
