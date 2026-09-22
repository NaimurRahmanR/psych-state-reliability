# V2 changelog

Base: `psych-state-reliability-research-package.zip` (62 files, SHA-256 `fe255b7501c56ab5eeba2a27284979be3f06115b5838cc33560a4bded60cdffe`). All V2 changes precede any model call. None was informed by empirical outcomes, because none exist.

Impact columns: **H** hypotheses, **Arch** architectures, **SEPR** primary metric, **Bench** benchmark, **Anal** analysis. "—" means unaffected.

## Baseline audit of V1 (independently verified)

- 71 tests ran and passed (61 `test_invariants.py`, 10 `test_pipeline.py`).
- 20 calibration latents, 120 condition variants, 600 evidence-prefix checks reproduced.
- Zero model calls, zero held-out materialisation, no final freeze — V1's self-report was accurate.
- Engineering found sound: hash-chained journals, strict parsers, model-identity drift stop, no fabricated fallback, counterfactual repair/replay SEPR.

## Provenance incident during V2 work

An early working copy contained three files not present in the authoritative ZIP and not written in this work (`src/psyr/benchmark/families.py` with identifiers such as `FAMILY_KEYS`/`family_pool`, `src/psyr/benchmark/audit.py`, and a 16,792-byte `dataset.py`). That tree was discarded. V2 was rebuilt from a CRC-verified extraction. A later check found a stray copy of the upload and its extraction in the workspace; both were verified byte-identical to the upload and removed. The packaged tree differs from the authoritative ZIP only by the changes listed here (verified by file-level diff before packaging; see `docs/provenance.md`).

## Benchmark

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| B1 | Twelve authored scenario families (`benchmark/families.py`) replace V1's single hardcoded situation plus activity-noun substitution | — | — | — | yes | — |
| B2 | Eight latent transition archetypes; natural appraisal/goal/emotion change at turns 2, 4, 5; turn 3 kept as the perturbation slot | — | — | — | yes | — |
| B3 | Both splits draw from all twelve families (V1: calibration 2 families, held-out 10 *disjoint* families, so calibration could not inform held-out behaviour) | — | — | — | yes | — |
| B4 | Family × archetype crossed allocation. The first V2 rule `(3i) mod 8` paired each family with only 2 archetypes; replaced before any use | — | — | — | yes | yes |
| B5 | Goal, emotion and feedback drawn independently by seeded RNG. V1 set initial appraisal, goal and prior exercise all from `variant % 2`, perfectly confounding negative appraisal with the validation goal | — | — | — | yes | — |
| B6 | `competing_interpretations` move stored as an appraisal move. As first written it had `field=None`, so under `superseded_appraisal` gold said *situational* while the user said "I hold both at once" | — | — | — | yes | — |
| B7 | Machine-readable manifest (`data/calibration/manifest.jsonl`): family, archetype, seed, version, latent variables, transitions, superseded propositions, intervention family, full condition design, latent digest | — | — | — | yes | — |
| B8 | Rendered calibration examples now produced by the `dataset` command (V1 shipped `examples.jsonl` with no generating command) | — | — | — | — | — |
| B9 | Fixture split (seed 5501, prefix FIX) for generator tests that cannot become held-out data | — | — | — | — | — |

## Degradations and design

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| D1 | Degradation text is family-specific (V1 hardcoded organiser/scheduling text in contradiction, supersession and stale conditions) | — | — | — | yes | — |
| D2 | Injected gold holds only until the trajectory's next natural appraisal statement | — | — | — | yes | — |
| D3 | `missing_evidence`: appraisal unobservable only until next explicit appraisal statement (V1: all turns) | — | — | — | yes | — |
| D4 | Prospective condition classification (`classify_condition`): clean / stratified / non_applicable / confounded, computed from the archetype | — | — | — | yes | yes |
| D5 | `superseded_appraisal` × uncertain-initial trajectories rendered as *resolution of uncertainty* without retraction language. **V1 defect:** V1 applied "I no longer take the reply as a personal judgment" to trajectories whose user had been uncertain (half of V1) | — | — | — | yes | yes |
| D6 | `superseded_appraisal` excluded where it would duplicate a natural correction verbatim; `contradictory_evidence` excluded where a later natural retraction presupposes the dissolved commitment | — | — | — | yes | yes |
| D7 | `stale_state`: old-topic narrative and "same issue" filler no longer carried into the new topic | — | — | — | yes | — |
| D8 | Planned held-out primary matrix 1,650 trajectories / 8,250 decision points (was 1,800 / 9,000); 600 control trajectories unchanged | — | — | — | yes | yes |

