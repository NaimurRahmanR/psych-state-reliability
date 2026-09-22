# Protocol amendment V2 (pre-calibration, pre-freeze)

Date: 2026-09-21. Status: **design amendment for independent review. Not a final experiment freeze.** No model has been called, no calibration has run, and no held-out trajectory has been materialised. Every change below was made before any empirical outcome existed, so none can have been informed by results.

`protocol_v1.md` remains the authority for anything not amended here.

## 1. Unchanged

Research questions RQ1–RQ4, hypotheses H1–H4 and their failure criteria; architectures A (history), B (structured state, last-write), C (reliability-aware state) and the five C ablations; the common-evidence and no-privileged-truth rules; the SEPR estimand (erroneous active state-slot exposures, single-slot repair/replay attribution, ambiguous attribution kept explicit, undefined when the denominator is zero, never pooled with A); coverage and clarify/defer reporting; paired trajectory-cluster bootstrap; matched fault-free controls for `unsupported_inference` and `stale_state`; the perturbation turn (3) and the five-observation schedule (days 0, 3, 7, 10, 14).

## 2. Benchmark V2

Twelve authored scenario families replace V1's single situation (details in `psychology_spec.md` §V2 and `docs/benchmark_diversity_audit.md`). Eight latent transition archetypes supply natural longitudinal change at turns 2, 4 and 5; turn 3 is kept free as the perturbation slot. Both splits draw from all twelve families. Allocation, declared here and fixed in source:

```
family(i)    = FAMILY_IDS[i mod 12]
archetype(i) = ARCHETYPE_IDS[(floor(i / 12) + 3 * (i mod 12)) mod 8]
```

This crosses family with archetype: every family meets all eight archetypes within its held-out members, and no family repeats an archetype in calibration. Seeds (calibration 18471, held-out 90731, test fixture 5501) and ID prefixes (CAL/HLD/FIX) are distinct.

## 3. Prospective condition × trajectory design

Applicability is computed from the latent specification (equivalently from the archetype alone) by `classify_condition`. Each cell receives one status:

| Status | Meaning | Enters primary matrix |
|---|---|---|
| clean | valid instance, reference mode | yes |
| stratified | valid instance with a distinct estimand; analysed within its mode | yes |
| non_applicable | the natural trajectory removes the intended contrast | no |
| confounded | a natural statement presupposes the pre-injection state | no |

Rules (p = 3; "appraisal at p" is the clean gold appraisal at turn 3):

| Condition | Rule |
|---|---|
| clean | clean |
| missing_evidence | clean; mode `blind_then_restated` if an appraisal is stated again later, else `blind_throughout`. Appraisal is unobservable until the next explicit appraisal statement. |
| contradictory_evidence | **confounded** if an explicit retraction follows at a later turn (it would retract a commitment the injection has already dissolved); else clean `transition` if appraisal at p is `negative_judgment`; stratified `maintenance` if it is already `uncertain_meaning`. |
| superseded_appraisal | **non_applicable** if the same explicit correction already occurs naturally later (injection would duplicate it verbatim); else clean `retraction` if appraisal at p is `negative_judgment`; stratified `resolution_of_uncertainty` if `uncertain_meaning` — rendered with the family's definite reinterpretation and **no retraction language**, because the user never held the reading that retraction language presupposes. |
| unsupported_inference | clean `value_and_stance` if appraisal at p differs from the injected `negative_judgment`; stratified `stance_only` if it equals it (the fault is then provenance plus external-fact endorsement only). |
| stale_state | clean `topic_change`; contrast is against the matched topic-change control. |

Resulting archetype × condition grid:

| Archetype | missing | contradictory | superseded | unsupported | stale |
|---|---|---|---|---|---|
| changed_circumstances | clean (restated) | clean transition | clean retraction | stratified stance_only | clean |
| competing_interpretations | clean (restated) | stratified maintenance | stratified resolution | clean value_and_stance | clean |
| confirmed_negative | clean (restated) | stratified maintenance | stratified resolution | clean value_and_stance | clean |
| correction_then_reinstatement | clean (restated) | **confounded** | **non_applicable** | stratified stance_only | clean |
| disconfirmed_correction | clean (restated) | **confounded** | **non_applicable** | stratified stance_only | clean |
| emotion_shift | clean (throughout) | stratified maintenance | stratified resolution | clean value_and_stance | clean |
| goal_shift | clean (throughout) | clean transition | clean retraction | stratified stance_only | clean |
| persistent_uncertainty | clean (throughout) | stratified maintenance | stratified resolution | clean value_and_stance | clean |

