"""Structural checks only; cannot certify evidence, claims or engineering performance."""
import argparse
import json
import re
from pathlib import Path


def validate(root):
    root = Path(root); errors=[]; ids=set(); sources=set(); counts={}
    def err(msg): errors.append(msg)
    def read(name):
        try: return json.loads((root/name).read_text(encoding='utf-8'))
        except (OSError, ValueError) as e: err(f'{name}: {e}'); return {}
    def rows(obj, field, name):
        if not isinstance(obj,dict) or not isinstance(obj.get(field),list):
            err(f'{name}: expected {field} array'); return []
        return obj[field]
    def nonempty(obj, key): return isinstance(obj.get(key),str) and bool(obj[key].strip())
    for i,s in enumerate(rows(read('source-index.json'),'sources','source-index.json')):
        tag=f'source[{i}]'
        if not isinstance(s,dict): err(f'{tag}: not an object'); continue
        for k in ('id','title','edition','locator','access','rights'):
            if not nonempty(s,k): err(f'{tag}: missing {k}')
        if nonempty(s,'id'):
            if s['id'] in sources: err(f'{tag}: duplicate source ID')
            sources.add(s['id'])
        if 'sha256' not in s or (s['sha256'] is not None and (not isinstance(s['sha256'],str) or not re.fullmatch(r'[0-9a-fA-F]{64}',s['sha256']))): err(f'{tag}: invalid sha256')
    sections=rows(read('coverage.json'),'sections','coverage.json')
    for i,s in enumerate(sections):
        if not isinstance(s,dict): err(f'coverage[{i}]: not an object'); continue
        if not nonempty(s,'source_id') or s['source_id'] not in sources or not nonempty(s,'locator'): err(f'coverage[{i}]: invalid source or locator')
        if s.get('status') not in ('pending','parsed','reviewed','partial','blocked','out_of_scope'): err(f'coverage[{i}]: invalid status')
        if not nonempty(s,'notes'): err(f'coverage[{i}]: missing notes')
    for name in ('concepts.jsonl','rules.jsonl','formula-index.jsonl'):
        counts[name]=0
        try: lines=(root/name).read_text(encoding='utf-8').splitlines()
        except OSError as e: err(f'{name}: {e}'); continue
        for i,line in enumerate(lines,1):
            if not line.strip(): continue
            tag=f'{name}:{i}'; counts[name]+=1
            try: r=json.loads(line)
            except ValueError as e: err(f'{tag}: {e}'); continue
            if not isinstance(r,dict): err(f'{tag}: not an object'); continue
            for k in ('id','title'):
                if not nonempty(r,k): err(f'{tag}: missing {k}')
            if nonempty(r,'id'):
                if r['id'] in ids: err(f'{tag}: duplicate card ID')
                ids.add(r['id'])
            if r.get('support') not in ('source','derived','inference','external'): err(f'{tag}: invalid support')
            if r.get('status') not in ('candidate','verified','blocked'): err(f'{tag}: invalid status')
            ev=r.get('evidence')
            if not isinstance(ev,list): err(f'{tag}: evidence must be array'); ev=[]
            if r.get('status')=='verified' and (not ev or r.get('support')=='inference'): err(f'{tag}: verified requires evidence and non-inference support')
            for e in ev:
                if not isinstance(e,dict) or not nonempty(e,'source_id') or e['source_id'] not in sources or not nonempty(e,'locator'): err(f'{tag}: invalid evidence locator/source')
            c=r.get('content')
            if not isinstance(c,dict) or not c: err(f'{tag}: missing content'); continue
            keys= {'rules.jsonl':('trigger','required_inputs','predicate','action','exceptions','unknown_behavior','validation'), 'formula-index.jsonl':('expression','variables','assumptions','domain','validation')}.get(name,())
            for k in keys:
                if k not in c or (not c[k] and k not in ('exceptions','assumptions')): err(f'{tag}: missing content.{k}')
    for name in ('workflows.md','integration.md','validation-report.md'):
        try:
            if not (root/name).read_text(encoding='utf-8').strip(): err(f'{name}: empty')
        except OSError as e: err(f'{name}: {e}')
    return {'structural_status':'FAIL' if errors else 'PASS','empty_pack':not any(counts.values()),'counts':counts,'sources':len(sources),'sections':len(sections),'errors':errors,'semantic_validation':'NOT_ASSESSED'}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('pack',type=Path)
    result=validate(p.parse_args().pack); print(json.dumps(result,indent=2,ensure_ascii=False)); raise SystemExit(bool(result['errors']))
