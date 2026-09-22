# Specification traceability (V2)

| Requirement | Location | Status |
|---|---|---|
| Baseline audit of V1 | `docs/V2_CHANGELOG.md` (baseline section) | Done: 71 V1 tests verified |
| Provenance | `docs/provenance.md`, `PROVENANCE_DIFF.json` | Done |
| 12 scenario families; latent-first | `src/psyr/benchmark/families.py`, `dataset.py` | Done, tested |
| Transition coverage | `ARCHETYPES`, `TRANSITION_TYPES`; tests | All 10 required types covered |
| Same family universe, distinct split identities | `allocation`, `SEEDS`, `PREFIX`; tests | Done, tested |
| Family-aware degradations; isolation; matched controls | `src/psyr/degradations/conditions.py`; tests | Done, tested |
| Condition × archetype applicability design | `classify_condition`; `protocol_v2_amendment.md` §3 | Done, tested |
| Held-out protection before freeze | dataset, audit, CLI guards; tests | Done, tested |
| Manifest | `data/calibration/manifest.jsonl` | Done, tested |
| Diversity audit | `docs/benchmark_diversity_audit.md`; `diversity.py`; `scripts/diversity_v1_v2.py` | Done; reproducibility tested |
| A/B/C fairness; no latent truth to C | prompts, runner; tests | Verified in software |
| Qwen3-8B non-thinking configuration | `configs/experiment.json`; `docs/evidence/` | Configured; **revision unresolved; not executed** |
| Real calibration | — | **NOT EXECUTED** (environment blocked) |
| Evaluator mode and validation gate | `evaluation/evaluator_policy.py`, `freeze.py`; `protocol_v2_amendment.md` §9 | Both modes and gate implemented and tested; **mode undecided; evaluator unselected** |
| Final freeze | `src/psyr/freeze.py` | Gate fixed for V2; **freeze not created** |
| Held-out materialisation and execution | — | **0** |
| Human audit | `evaluation/audit.py` packet tooling | **NOT EXECUTED** |
| Clean-environment reproducibility | README; fresh-venv verification | Done |
| GPU execution plan | `docs/gpu_execution_plan.md` | Documented |
| Reliability audit; changelog; manuscript; application note; status | `docs/`, `manuscript/`, `Research_Execution_Status.md` | Done |
