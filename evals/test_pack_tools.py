import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from init_pack import initialize
from validate_pack import validate

class PackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=initialize(Path(self.temp.name)/'pack')
    def test_empty_is_structural_only(self):
        r=validate(self.root); self.assertEqual(r['structural_status'],'PASS'); self.assertTrue(r['empty_pack']); self.assertEqual(r['semantic_validation'],'NOT_ASSESSED')
    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError): initialize(self.root)
    def test_bad_source(self):
        (self.root/'concepts.jsonl').write_text(json.dumps({'id':'C1','title':'Example','evidence':[{'source_id':'missing','locator':'1'}],'support':'source','status':'verified','content':{'meaning':'test'}}),encoding='utf-8')
        self.assertEqual(validate(self.root)['structural_status'],'FAIL')
    def test_verified_without_evidence(self):
        (self.root/'concepts.jsonl').write_text(json.dumps({'id':'C1','title':'Example','evidence':[],'support':'source','status':'verified','content':{'meaning':'test'}}),encoding='utf-8')
        self.assertEqual(validate(self.root)['structural_status'],'FAIL')
    def test_valid_synthetic(self):
        s={'id':'S1','title':'Synthetic test','edition':'1','locator':'test','sha256':None,'access':'synthetic','rights':'original'}
        (self.root/'source-index.json').write_text(json.dumps({'sources':[s]}),encoding='utf-8')
        (self.root/'concepts.jsonl').write_text(json.dumps({'id':'C1','title':'Example','evidence':[{'source_id':'S1','locator':'section 1'}],'support':'source','status':'verified','content':{'meaning':'test'}}),encoding='utf-8')
        self.assertEqual(validate(self.root)['structural_status'],'PASS')
if __name__=='__main__': unittest.main()