## Engineering and analysis

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| E1 | `latent_trajectory("heldout")` refuses without `allow_heldout`; V1 gated only `build_split`, so held-out specs could be built in-process pre-freeze | — | — | — | — | — |
| E2 | Held-out traps verify the freeze themselves; `rendered_examples` refuses held-out | — | — | — | — | — |
| E3 | Runner iterates `applicable_conditions`; rows record family, archetype, relationship, `perturbation_mode`, `design_status`, benchmark version | — | — | — | — | yes |
| E4 | Analysis: `stratified_counts`, `stratified_comparisons`, `ALL_REFERENCE` sensitivity aggregate | — | — | — | — | yes |
| E5 | Completeness uses `planned_variants`. **V1 defect under V2:** `expected = n × 6 × 3 × 5` would have marked every complete V2 run incomplete | — | — | — | — | yes |
| E6 | Backend records `think_block_detected`; text preserved unaltered | — | — | — | — | yes |
| E7 | `psyr.common` raises a clear error under a non-editable install (V1 would silently resolve `ROOT` into site-packages) | — | — | — | — | — |
| E8 | CLI: `diversity-audit`; `scripts/diversity_v1_v2.py` | — | — | — | — | — |
| E9 | `finalize` expects the V2 calibration cells and matched controls. **V1 defect under V2:** it required exactly 1,800 primary turns over six conditions, so the freeze could never pass under V2 | — | — | — | — | yes |
| E10 | Ablation extraction reuse counts `planned_variants × 5` (V1 hardcoded ×6×5, rejecting every V2 ablation) | — | — | — | — | yes |
| E12 | `source_manifest` ignores `*.egg-info` and `build/`. **V1 defect:** `pip install -e .` added build metadata under `src/`, so a design lock or freeze made before installation failed verification after it | — | — | — | — | — |
| E11 | `run --no-judge` for calibration only, so calibration can precede evaluator selection; a judgeless run cannot pass the freeze gate | — | — | — | — | — |

## Evaluator

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| V1 | Family-aware traps. **V1 defect under V2:** every trap embedded "You now see the message as a scheduling issue" / "the organiser clearly does think poorly of you"; under other families the *correct* trap would itself be wrong, so a competent judge would be scored as a false positive | — | — | — | — | yes (RQ4) |
| V2 | Added `uncertainty_ack` (negative control) and `strategy_switch` (expected failure); 8 calibration bases × 7 kinds = 56 items | — | — | — | — | yes (RQ4) |

No evaluator model has been selected; see `docs/gpu_execution_plan.md`.

## Model integration (configuration only; nothing executed)

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| M1 | `configs/experiment.json` → `design-v2`: `Qwen/Qwen3-8B`, `model_revision: null` (unresolved, not invented), calibration starting sampling T 0.7 / top_p 0.8 / top_k 20 / min_p 0, `chat_template_kwargs.enable_thinking=false`, one generation block for A/B/C | — | — | — | — | — |
| M2 | Thinking-switch evidence stored in `docs/evidence/` (Qwen3 README, vLLM reasoning docs, retrieved via raw.githubusercontent.com) | — | — | — | — | — |

Prompts (`configs/prompts/*.txt`) are unchanged from V1.

## Tests

V1: 71. V2: **125** (0 failures, 0 errors, 0 skipped).

