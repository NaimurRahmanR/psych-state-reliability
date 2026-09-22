#!/usr/bin/env python3
"""Reproduce the public descriptive author-blinded audit counts."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'results/processed/pilot20_manual_audit'
with (D/'human_overall_ratings.csv').open(newline='',encoding='utf-8') as f: ratings=list(csv.DictReader(f))
key={r['audit_id']:r for r in (json.loads(x) for x in (D/'audit_deblinding_key.jsonl').read_text().splitlines() if x.strip())}
assert len(ratings)==324 and set(r['audit_id'] for r in ratings)==set(key)
c=Counter(r['overall_failure'] for r in ratings)
assert c==Counter({'false':322,'true':1,'ambiguous':1})
assert all(key[r['audit_id']]['automated_failure'] is None for r in ratings)
summary=json.loads((D/'human_audit_descriptive.json').read_text())
assert summary['human_counts']['pass']==322 and summary['human_counts']['fail']==1 and summary['human_counts']['ambiguous']==1
by_arch=defaultdict(Counter); by_cond=defaultdict(Counter)
for r in ratings:
    k=key[r['audit_id']]; by_arch[k['architecture']][r['overall_failure']]+=1; by_cond[k['condition']][r['overall_failure']]+=1
for a in 'ABC':
    s=summary['by_architecture'][a]
    assert by_arch[a]['false']==s['pass'] and by_arch[a]['true']==s['fail'] and by_arch[a]['ambiguous']==s['ambiguous']
for cond,s in summary['by_condition'].items():
    assert by_cond[cond]['false']==s['pass'] and by_cond[cond]['true']==s['fail'] and by_cond[cond]['ambiguous']==s['ambiguous']
print('HUMAN_AUDIT_PUBLIC_COUNTS=EXACT_MATCH')
print('AUTOMATED_SEMANTIC_LABELS=UNAVAILABLE_324_OF_324')
print('MODEL_CALLS=0')
