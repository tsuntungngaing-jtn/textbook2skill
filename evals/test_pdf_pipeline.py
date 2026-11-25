import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from extraction_metrics import score
from pdf_pipeline import run
try:
    import pymupdf as pm
except ImportError:
    pm=None

class MetricsTests(unittest.TestCase):
    def test_sign_and_missing(self):
        h='a'*64
        g={'source_sha256':h,'items':[{'id':'a','kind':'number','value':'-0.15'},{'id':'b','kind':'unit','value':'MPa'}]}
        p={'source_sha256':h,'items':[{'id':'a','kind':'number','value':'0.15'}]}
        r=score(g,p)
        self.assertEqual(r['overall']['correct'],0)
        self.assertEqual(r['missing_ids'],['b'])
        self.assertEqual(r['mismatch_ids'],['a'])
    def test_whitespace(self):
        h='a'*64
        g={'source_sha256':h,'items':[{'id':'a','kind':'unit','value':'N   m'}]}
        p={'source_sha256':h,'items':[{'id':'a','kind':'unit','value':'N m'}]}
        self.assertEqual(score(g,p)['overall']['recall'],1)
    def test_source_mismatch(self):
        with self.assertRaises(ValueError): score({'source_sha256':'a'*64},{'source_sha256':'b'*64})

@unittest.skipIf(pm is None,'Optional PyMuPDF unavailable')
class PDFTests(unittest.TestCase):
    def test_native(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'s.pdf'
            with pm.open() as doc:
                p=doc.new_page();p.insert_text((50,50),'Synthetic -0.15 MPa');p.draw_rect(pm.Rect(50,80,120,140));doc.save(src)
            out=run(src,root/'out','native',1,1,72)
            data=json.loads((out/'pages.json').read_text())
            self.assertIn('-0.15 MPa',data['pages'][0]['text'])
            self.assertGreater(data['pages'][0]['vector_count'],0)
            self.assertTrue((out/'page-00001.png').is_file())
            with self.assertRaises(FileExistsError): run(src,out,'native',1,1,72)
if __name__=='__main__': unittest.main()
