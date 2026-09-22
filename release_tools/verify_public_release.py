#!/usr/bin/env python3
"""Offline integrity checks for the public empirical release."""
from pathlib import Path
import hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from psyr.common import digest, read_jsonl
from psyr.freeze import source_manifest

EXPECTED_SOURCE='a985aa60ef4eedda3e7eb4d68b31437aba669c9dca15caa7328b79857cdf41dd'
EXPECTED_HELDOUT='e8d1da248ad4ba794360cf67796e2cd4214a404fc404e26a6f9ea5255a22a557'
EXPECTED_AMEND='6f79908de18b9fc7c0e268c8195de997044c25136235eff90ef051f02d1ae2e7'
EXPECTED_CONC='e30e58b48c07ceafc8cf83501bd0a5e8bef84225372780577f589e42ccc10548'
EXPECTED_MERGED='3f2ca80cb663d70e0135ec9f2a53cce0f2cab68e65286042401ec5b2bb94e98c'
EXPECTED_ANALYSIS='5f18ec2ba4bc673520e4db472bb6c5f981376a9465319cb81103642ad766a791'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

assert digest(source_manifest(ROOT))==EXPECTED_SOURCE
latent=read_jsonl(ROOT/'data/heldout/latent.jsonl')
assert len(latent)==100 and digest(latent)==EXPECTED_HELDOUT
assert sha(ROOT/'results/provenance/application_preprint_pilot_amendment.json')==EXPECTED_AMEND
assert sha(ROOT/'results/provenance/concurrency_execution_amendment.json')==EXPECTED_CONC
merged=ROOT/'results/processed/pilot20_final/outcomes_merged.jsonl'
analysis=ROOT/'results/processed/pilot20_final/pilot20_analysis.json'
assert sha(merged)==EXPECTED_MERGED
assert sha(analysis)==EXPECTED_ANALYSIS
rows=read_jsonl(merged)
assert len(rows)==2190 and len({r['key'] for r in rows})==2190
assert len({r['base_id'] for r in rows})==20
assert sum(not r['control'] for r in rows)==1590
assert sum(bool(r['control']) for r in rows)==600

# The frozen archive manifest is retained verbatim; verify every authoritative file
# from it that is intentionally redistributed in the public release.
manifest=json.loads((ROOT/'results/provenance/final_analysis_manifest.json').read_text())
assert manifest['scientific_status']=='ANALYSIS_FROZEN'
assert manifest['pilot']['total_outcomes']==2190
for e in manifest['files']:
    p=ROOT/e['path']
    if p.exists():
        assert sha(p)==e['sha256'], f"hash mismatch: {e['path']}"

assert not (ROOT/'weights').exists()
print('PUBLIC_RELEASE_INTEGRITY=PASS')
print('SOURCE_DIGEST=VALID')
print('HELDOUT_DATASET=VALID')
print('FROZEN_OUTCOME_JOURNAL=VALID_2190')
print('MODEL_CALLS=0')
