"""Deterministic predicates, unit checks and independent evidence adjudication."""
import math
import operator
from knowledge_graph import validate, index, present

OPS={"lt":operator.lt,"le":operator.le,"eq":operator.eq,"ge":operator.ge,"gt":operator.gt,"ne":operator.ne}

def convert(value, source_unit, target_unit):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError("Finite numeric input required")
    if not present(source_unit) or not present(target_unit):
        raise ValueError("Explicit units required")
    if source_unit==target_unit: return float(value)
    import pint
    registry=pint.UnitRegistry()
    result=registry.Quantity(value,source_unit).to(target_unit).magnitude
    if not math.isfinite(result): raise ValueError("Nonfinite conversion")
    return float(result)

def compare_quantities(a,b,relative_tolerance=0,absolute_tolerance=0):
    """Exact scope/quantity identity required; comparison is not scientific verification."""
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in (relative_tolerance,absolute_tolerance)):
        raise ValueError("Invalid tolerance")
    for k in ("quantity","scope"):
        if not present(a.get(k)) or a.get(k)!=b.get(k):
            return {"status":"SCOPE_UNRESOLVED"}
    try:
        x=convert(a["value"],a["unit"],a["unit"])
        y=convert(b["value"],b["unit"],a["unit"])
    except (ImportError,ValueError,TypeError,KeyError,ArithmeticError):
        return {"status":"UNKNOWN"}
    except Exception as exc:
        if exc.__class__.__module__.startswith("pint"): return {"status":"INCOMPATIBLE_UNITS"}
        raise
    return {"status":"NUMERIC_MATCH" if math.isclose(x,y,rel_tol=relative_tolerance,abs_tol=absolute_tolerance) else "NUMERIC_DISAGREEMENT","first":x,"second":y,"unit":a["unit"]}

def adjudicate(graph, claim, reviews):
    """Require separate author/reviewer, evidence and aligned scope; no majority voting."""
    validate(graph)
    ev=index(graph["evidence"],"evidence")
    if not all(present(claim.get(k)) for k in ("id","author","scope")): raise ValueError("Invalid claim")
    accepted=[]; rejected=[]
    for r in reviews:
        refs=r.get("evidence_ids",[])
        valid=(r.get("claim_id")==claim["id"] and present(r.get("reviewer")) and r["reviewer"]!=claim["author"] and r.get("scope")==claim["scope"] and r.get("independent_read") is True and present(r.get("review_log")) and isinstance(refs,list) and bool(refs) and all(x in ev and ev[x]["status"]=="reviewed" for x in refs) and r.get("verdict") in {"SUPPORTED","CONTRADICTED","CONDITIONALLY_VALID","EQUIVALENT","COMPLEMENTARY","INSUFFICIENT_EVIDENCE"})
        (accepted if valid else rejected).append(r)
    kinds={r["verdict"] for r in accepted}
    if "CONTRADICTED" in kinds: status="CONFLICT_REVIEW_REQUIRED"
    elif not kinds or kinds-{"SUPPORTED","EQUIVALENT"}: status="NEEDS_EVIDENCE"
    else: status="SUPPORTED_BY_REVIEW"
    return {"status":status,"accepted":accepted,"rejected":rejected,"evidence_ids":sorted({e for r in accepted for e in r["evidence_ids"]}),"automatic_truth_certification":False}

def decide(graph, rules, facts, scope):
    """Conjunctive typed hard constraints. Missing or unreviewed evidence never passes."""
    validate(graph)
    nodes=index(graph["nodes"],"node")
    if not rules or not present(scope): return {"status":"UNKNOWN","checks":[]}
    checks=[]
    for rule in rules:
        n=nodes.get(rule.get("node_id"),{})
        check={"rule":rule.get("node_id"),"status":"UNKNOWN"}
        if n.get("type")=="rule" and n.get("status")=="reviewed" and n.get("predicate")==rule and rule.get("scope")==scope and rule.get("op") in OPS:
            f=facts.get(rule.get("input"),{})
            if f.get("scope")==scope and f.get("reviewed") is True and present(f.get("origin")):
                try:
                    x=convert(f["value"],f["unit"],rule["unit"])
                    y=convert(rule["threshold"],rule["unit"],rule["unit"])
                    check.update(status="PASS" if OPS[rule["op"]](x,y) else "FAIL",actual=x,threshold=y,unit=rule["unit"],evidence_ids=n["evidence_ids"],origin=f["origin"])
                except (ImportError,ValueError,TypeError,KeyError,ArithmeticError): pass
                except Exception as exc:
                    if not exc.__class__.__module__.startswith("pint"): raise
        checks.append(check)
    statuses={c["status"] for c in checks}
    return {"status":"FAIL" if "FAIL" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "PASS","checks":checks,"scope":scope}
