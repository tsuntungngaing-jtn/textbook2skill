import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from extraction_suite import normalize_mineru,page_compare,axis,digitize,freeze_plan,evaluate
H='a'*64

class SuiteTests(unittest.TestCase):
    def test_mineru_mapping(self):
        p={'metadata':{'producer':{'name':'mineru','version':'4.0.0'}},'pages':[{'page_idx':0,'blocks':[{'type':'text','content':'-0.15 MPa'},{'type':'equation','content':'x'}]}]}
        r=normalize_mineru(p,{'0':5,'1':6},H)
        self.assertEqual(r['pages'][0]['page'],5); self.assertEqual(r['pages'][0]['text'],'-0.15 MPa'); self.assertEqual(len(r['pages'][0]['blocks']),2); self.assertEqual(r['missing_pages'],[6])
    def test_compare(self):
        a={'source_sha256':H,'pages':[{'page':1,'text':'-0.15 MPa'},{'page':2,'text':'x'}]}
        b={'source_sha256':H,'pages':[{'page':1,'text':'0.15 MPa'}]}
        r=page_compare(a,b); self.assertAlmostEqual(r['pages'][0]['distance'],1/9); self.assertEqual(r['missing'],[2])
    def test_axes(self):
        self.assertAlmostEqual(axis(50,100,0,0,10),5); self.assertAlmostEqual(axis(50,0,100,1,100,'log10'),10)
        with self.assertRaises(ValueError): axis(101,0,100,0,10)
    def test_chart(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'synthetic.png'; im=Image.new('RGB',(11,11),'white'); ImageDraw.Draw(im).line((0,5,10,5),fill=(255,0,0)); im.save(p)
            cfg={'rgb':[255,0,0],'tolerance':0,'roi':[0,0,11,11],'x_axis':[0,10,0,10,'linear'],'y_axis':[10,0,0,10,'linear'],'max_spread_px':2}
            r=digitize(p,cfg); self.assertEqual(len(r['points']),11); self.assertEqual(r['points'][5]['y'],5); self.assertEqual(r['missing_columns'],0)
    def test_holdout(self):
        a={'id':'dev','source_sha256':H,'page':1,'split':'dev','stratum':'formula'}; b={**a,'id':'test','page':2,'split':'holdout'}
        with self.assertRaises(ValueError): freeze_plan({'cases':[a,{**b,'page':1}]})
        f=freeze_plan({'cases':[a,b]}); h=f['plan_sha256']; row={'case_id':'test','id':'unit','kind':'unit','value':'MPa'}
        r=evaluate(f,{'plan_sha256':h,'items':[row]},{'plan_sha256':h,'items':[{**row,'value':'mPa'}]})
        self.assertEqual(r['overall']['correct'],0); self.assertEqual(r['unresolved_critical_fields'],[['test','unit']])
        r=evaluate(f,{'plan_sha256':h,'items':[row]},{'plan_sha256':h,'items':[]}); self.assertEqual(r['overall']['missing'],1)

if __name__=='__main__': unittest.main()
