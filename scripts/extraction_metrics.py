"""Strict literal transcription metrics, not the OmniDocBench evaluator."""
import argparse
import json
import re
from pathlib import Path
KINDS=('text','number','unit','formula','table_cell','figure_label','reading_order')

def score(gold,pred):
    h=gold.get('source_sha256')
    if not isinstance(h,str) or not re.fullmatch('[0-9a-fA-F]{64}',h) or h!=pred.get('source_sha256'):
        raise ValueError('Source SHA-256 mismatch')
    def index(obj):
        rows={}
        for r in obj['items']:
            i,k,v=r['id'],r['kind'],r['value']
            if not isinstance(i,str) or not i.strip() or i in rows or k not in KINDS or not isinstance(v,str):
                raise ValueError('Invalid or duplicate item')
            rows[i]=(k,' '.join(v.split()))
        return rows
    g,p=index(gold),index(pred)
    correct={i for i in g.keys() & p.keys() if g[i]==p[i]}
    def metric(a,b,c):
        return {'gold':a,'predicted':b,'correct':c,'precision':c/b if b else None,'recall':c/a if a else None,'f1':2*c/(a+b) if a+b else None}
    return {'overall':metric(len(g),len(p),len(correct)),
        'by_kind':{k:metric(sum(x[0]==k for x in g.values()),sum(x[0]==k for x in p.values()),sum(g[i][0]==k for i in correct)) for k in KINDS},
        'missing_ids':sorted(g.keys()-p.keys()),'extra_ids':sorted(p.keys()-g.keys()),'mismatch_ids':sorted((g.keys() & p.keys())-correct)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('gold',type=Path);p.add_argument('pred',type=Path)
    a=p.parse_args()
    print(json.dumps(score(json.loads(a.gold.read_text(encoding='utf-8')),json.loads(a.pred.read_text(encoding='utf-8'))),indent=2,ensure_ascii=False))
