# Psych-State Reliability

**From Evidence to Intervention: State Error Propagation and Abstention in Longitudinal LLM-Mediated Psychological Support**

Reproducible research code and frozen pilot results for a synthetic, non-clinical study of how longitudinal psychological-state errors propagate into downstream LLM intervention decisions.

> **Scientific status:** analysis frozen on 22 September 2026. The locked application/preprint pilot contains **20 held-out base trajectories, 106 applicable primary base-condition variants, 1,590 primary architecture-turn outcomes, 600 matched-control outcomes, and 2,190 total outcomes**. The originally planned 100-base held-out design was not executed.

## Main result

The reliability-aware architecture C reduced **absolute propagation burden** relative to naive structured state B, but did so with a severe loss of coverage and a **higher conditional state-error propagation rate (SEPR)**:

| Primary C - B contrast | Difference | 95% paired bootstrap CI |
|---|---:|---:|
| SEPR | **+0.1018** | [0.0527, 0.1541] |
| Propagation burden | **-0.1811** | [-0.2648, -0.1060] |
| Coverage | **-0.7698** | [-0.8920, -0.6333] |
| Decision-reliable coverage | **-0.0981** | [-0.1473, -0.0537] |

The central finding is a distinction between **selectivity** and **conditional reliability**: fewer propagated errors in absolute terms can coexist with worse propagation conditional on an erroneous state remaining active.

Other prospective results were mixed or adverse:

- **H1:** structured state did not improve clean state recall over history prompting (B - A = -0.0883, 95% CI [-0.1983, 0.0050]).
- **H2:** unsupported inference increased persistence in B (+0.2833 [0.1667, 0.4167]), while the downstream decision-error increase was not clearly separated from zero (+0.0200 [0.0000, 0.0600]).
- **H3:** the prospective improvement criterion was not met; SEPR moved in the opposite direction while coverage fell materially.
- **H4:** not tested. The final evaluator mode was `manual_audit_only`, and automated semantic failure labels were unavailable for all audited items.

## Descriptive human audit

A seed-fixed 324-item response-text packet was completed by one non-clinical author rater. Final overall judgments were **322 pass, 1 fail, 1 ambiguous**. This is **descriptive author-blinded evidence only**: the rater was also the study author/developer and had seen aggregate experimental results before completing the audit. It is not an independent clinical validation.

The public repository includes only the minimal overall judgments and deblinding mapping needed to reproduce the reported counts. Free-text rater notes are retained in the frozen private analysis archive but are not redistributed because they are not needed to reproduce the paper's descriptive audit statistics.

## Architectures

- **A - HISTORY:** full available user-evidence prefix; no persistent state object.
- **B - STRUCTURED:** shared extraction plus last-write persistent typed state.
- **C - RELIABILITY-AWARE:** the same user evidence and extraction proposals as B, augmented with provenance, temporal scope, explicit/inferred status, contradiction/supersession handling, and clarify/defer behavior. C receives no latent truth or future turns.

## Benchmark

The benchmark uses 12 authored everyday scenario families, eight longitudinal transition archetypes, and five observations at days 0, 3, 7, 10, and 14. Conditions are:

`clean` · `missing_evidence` · `contradictory_evidence` · `superseded_appraisal` · `unsupported_inference` · `stale_state`

The psychological state representation is deliberately narrow: situation/context, appraisal, emotion, regulatory goal, and prior exercise/feedback. Intervention decisions are restricted to emotional validation, cognitive reappraisal, or clarify/defer.

**This is not a clinical benchmark.** It contains no participant or patient data, no diagnoses, no crisis scenarios, and no evidence of therapeutic effectiveness or clinical safety.

## Reproduce the reported statistics offline

Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
python release_tools/run_frozen_tests.py
python release_tools/verify_public_release.py
python release_tools/analyze_pilot20.py
python release_tools/verify_human_audit.py
python release_tools/make_publication_tables.py
```

Expected endpoints include:

```text
Ran 149 tests ... OK
PUBLIC_RELEASE_INTEGRITY=PASS
REPORTED_CORE_STATISTICS=EXACT_MATCH
HUMAN_AUDIT_PUBLIC_COUNTS=EXACT_MATCH
```

No model call, GPU, API key, or network access is needed for the offline analysis.

## Robustness and bootstrap checks

The confirmatory confidence intervals use a **paired cluster bootstrap over held-out base trajectories**: the same sampled base IDs are reused in both compared arms, with 2,000 repetitions and frozen seed `77129`. The implementation is in `src/psyr/analysis/statistics.py`; the release wrapper verifies the stored effects exactly.

A separate **post-freeze robustness audit** (`release_tools/robustness_audit.py`) performs analysis-only sensitivity checks without model calls or protocol changes:

- repeats the key contrasts with **10,000 bootstrap draws**;
- repeats the 2,000-draw bootstrap across **five fixed seeds**;
- re-clusters by **context family** (10 clusters) instead of base trajectory where pairing is complete;
- performs **leave-one-base-out** influence checks;
- confirms the prespecified `ALL_REFERENCE` H3 sensitivity direction.

Key H3 conclusions are stable in these checks: C-B SEPR remains positive, while propagation burden and coverage remain negative under every leave-one-base-out replicate, the 10,000-draw bootstrap, and context-family clustering. These checks assess sampling/influence stability of this frozen pilot; they do **not** establish cross-model, real-user, or clinical robustness.

Run:

```bash
python release_tools/robustness_audit.py
```

Outputs are written to `results/publication/robustness_audit.json` and `results/publication/robustness_summary.json`.

## Authoritative empirical files

- `results/processed/pilot20_final/outcomes_merged.jsonl` - all 2,190 frozen turn outcomes used for offline recomputation.
- `results/processed/pilot20_final/pilot20_analysis.json` - authoritative H1-H4/overall analysis object.
- `results/processed/pilot20_final/condition_architecture_metrics.csv` - condition-by-architecture descriptives.
- `results/provenance/final_analysis_manifest.json` - frozen analysis manifest and checksums.
- `results/provenance/application_preprint_pilot_amendment.json` - 20-base compute/time amendment locked before held-out performance inspection.
- `results/provenance/concurrency_execution_amendment.json` - five-worker between-base execution amendment locked before additional held-out inference.

The complete raw held-out archive is not required to verify the paper statistics. Its frozen SHA-256 is recorded in the provenance manifest; the merged outcome journal is the committed publication artifact.

## Frozen identities

- Source digest: `a985aa60ef4eedda3e7eb4d68b31437aba669c9dca15caa7328b79857cdf41dd`
- Final manual configuration SHA-256: `db83f43b1630356358abf54485f225d7d095b7b00675e78b29c151378f7a4545`
- Held-out dataset digest: `e8d1da248ad4ba794360cf67796e2cd4214a404fc404e26a6f9ea5255a22a557`
- Merged 2,190-outcome journal SHA-256: `3f2ca80cb663d70e0135ec9f2a53cce0f2cab68e65286042401ec5b2bb94e98c`
- Completed raw held-out archive SHA-256: `fb54337806ff43e4e9f03ba91370cc651473850f650cb6ef38aa6502fd939c7f`
- Final analysis archive SHA-256: `76bb169803e3362eb538319c616ac179e6e2a43c1a1fe625deb0fe8688dcac15`

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md), [`RESULTS.md`](RESULTS.md), and the paper source under [`paper/`](paper/).

## Citation

Until the arXiv identifier is assigned, cite the repository using `CITATION.cff`. The citation file will be updated after arXiv submission.

## License

Software in this repository is released under the MIT License. The manuscript has its own publication/reuse terms as selected during arXiv submission.
