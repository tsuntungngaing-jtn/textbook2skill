"""Create a new empty knowledge pack; never overwrite existing paths."""
import argparse
import json
from pathlib import Path

def initialize(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    for name, obj in [('source-index.json', {'sources': []}), ('coverage.json', {'sections': []})]:
        (root/name).write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8')
    for name in ('concepts.jsonl','rules.jsonl','formula-index.jsonl'):
        (root/name).write_text('', encoding='utf-8')
    for name, title in [('workflows.md','Workflows'),('integration.md','Integration'),('validation-report.md','Validation report')]:
        (root/name).write_text(f'# {title}\n\nNOT_RUN: no textbook reviewed yet.\n', encoding='utf-8')
    return root

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('output',type=Path)
    print(initialize(p.parse_args().output))