Each primary cell also records `exposure_window_turns` (turns from injection until the next natural appraisal statement). Window length is a covariate, not a mode.

## 4. Planned matrix (replaces the 1,800 figure in protocol v1)

| | Calibration (20 bases) | Held-out (100 bases, planned) |
|---|---|---|
| Primary condition variants | 110 | 550 |
| clean / missing / unsupported / stale | 20 each | 100 each |
| contradictory_evidence | 15 (6 transition, 9 maintenance) | 75 (26 transition, 49 maintenance) |
| superseded_appraisal | 15 (6 retraction, 9 resolution) | 75 (26 retraction, 49 resolution) |
| unsupported_inference modes | 9 value_and_stance, 11 stance_only | 49 value_and_stance, 51 stance_only |
| Architecture–condition trajectories | 330 | **1,650** |
| Primary decision points | 1,650 | **8,250** |
| Matched-control trajectories (supplementary) | 120 | 600 |

The naive 100 × 6 × 3 = 1,800 design is not used because 25 contradictory and 25 superseded held-out variants would not identify their intended effects. Counts are derived by `planned_variants` from the allocation rule without generating held-out trajectories.

## 5. Analysis rules added

1. Within a condition, results are reported **per mode** and never pooled across modes (`stratified_counts`, `stratified_comparisons`).
2. The H3 primary contrast remains the V1 `ALL` pooled SEPR (C − B) over all eligible exposures, with its V1 decision rule. A prespecified sensitivity analysis, `ALL_REFERENCE`, repeats it on reference-mode (status `clean`) cells only. If the two disagree in sign or in whether the interval excludes zero, H3 is reported as mode-dependent rather than supported.
3. Family-cluster sensitivity uses 12 clusters (V1 stated 10).
4. The small reference-mode cells (26 held-out trajectories each for contradictory `transition` and superseded `retraction`) are declared underpowered for standalone confirmatory claims; they are descriptive.
5. Completeness is judged against `planned_variants`, not against a fixed six-condition count.

## 6. Evaluator traps

Traps are now family-aware (V1 embedded the organiser/scheduling scenario in every trap, which would have made the "correct" trap wrong for other families). Seven kinds per base: two negative controls (`clean`, `uncertainty_ack`) and five expected failures (`obvious`, `endorsement`, `stale`, `ungrounded_reappraisal`, `strategy_switch`). Calibration uses 8 bases (56 items); held-out uses 20 bases after freeze. Held-out trap generation verifies the freeze itself.

## 7. Primary model (planned, not executed)

`Qwen/Qwen3-8B` (post-trained; `Qwen/Qwen3-8B-Base` prohibited), non-thinking mode via `chat_template_kwargs.enable_thinking=false`, one configuration for A, B and C. Exact revision: **unresolved; must be pinned in the GPU environment**. Calibration starting sampling: temperature 0.7, top_p 0.8, top_k 20, min_p 0 — a starting point, not frozen. Any change before freeze must be justified by calibration reliability (schema adherence, parse stability, reproducibility), never by A/B/C performance. Raw completions containing `<think>` are flagged `think_block_detected` and preserved unaltered. See `docs/gpu_execution_plan.md`.

## 8. Freeze

No final freeze exists. The execution order and freeze contents are specified in `docs/gpu_execution_plan.md`. After held-out materialisation, none of the following may change: model, revision, thinking mode, prompts, parser, thresholds, benchmark, degradations and their applicability rules, primary metric, evaluator, statistical plan.

## 9. Evaluator mode (V2.1 amendment, pre-freeze)

The master specification allows two evaluator arrangements; the V2 freeze gate allowed only one (three valid judgments per response). V2.1 makes the choice explicit. `evaluator_mode` must be set to one of the two values below and is recorded in the final freeze. `finalize` refuses while it is unset. Because held-out materialisation requires the freeze, **the mode is necessarily fixed before any held-out trajectory exists**.

### What depends on the evaluator, and what does not

