"""Independent extraction utilities. All extracted values are candidates, not verified knowledge."""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import zipfile
from importlib.metadata import version
from pathlib import Path
from statistics import median


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, data):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def valid_hash(h):
    return isinstance(h, str) and bool(re.fullmatch('[0-9a-f]{64}', h))


def normalize_mineru(payload, page_map, source_sha256):
    """MinerU 4 structured_content only; retain all blocks, compare plain text separately."""
    if not valid_hash(source_sha256):
        raise ValueError('Invalid source hash')
    producer = payload['metadata']['producer']
    if producer['name'].lower() != 'mineru' or not producer['version'].startswith('4.'):
        raise ValueError('Unsupported producer; inspect schema')
    pages, seen = [], set()
    if not isinstance(page_map, dict) or set(page_map) != {str(i) for i in range(len(page_map))} or any(type(n) is not int or n < 1 for n in page_map.values()) or len(set(page_map.values())) != len(page_map):
        raise ValueError('Invalid zero-based subset to physical page map')
    for p in payload['pages']:
        idx = p['page_idx']
        if type(idx) is not int or str(idx) not in page_map or idx in seen:
            raise ValueError('Unexpected or duplicate page index')
        seen.add(idx)
        blocks = p['blocks']
        if not isinstance(blocks, list) or any(not isinstance(b, dict) for b in blocks):
            raise ValueError('Invalid blocks')
        text = '\n'.join(b['content'] for b in blocks if b.get('type') == 'text' and isinstance(b.get('content'), str))
        pages.append({'page': page_map[str(idx)], 'text': text, 'blocks': blocks, 'status': 'UNREVIEWED'})
    return {'source_sha256': source_sha256, 'producer': producer, 'extensions': payload.get('extensions', {}), 'pages': sorted(pages, key=lambda p:p['page']), 'missing_pages': sorted(page_map[str(i)] for i in set(range(len(page_map)))-seen), 'text_scope': 'plain text blocks only; all other blocks retained raw'}


def mineru_run(source, output, start, end, tier='standard', timeout=3600):
    import pymupdf as pm
    source, output = Path(source).resolve(), Path(output).resolve()
    installed = version('mineru')
    exe = shutil.which('mineru-kit')
    if not installed.startswith('4.') or not exe or tier not in ('flash','basic','standard','advanced') or timeout <= 0:
        raise RuntimeError('Requires installed MinerU 4.x local CLI, supported tier and timeout')
    # Do not use a configured remote endpoint. Local model downloads may still occur.
    if os.environ.get('MINERU_API_URL') or os.environ.get('MINERU_API_KEY'):
        raise RuntimeError('Remove remote MinerU endpoint credentials before local parsing')
    h = sha(source)
    with pm.open(source) as d:
        if not d.is_pdf or d.needs_pass or not 1 <= start <= end <= len(d):
            raise ValueError('Readable PDF and valid inclusive physical range required')
        output.mkdir(parents=True, exist_ok=False)
        inp, out = output/'input', output/'output'
        inp.mkdir(); out.mkdir()
        with pm.open() as subset:
            subset.insert_pdf(d, from_page=start-1, to_page=end-1)
            subset.save(inp/'subset.pdf')
    mapping = {str(i):n for i,n in enumerate(range(start,end+1))}
    command = [exe,'parse',str(inp),'-o',str(out),'--format','zip','--tier',tier]
    manifest = {'source_sha256':h,'subset_sha256':sha(inp/'subset.pdf'),'page_map':mapping,'installed_version':installed,'requested_tier':tier,'command':command,'status':'INCOMPLETE'}
    save(output/'manifest.json',manifest)
    with (output/'parser.log').open('wb') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout, shell=False)
    archives = list(out.rglob('*.zip'))
    if len(archives) != 1:
        raise RuntimeError('Expected one ZIP; inspect log')
    with zipfile.ZipFile(archives[0]) as z:
        members = [i for i in z.infolist() if Path(i.filename).name == 'structured_content.json']
        if len(members) != 1 or members[0].file_size > 100*1024*1024:
            raise RuntimeError('Unexpected structured artifact')
        pages = normalize_mineru(json.loads(z.read(members[0])),mapping,h)
    if sha(source) != h:
        raise RuntimeError('Source changed')
    save(output/'pages.json',pages)
    save(output/'result.json',{'archive':str(archives[0].relative_to(output)),'archive_sha256':sha(archives[0]),'missing_pages':pages['missing_pages'],'status':'PARTIAL' if pages['missing_pages'] else 'PARSED_NOT_REVIEWED'})
    return output


