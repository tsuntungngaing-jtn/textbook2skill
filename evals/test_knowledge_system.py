import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from knowledge_graph import validate, paths, search_evidence
from knowledge_reasoning import decide, adjudicate, compare_quantities
from learning_state import new_state, ready_tasks, transition, fingerprint, ablation

PRED={"node_id":"R","scope":"s","input":"x","op":"le","threshold":10,"unit":"mm"}

def graph():
    return {"sources":[{"id":"S","title":"Synthetic","edition":"1","sha256":"a"*64}],
            "evidence":[{"id":"E","source_id":"S","chapter":"1","locator":"p1","summary":"assembly time","status":"reviewed","reviewer":"B","review_log":"log"}],
            "nodes":[{"id":i,"type":t,"title":i,"status":"reviewed","evidence_ids":["E"],**({"predicate":PRED.copy()} if i=="R" else {})} for i,t in [("A","concept"),("B","concept"),("R","rule")]],
            "edges":[{"id":i,"from":a,"to":b,"type":"prerequisite_of","scope":"s","status":"reviewed","evidence_ids":["E"]} for i,a,b in [("ab","A","B"),("br","B","R")]]}

class KnowledgeTests(unittest.TestCase):
    def test_graph_paths(self):
        g=graph()
        self.assertEqual(validate(g)["edges"],2)
        self.assertIn(["A","B","R"],[x["node_path"] for x in paths(g,["A"])["paths"]])
        self.assertEqual(search_evidence(g,"assembly")[0]["evidence"]["id"],"E")
    def test_prerequisite_cycle(self):
        g=graph();g["edges"].append({**g["edges"][0],"id":"ra","from":"R","to":"A"})
        with self.assertRaises(ValueError): validate(g)
        g["edges"][-1]["type"]="related_to";validate(g)
    def test_missing_evidence(self):
        g=graph();g["evidence"][0]["status"]="candidate"
        with self.assertRaises(ValueError): validate(g)
    def test_rule_scope_binding(self):
        facts={"x":{"value":8,"unit":"mm","scope":"s","origin":"measurement","reviewed":True}}
        self.assertEqual(decide(graph(),[PRED],facts,"s")["status"],"PASS")
        self.assertEqual(decide(graph(),[{**PRED,"threshold":20}],facts,"s")["status"],"UNKNOWN")
        self.assertEqual(decide(graph(),[PRED],{},"s")["status"],"UNKNOWN")
        facts["x"]["value"]=12
        self.assertEqual(decide(graph(),[PRED],facts,"s")["status"],"FAIL")
    def test_review_conflict(self):
        c={"id":"C","author":"A","scope":"s"}
        r={"claim_id":"C","reviewer":"B","scope":"s","independent_read":True,"review_log":"audit","evidence_ids":["E"],"verdict":"SUPPORTED"}
        self.assertEqual(adjudicate(graph(),c,[r])["status"],"SUPPORTED_BY_REVIEW")
        self.assertEqual(adjudicate(graph(),c,[r,{**r,"reviewer":"D","verdict":"CONTRADICTED"}])["status"],"CONFLICT_REVIEW_REQUIRED")
        self.assertEqual(adjudicate(graph(),c,[{**r,"reviewer":"A"}])["status"],"NEEDS_EVIDENCE")
    def test_quantity(self):
        a={"quantity":"stress","scope":"s","value":10,"unit":"MPa"}
        self.assertEqual(compare_quantities(a,a)["status"],"NUMERIC_MATCH")
        self.assertEqual(compare_quantities(a,{**a,"scope":"other"})["status"],"SCOPE_UNRESOLVED")
    def test_pint(self):
        try: import pint
        except ImportError: self.skipTest("optional Pint unavailable")
        a={"quantity":"stress","scope":"s","value":1,"unit":"MPa"}
        self.assertEqual(compare_quantities(a,{**a,"unit":"kPa","value":1000},1e-9)["status"],"NUMERIC_MATCH")
    def test_checkpoint(self):
        plan={"tasks":[{"id":"a","role":"chapter","scope":"s","depends_on":[]},{"id":"b","role":"verification","scope":"s","depends_on":["a"]}]}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"a.json";p.write_text("candidate")
            s=new_state(plan)
            self.assertEqual(ready_tasks(plan,s,td),["a"])
            s=transition(plan,s,td,"a","RUNNING","A")
            s=transition(plan,s,td,"a","DONE","A",["a.json"])
            with self.assertRaises(ValueError): transition(plan,s,td,"b","RUNNING","A")
            self.assertEqual(ready_tasks(plan,s,td),["b"])
            p.write_text("changed")
            with self.assertRaises(ValueError): ready_tasks(plan,s,td)
    def test_ablation_missing(self):
        plan={"cases":[{"id":i,"split":"holdout"} for i in ("a","b")],"metrics":["accuracy"]}
        r={"plan_sha256":fingerprint(plan),"configuration":"frozen","results":[{"id":"a","scores":{"accuracy":1}}]}
        result=ablation(plan,r,{**r,"results":[]})
        self.assertEqual(result["metrics"]["accuracy"]["paired_delta"],-0.5)
        self.assertEqual(result["missing_candidate"],["a","b"])
if __name__=="__main__": unittest.main()