| Change | Reason |
|---|---|
| `test_repair_does_not_mutate_live_state` | Invariant scoped to the window before a natural appraisal restatement; its V1 premise (appraisal never restated after turn 3) is false under V2 by design. Not deleted |
| `test_context_split_disjoint_without_heldout_generation` | Its V1 body asserted disjointness of two slices of a dict, which V2 deliberately abandons (B3). Replaced with the instance-level invariant: distinct seeds, same family universe, held-out latent generation blocked |
| `test_all_calibration_variants_valid` | Now iterates applicable conditions and asserts that excluded cells refuse to render |
| `test_calibration_traps_marked_authored` | Updated for 56 items; asserts no V1 scenario text and that held-out traps are blocked |
| + `test_explicit_user_evidence_supersedes_injected_fault` | New (pipeline) |
| + `test_v2_complete_run_counts_and_stratified_outputs` | New (pipeline) |
| + `tests/test_benchmark_v2.py` | 52 new scientific-invariant tests |

Mutation check: nine defects were deliberately reintroduced one at a time (competing move without field; stale narrative leak; retraction text in resolution mode; unguarded held-out latent; C payload leaking `archetype`; thinking switch removed; supersession allowed on duplicate archetypes; old allocation rule; hardcoded 1,800 in the freeze gate). All nine were caught. The leakage mutation initially passed undetected because the test searched a re-serialised message whose inner JSON quotes were escaped; the test now inspects parsed payload keys.

## Reproduction

- Documented `pip install -e .`; verified in a fresh virtual environment with no `PYTHONPATH` (re-verified at packaging) from `python -m unittest discover -s tests`.
- `python scripts/check.py` still works without installation.

## Documentation

New: `protocol/protocol_v2_amendment.md`, `docs/benchmark_diversity_audit.md`, `docs/gpu_execution_plan.md`, `docs/application_research_note.md`, `docs/provenance.md`, this file. Rewritten: `README.md`, `docs/reliability_audit.md`, `protocol/FREEZE.md`, `manuscript/draft.md`, `Research_Execution_Status.md`. Amended: `protocol/evaluation_spec.md`, `protocol/psychology_spec.md`, `docs/ethics_and_scope.md`. Unchanged: `protocol/literature_review.md` (byte-identical to the supplied `Literature_Review.md`), `protocol/novelty_audit.md`, `protocol/protocol_v1.md`.

## V2.1 — evaluator mode (pre-freeze)

Resolves a protocol/code contradiction found in independent review of V2: the freeze gate required three valid judgments per primary calibration response and a pinned judge, while the protocol permitted proceeding without an automated evaluator.

| # | Change | H | Arch | SEPR | Bench | Anal |
|---|---|---|---|---|---|---|
| X1 | `evaluator_mode` (`validated_automated` / `manual_audit_only`) in config; `finalize` refuses while unset; recorded in the freeze, hence fixed before held-out materialisation | — | — | — | — | yes |
| X2 | Prospective evaluator-validation gate (`evaluation/evaluator_policy.py`; thresholds in config): per-kind sensitivity and negative-control specificity ≥ 7/8 with invalid items counted as errors; ≤ 5% invalid trap items; ≤ 20% sample disagreement; ≥ 95% calibration responses with three valid samples (V2 required 100%); evaluator ≠ primary model; trap-journal identity check | H4 arm conditional on mode | — | — | — | yes |
| X3 | Frozen aggregation and invalid-output policy; three samples described as repeated draws from one model, not independent raters | — | — | — | — | — |
| X4 | Manual mode: no judge constructed, `judge-traps` refused, configured judge rejected at freeze, semantic fields masked `UNAVAILABLE_NOT_VALIDATED` (previously `reliable_coverage` would have read 0 without a judge) | — | — | — | — | yes |
| X5 | New deterministic `decision_reliable_coverage`, reported in both modes | — | — | — | — | yes |
| X6 | `freeze --trap-dir` | — | — | — | — | — |
| X7 | Test fixture backend moved to `tests/tests_fixture.py` for reuse | — | — | — | — | — |

SEPR is unchanged: its attribution uses only deterministic typed decision violations, now asserted by a test. Hypotheses, architectures, benchmark, degradation definitions, the 110/550/1,650/8,250/600 design and the Qwen configuration are unchanged.

Tests: 125 → **145** (20 new evaluator-mode tests; one V2 freeze test superseded by them). Mutation check: four further mutations (invalid items counted as correct; semantic masking removed; gate result ignored; manual mode accepting a judge) were each caught by assertions. A first mutation run appeared to catch them only through import errors of a shared fixture; it was rerun with correct discovery against an unmutated baseline.