def page_compare(a,b):
    if not valid_hash(a.get('source_sha256')) or a['source_sha256'] != b.get('source_sha256'):
        raise ValueError('Source mismatch')
    def index(obj):
        d = {}
        for p in obj['pages']:
            n = p['page']
            if type(n) is not int or n < 1 or n in d or not isinstance(p['text'],str):
                raise ValueError('Invalid page')
            d[n] = ' '.join(p['text'].split())
        return d
    def distance(x,y):
        if len(x)<len(y): x,y=y,x
        row=list(range(len(y)+1))
        for i,c in enumerate(x,1):
            nxt=[i]
            for j,d in enumerate(y,1): nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(c!=d)))
            row=nxt
        return row[-1]/max(len(x),len(y),1)
    x,y=index(a),index(b)
    return {'metric':'disagreement_not_accuracy','pages':[{'page':n,'distance':distance(x[n],y[n])} for n in sorted(x.keys()&y.keys())],'missing':sorted(x.keys()-y.keys()),'extra':sorted(y.keys()-x.keys())}


def axis(pixel, p0,p1,v0,v1,scale='linear'):
    if not all(math.isfinite(v) for v in (pixel,p0,p1,v0,v1)) or p0==p1 or v0==v1 or not min(p0,p1)<=pixel<=max(p0,p1):
        raise ValueError('Invalid anchors or extrapolation')
    t=(pixel-p0)/(p1-p0)
    if scale=='linear': return (1-t)*v0+t*v1
    if scale=='log10' and min(v0,v1)>0: return 10**((1-t)*math.log10(v0)+t*math.log10(v1))
    raise ValueError('Invalid scale')


def digitize(image, cfg):
    """Color-selected candidate points for a reviewed single-valued orthogonal XY curve."""
    from PIL import Image
    import numpy as np
    rgb=cfg['rgb']; tolerance=cfg['tolerance']; x0,y0,x1,y1=cfg['roi']
    if len(rgb)!=3 or any(type(c) is not int or not 0<=c<=255 for c in rgb) or not 0<=tolerance<=100 or not all(type(c) is int for c in (x0,y0,x1,y1)):
        raise ValueError('Invalid color or ROI')
    with Image.open(image) as im:
        if not 0<=x0<x1<=im.width or not 0<=y0<y1<=im.height:
            raise ValueError('ROI outside image')
        arr=np.asarray(im.convert('RGB').crop((x0,y0,x1,y1)),dtype=float)
    mask=np.linalg.norm(arr-np.array(rgb),axis=2)<=tolerance
    xa,ya=cfg['x_axis'],cfg['y_axis']
    # Check both axes even if no pixels match.
    axis(xa[0],*xa); axis(ya[0],*ya)
    spread=cfg['max_spread_px']
    if type(spread) is not int or spread<0: raise ValueError('Invalid spread')
    points=[]; missing=ambiguous=outside=0
    for j in range(mask.shape[1]):
        ys=np.flatnonzero(mask[:,j])+y0
        if not len(ys): missing+=1; continue
        if int(ys[-1]-ys[0])>spread: ambiguous+=1; continue
        px=x0+j; py=float(median(ys.tolist()))
        try:
            x=axis(px,*xa); y=axis(py,*ya)
            bounds=sorted([axis(float(ys[0]),*ya),axis(float(ys[-1]),*ya)])
        except ValueError: outside+=1; continue
        points.append({'px':px,'py':py,'x':x,'y':y,'stroke_y_bounds':bounds})
    return {'image_sha256':sha(image),'config':cfg,'points':points,'missing_columns':missing,'ambiguous_columns':ambiguous,'outside_columns':outside,'status':'CANDIDATE_REVIEW_REQUIRED','uncertainty':'stroke extent only; calibration, sampling and reading uncertainty not included'}


