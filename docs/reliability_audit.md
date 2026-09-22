# Reliability audit (V2, pre-empirical)

Date: 2026-09-21. This is an AI-assisted engineering self-audit. It is **not** independent scientific review, psychological expert review or clinician validation. Test outcomes are in `docs/test_summary.json` and `docs/test_results.txt`.

Headline: REAL QWEN CALLS 0; judge calls 0; human ratings 0; held-out trajectories materialised 0; final experiment freeze not created. Every statement below concerns software and design, not model behaviour.

| Area | What was checked | Status | Residual risk |
|---|---|---|---|
| Leakage: future turns | `evidence(case, t)` returns turns 1..t only; future mutation cannot alter a prefix; checked for every primary calibration variant | Verified | — |
| Leakage: latent truth into C | Parsed payload keys for A, B and C extraction/decision messages contain no gold, archetype, mode, transition or fault labels; no condition or archetype name appears in any message | Verified (after a vacuous version of the test was caught by mutation testing) | Metadata C *legitimately* receives (source turn, episode, day) could correlate with conditions; e.g. the stale topic change is visible to all three architectures by design |
| Leakage: held-out | Latent generation, `build_split`, traps, rendered examples and the CLI refuse held-out without a verified freeze; no held-out file exists | Verified | Procedural guards; a researcher can bypass them deliberately |
| Determinism | Latents, rendered cases, manifest and data files are byte-reproducible; calibration latent SHA-256 `7d86ecbb3e34b07bb0391e144f6d7773169f418701a6ae7fbecf7b31cff2c4a3` | Verified | Model sampling determinism is untested (no model run) |
| Model pinning | `Qwen/Qwen3-8B` configured; `model_revision` **null**; freeze refuses null revisions | Enforced | Revision must be resolved on the GPU host; weight hashes recorded there |
| Non-thinking mode | `chat_template_kwargs.enable_thinking=false` sent on every request (tested with a mocked endpoint); `think_block_detected` recorded without altering text | Verified in software | Documentation is `main`-branch; must be re-verified against the pinned vLLM/Qwen versions |
| A/B/C fairness | One generation block; identical evidence to A/B/C; B/C share one instruction template and one extraction per case/turn | Verified | C's additional metadata changes prompt length; this is part of the architecture, not equalised |
| Degradation isolation | Per-condition allowed changes (turns and gold fields) tested for every calibration trajectory | Verified | Isolation is relative to the authored text; wording effects of family-specific perturbations are not separately controlled |
| Degradation validity | Every condition × archetype cell rendered and classified; confounded and non-applicable cells excluded prospectively; excluded cells refuse to render | Verified | Classification rules were designed by the authors and need independent review |
| Matched controls | `unsupported_inference` and `stale_state` controls identical to injected cases except faults | Verified | — |
| Benchmark diversity | See `benchmark_diversity_audit.md` | Improved | 55–62% of rendered characters still templated; max same-family pairwise Jaccard 0.917 |
| Family × archetype confound | Allocation crosses all 8 archetypes with every family (held-out plan) | Fixed during V2, tested | Calibration cannot cross fully with 20 trajectories |
| Parser | Strict JSON, no silent repair; failures kept in denominators | Unchanged from V1, tested | Real Qwen failure modes unknown until calibration |
| Missing outputs | Parse/API failures are rows, not omissions; completeness from `planned_variants` | Verified | — |
| Repair/replay | Single-slot repair; replay-equality required for attribution; repair never mutates live state | Unchanged from V1, tested | Replay-equality under stochastic sampling may be rare, inflating `ambiguous`; must be measured in calibration |
| Evaluator | Family-aware traps, 2 negative controls, 5 failure kinds; two explicit evaluator modes; prospective validation gate; semantic metrics masked unless validated; SEPR independent of the evaluator | Implemented, tested (4 mutations caught) | Mode undecided; no evaluator selected; zero trap judgments exist. Gate thresholds on 8 items per kind screen out only clearly inadequate evaluators |
| Freeze gate | Expects the V2 calibration design (1,650 primary, 600 control turns); accepts a complete synthetic journal and rejects one missing cell, without writing a manifest | Fixed during V2, tested | See open decision 1 |
| Post-freeze deviations | None possible yet | — | — |
| Reproducibility | Fresh venv, `pip install -e .`, no `PYTHONPATH`: full suite passes; non-editable install fails loudly | Verified | Python 3.12 only |

## V1 defects found by this audit

1. Every trajectory used one situation; context was noun substitution.
2. Calibration and held-out used disjoint families.
3. Initial appraisal, goal and prior exercise were all set by `variant % 2` (perfect confound).
4. Supersession wording ("I no longer take the reply as a personal judgment") was applied to users who had been uncertain.
5. Held-out latent specifications could be built in-process pre-freeze.
6. Evaluator traps embedded the single V1 scenario.
7. `source_manifest` hashed build metadata that `pip install -e .` creates under `src/`, so a lock or freeze made before installation failed verification after it (found by verifying the packaged ZIP in a fresh environment).

Defects 1–4 affect benchmark validity. Defects 5–7 are integrity and evaluator issues. None affected results, because V1 produced none.

## V2 defects found and fixed before packaging

Family × archetype confound in the first V2 allocation; gold/dialogue mismatch for `competing_interpretations × superseded`; stale-topic evidence leak; hardcoded six-condition assumptions in analysis completeness, ablation reuse and the freeze gate (the last would have made the final freeze impossible); a vacuous leakage test.

## Open decisions that must be made before freeze

1. **Evaluator mode (mechanism resolved in V2.1; choice still open).** The contradiction between the three-judgment freeze gate and the manual-audit fallback is resolved by an explicit `evaluator_mode` (`validated_automated` | `manual_audit_only`) with a prospective validation gate (`protocol_v2_amendment.md` §9). Which mode to use is not yet decided; the freeze cannot be created until it is.
2. **Sampling configuration.** T 0.7 / top_p 0.8 / top_k 20 / min_p 0 is a starting point. Whether stochastic sampling yields acceptable parse stability and replay-equality for SEPR attribution must be decided from calibration, on reliability grounds only.
3. **Power.** Reference-mode cells (26 held-out trajectories for contradiction `transition` and supersession `retraction`) are small. Accept as descriptive, or revise allocation before approval.

## Limitations not addressable by software checks

Authored synthetic truth; templated, unusually explicit appraisal statements; five fixed observations; open-loop replay (the user never reacts to the system); single language and cultural register; no psychologist review of families or rubric; LLM evaluation is not human evaluation; results, when they exist, will not bear on clinical efficacy.
