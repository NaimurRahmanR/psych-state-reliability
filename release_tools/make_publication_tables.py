#!/usr/bin/env python3
"""Create clearly-labelled post-freeze publication tables from frozen pilot outcomes."""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from psyr.analysis.report import metric_clusters
from psyr.analysis.statistics import paired_ratio_bootstrap

REPS=2000; SEED=77129
CONDITIONS=['clean','missing_evidence','contradictory_evidence','superseded_appraisal','unsupported_inference','stale_state']

def load(path):
    with path.open(encoding='utf-8') as f: return [json.loads(x) for x in f if x.strip()]

def paired(left,right,metric):
    a=metric_clusters(left,metric,'base_id'); b=metric_clusters(right,metric,'base_id')
    assert set(a)==set(b)
    return paired_ratio_bootstrap(a,b,repetitions=REPS,seed=SEED)

rows=load(ROOT/'results/processed/pilot20_final/outcomes_merged.jsonl')
primary=[r for r in rows if not r['control']]
out=[]
for cond in CONDITIONS:
    b=[r for r in primary if r['condition']==cond and r['architecture']=='B']
    c=[r for r in primary if r['condition']==cond and r['architecture']=='C']
    rec={'condition':cond}
    for metric in ['sepr','propagation_burden','coverage','decision_error_rate','decision_reliable_coverage']:
        e=paired(b,c,metric)
        rec[f'{metric}_c_minus_b']=e['difference_b_minus_a']
        rec[f'{metric}_ci_low']=e['ci_low']
        rec[f'{metric}_ci_high']=e['ci_high']
        rec[f'{metric}_clusters']=e['clusters']
    out.append(rec)

p=ROOT/'results/publication/condition_effects.csv'; p.parent.mkdir(parents=True,exist_ok=True)
with p.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n'); w.writeheader(); w.writerows(out)
meta={
 'status':'POST_FREEZE_PUBLICATION_DERIVATION',
 'source':'results/processed/pilot20_final/outcomes_merged.jsonl',
 'bootstrap_repetitions':REPS,'bootstrap_seed':SEED,
 'note':'Secondary condition-level decomposition; no model calls and no protocol tuning.'
}
(ROOT/'results/publication/condition_effects.meta.json').write_text(json.dumps(meta,indent=2)+'\n')
print('PUBLICATION_CONDITION_TABLE=CREATED')
print('MODEL_CALLS=0')