def freeze_plan(plan):
    """Freeze IDs and source-page split; gold stays outside the parser input."""
    ids=set(); seen={}; cases=plan['cases']
    if not cases: raise ValueError('Empty plan')
    for c in cases:
        i,h,p,s,st=(c[k] for k in ('id','source_sha256','page','split','stratum'))
        if not isinstance(i,str) or not i or i in ids or not valid_hash(h) or type(p) is not int or p<1 or s not in ('dev','holdout') or not isinstance(st,str) or not st:
            raise ValueError('Invalid or duplicate case')
        ids.add(i)
        if (h,p) in seen and seen[h,p]!=s: raise ValueError('Dev/holdout page leakage')
        seen[h,p]=s
    if set(seen.values())!={'dev','holdout'}: raise ValueError('Both splits required')
    payload=json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    return {'plan':plan,'plan_sha256':hashlib.sha256(payload).hexdigest()}


def evaluate(frozen,gold,pred):
    """Holdout literal field score by stratum; missing predictions remain failures."""
    if freeze_plan(frozen['plan'])['plan_sha256']!=frozen['plan_sha256']:
        raise ValueError('Plan changed')
    if any(obj.get('plan_sha256')!=frozen['plan_sha256'] for obj in (gold,pred)):
        raise ValueError('Gold/prediction plan mismatch')
    cases={c['id']:c for c in frozen['plan']['cases'] if c['split']=='holdout'}
    kinds={'text','number','unit','formula','table_cell','figure_label','reading_order'}
    def index(obj):
        d={}
        for r in obj['items']:
            k=r['case_id'],r['id']
            if k[0] not in cases or not isinstance(k[1],str) or not k[1] or k in d or r['kind'] not in kinds or not isinstance(r['value'],str):
                raise ValueError('Invalid or duplicate field')
            d[k]=(r['kind'],' '.join(r['value'].split()))
        return d
    g,p=index(gold),index(pred)
    if set(k[0] for k in g)!=set(cases): raise ValueError('Gold must cover every holdout case')
    def stats(keys):
        a={k for k in g if k[0] in keys}; b={k for k in p if k[0] in keys}
        n=sum(g[k]==p[k] for k in a&b)
        return {'gold':len(a),'predicted':len(b),'correct':n,'precision':n/len(b) if b else None,'recall':n/len(a) if a else None,'f1':2*n/(len(a)+len(b)) if a or b else None,'missing':len(a-b),'extra':len(b-a),'mismatch':sum(g[k]!=p[k] for k in a&b)}
    return {'overall':stats(cases),'by_stratum':{s:stats({i for i,c in cases.items() if c['stratum']==s}) for s in sorted({c['stratum'] for c in cases.values()})},'unresolved_critical_fields':sorted([list(k) for k in g if g[k][0] in {'number','unit','formula','table_cell','figure_label'} and p.get(k)!=g[k]]),'metric':'strict_literal_not_official_benchmark'}


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('mineru'); a.add_argument('source'); a.add_argument('output'); a.add_argument('--start',type=int,required=True); a.add_argument('--end',type=int,required=True); a.add_argument('--tier',default='standard'); a.add_argument('--timeout',type=int,default=3600)
    for name,fields in [('compare',['first','second','output']),('chart',['image','config','output']),('freeze',['plan','output']),('evaluate',['frozen','gold','pred','output'])]:
        a=sub.add_parser(name)
        for f in fields: a.add_argument(f)
    a=p.parse_args()
    if a.cmd=='mineru': print(mineru_run(a.source,a.output,a.start,a.end,a.tier,a.timeout)); return
    if a.cmd=='compare': r=page_compare(load(a.first),load(a.second))
    elif a.cmd=='chart': r=digitize(a.image,load(a.config))
    elif a.cmd=='freeze': r=freeze_plan(load(a.plan))
    else: r=evaluate(load(a.frozen),load(a.gold),load(a.pred))
    save(a.output,r)

if __name__=='__main__': main()