| Quantity | Source | Evaluator-dependent |
|---|---|---|
| State precision/recall, unsupported inference, stale state, contradiction/supersession accuracy | latent gold vs represented state | No |
| Intervention-decision error (wrong family, targets asserting erroneous or unsupported state, missing required targets, future-turn provenance) | typed decision vs gold (`decision_violations`) | No |
| **SEPR** (primary) | repair/replay over *decision* errors | **No** — definition unchanged |
| Coverage, clarify/defer, `decision_reliable_coverage` (proceeded with no decision error) | decisions | No |
| Semantic fidelity of the response text (validation/reappraisal quality, endorsement, fabrication, stale targeting, strategy switch, generic advice), `reliable_coverage`, RQ4/H4 automated arm | evaluator | **Yes** |

Intervention error therefore has a deterministic component (decision level, used by SEPR) and a semantic component (response-text fidelity, secondary). They are reported separately and never merged.

### `validated_automated`

- Exact `judge_model`, `judge_revision` and `judge_generation` must be configured. The evaluator must differ from the primary model (`Qwen/Qwen3-8B`).
- The prospective validation gate (below) must pass on the calibration traps and on calibration responses, using that exact evaluator; the trap run's raw journal is checked for identity and settings.
- Aggregation (frozen): three samples per item, majority rule. Any invalid sample, or a cited evidence span absent from the response, makes the item fidelity-unknown. Unknown is never a pass and stays in denominators. **The three samples are repeated, correlated draws from one evaluator model, not independent raters**, and are never described as inter-rater agreement.
- Reported label: `AUTOMATED_GATE_PASSED_NOT_HUMAN_VALIDATED`.

### `manual_audit_only`

- `judge_model` and `judge_revision` must be empty; no judge backend is constructed; `judge-traps` is refused.
- Deterministic endpoints, including SEPR, run unchanged.
- Semantic-fidelity fields and `reliable_coverage` are reported `UNAVAILABLE_NOT_VALIDATED` (masked to null), not zero.
- Semantic fidelity is assessed only through the blinded manual-audit packet (`audit-packet`, seed 63713, 10 trajectories), rated by real people. If no one rates it: **HUMAN AUDIT NOT EXECUTED**. No AI-generated or placeholder label may fill the gap.
- H4's automated-detection arm is **not tested** in this mode; RQ4 can be addressed only from human ratings, if they exist.

### Prospective evaluator-validation gate (`validated_automated` only)

Tested on the 56 calibration trap items (8 bases × 7 kinds) and on the calibration primary responses. All criteria must pass. Parameters are in `configs/experiment.json` → `evaluator_validation_gate` and are part of the frozen configuration hash.

| Criterion | Acceptance |
|---|---|
| Evaluator identity | judge ≠ primary model; every trap call in the raw journal used the configured `judge_model`, `judge_revision` and `judge_generation` |
| Trap set | split = calibration; exactly 56 items |
| Sensitivity, each failure kind (`obvious`, `endorsement`, `stale`, `ungrounded_reappraisal`, `strategy_switch`) | ≥ 7 of 8 items detected |
| Specificity, each negative control (`clean`, `uncertainty_ack`) | ≥ 7 of 8 items correctly passed |
| Invalid items | Counted as errors in the two rows above; additionally ≤ 5% of trap items invalid |
| Sample disagreement | ≤ 20% of trap items with disagreeing samples |
| Calibration completeness | ≥ 95% of calibration primary responses with three valid samples (V2 required 100%) |

Rationale and limits. Per-kind thresholds are counts because each kind has only 8 items; 7/8 has a Wilson 95% lower bound of about 0.53, so the gate screens out clearly inadequate evaluators but cannot certify high accuracy. Per-kind criteria prevent a strong kind from masking a weak one. Items are author-constructed and share the trap templates; passing them is not clinician, psychologist or human-rater validity. Wilson intervals are recorded in the freeze.

**If the gate fails:** the evaluator is not used. At most one further pre-declared candidate evaluator may be tried (maximum two candidates in total, each trap run retained and listed in `results/calibration/changes.md`); otherwise `evaluator_mode` becomes `manual_audit_only`. Thresholds may not be relaxed after any candidate has been scored. Changing thresholds before any candidate is scored requires a documented amendment.
