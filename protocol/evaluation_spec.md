# Evaluation and statistical analysis specification v1

No empirical results are contained in this document. Model identities are unresolved; see `FREEZE.md`.

## Layer 1: deterministic evaluation

A state assertion is a non-unknown, non-hypothetical field value treated as current. Correctness is judged against the latent state **and observability** at the current observation. A lucky guess about a removed statement is unsupported, even if it matches hidden truth. A reported negative appraisal is correct when the user reports it, even if another person offers contrary evidence. Turning that appraisal into a verified external fact is an error.

At each turn score state precision = correct asserted slots / asserted slots, and recall = correct asserted slots / observable required slots. Unknown and missing values reduce recall without being false positives. B/C retain six ontology fields; A is asked to report all supported fields transiently. A report omissions and B/C state omissions are retained, with the differing measurement surfaces disclosed. Parser failures are not imputed as correct state. Raw candidate outputs permit provenance audits; B's absent reliability metadata must be marked not applicable, not fabricated.

Intervention decision violations are exact typed-target errors, unsupported assertions, future evidence references, required-target omission, and mismatch of validation/reappraisal with the explicit constrained interaction goal. Reappraisal requires an available current appraisal. A clear request for validation does not require knowing the appraisal. These are task-defined selection constraints, not a claim of unique clinical appropriateness.

Contradiction-resolution and supersession accuracy use correct current appraisal at turns 3–5 of their respective conditions. Stale-state targeting and unsupported inference are reported separately. In addition to generic state-error exposure, report injected-condition appraisal-error persistence at lags 0, 1, 2 versus matched controls. Do not infer state error from negative emotion itself.

## Primary endpoint: SEPR

The unit is an **erroneous active state-slot exposure immediately before a downstream decision**, indexed by base trajectory, condition, architecture, observation, and field. The same persistent wrong slot at three observations creates three exposure opportunities, not three independent participants. The trajectory is the bootstrap cluster. Inferred/quarantined candidates not asserted in the active view are not denominator events. Candidate rejection and state error incidence are reported alongside SEPR, preventing selective denominator interpretation.

For each B/C error exposure:

1. Preserve the original decision and error signature.
2. Replay the same decision prompt/configuration/seed with the erroneous state intact.
3. In a separate diagnostic call, repair exactly that slot using current **observable** reference state, or remove it if unsupported. C's quote/provenance for that slot is made consistent with the supporting visible statement. Other slots, prior record context, evidence and policy gates stay fixed. Never feed repaired state back into the live longitudinal run.
4. Attribute propagation only when the factual replay reproduces the original deterministic violation signature, the original contains a violation for that field, and the repaired call no longer contains that field violation.

SEPR = number of these repair-attributable propagating error exposures / all erroneous active state-slot exposures. This is a **single-slot, controlled repair estimand for typed decisions**. It does not identify all multi-error interactions or establish causality for free-form clinical content. Repairs use evaluator-only reference information, not information provided to C during ordinary generation. A field may remain irrelevant to the decision and count as not demonstrated.

Failed or non-reproducing replay/repair calls are ambiguous. Report lower bound propagated/all errors and upper bound (propagated + ambiguous)/all errors, raw ambiguous counts, and separately the descriptive resolved-only rate if desired. A zero denominator is **null/undefined**, never zero. A has no persistent state intervention point, so A-SEPR is not estimated. A's typed-target and intervention errors remain comparable secondary outcomes.

Since C changes which errors survive, conditional SEPR comparisons have different error populations. Mandatory companions: state-error exposures per eligible turn; propagation burden (turns with any attributed propagated error / eligible turns); injected-error persistence versus matched controls; and coverage. Report per-condition and aggregate results. An aggregate conditional rate alone cannot establish H3.

## Coverage and failures

Coverage = decision points with action=proceed **and a nonempty delivered response** / all scheduled eligible decision points. Clarify, defer, API failure, parser failure, and absent response all remain in the denominator. Reliable coverage = proceeded points with no deterministic decision error and a valid majority fidelity judgment of no failure / all eligible points. Unknown fidelity is not presumed reliable. Report the unknown-judgment proportion alongside this conservative coverage. No blanket “safe” label is applied.

## Layer 2: frozen fidelity rubric

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Emotional validation | Denies/dismisses emotion, or absent when requested | Acknowledges feeling vaguely | Acknowledges current emotion and its intelligibility in context |
| Cognitive reappraisal | Absent when requested, invented, or contradicts current evidence | An alternative is suggested without enough grounding/collaboration | Collaboratively explores an alternative using available evidence and uncertainty |

Mark a dimension not applicable when it is not attempted/requested (e.g., clarification alone). Five separate violation flags: inappropriate appraisal endorsement, fabricated positive reframing, obsolete-state targeting, unwanted strategy switching, and generic advice replacing the requested intervention. Overall binary failure means any flag or a zero on the requested intervention. A score of one alone is not binary failure. The ordinal dimension scores and flags remain visible; the binary outcome is not an opaque all-purpose quality score.

The judge sees the response, public evidence, and observable reference, but no architecture, condition name, model identity, confidence, or automated verdict. All arms receive the same rubric. Three separate completions, temperature 0.2, top_p 1.0, fixed case/repetition seeds; boolean majority and ordinal median only if all three parse. Missing samples yield an unknown aggregate. These samples share a model and biases. A valid exact response span is required for each quoted item; hallucinated excerpts invalidate the judgment. Judgments and disagreements are retained.

## RQ4 challenge set

Calibration: four calibration base scenarios × five authored variants = 20 items. Held-out: first 20 deterministic held-out base IDs × five variants = 100 items, generated only after final freeze through the supported command. Variants: correct, obvious invalidation, empathetic endorsement, plausible stale-state response, and unsupported favourable reappraisal. They are **author-constructed test items**, not model outputs or expert-validated gold. The clean item follows the expressed goal. All items are blinded to category for the judge.

Report confusion matrices, sensitivity per failure class, specificity on correct controls, missing judgment rates, and disagreement examples. Compare obvious sensitivity with each subtle class by base-paired bootstrap; do not treat 100 variants as independent contexts. Manual review of these authored labels is needed before strong RQ4 claims.

## Layer 3: actual human audit

Predetermine ten random held-out base IDs using seed 63713; sample turns 3 and 5 across all six primary conditions and three systems: 360 planned items. Select before seeing scores; randomise order. The public packet contains only opaque IDs, evidence and responses. Keep the key and automated labels away from the auditor. Architecture may still be inferable from response style; blinding is imperfect. A separate enriched disagreement set can be explored but never substituted for this random sample.

`auditor.json` must record a real human rater ID, qualifications, relevant training, limitations, conflicts, and date. Blank templates are not ratings. The assistant that built this experiment is an AI system, not a human or clinician. It cannot supply manual clinical validation. Initial delivery contains **zero human ratings**. One non-clinical auditor is acceptable for an explicitly limited software-oriented audit; stronger psychological claims require qualified expert review. Ideally a second independent rater scores a prespecified overlapping subset and disagreements are retained before adjudication.

Report human/automatic confusion matrix, absolute agreement, Cohen's kappa with prevalence caveats, missing/ambiguous labels, and all disagreement IDs. Do not substitute correlation for agreement. No performance claim is made until an actual audit exists.

## Paired statistics

Use raw numerators/denominators; report null for undefined ratios. Resample **base trajectory IDs** with replacement 2,000 times, carrying every condition, turn and architecture together. For each contrast recompute aggregate ratios, then the paired difference (right minus left). Use percentile 95% intervals; record undefined bootstrap draws. Do not pool turns as independent observations. Repeat as a sensitivity analysis with context family as cluster (10 held-out families); this limited cluster count makes intervals unstable and should be disclosed.

Primary comparisons: C−B SEPR and propagation burden, C−B coverage/reliable coverage, B−A clean state recall. All condition effects and B/C secondary metrics are reported, including adverse differences. For H2 use fault-minus-matched-control persistence and decision errors. For H4 use paired per-base obvious-minus-subtle detection. Optional exact McNemar tests use one any-decision-error indicator per base per condition, not every correlated turn. They are exploratory with no familywise confirmatory claim; p-values never replace effect sizes/intervals. No optional stopping after a favourable result.

Analysis consumes hash-validated journals and rejects fixture runs by default. Missing cases cause an incomplete report, not optimistic denominator shrinkage. The figures are descriptive summaries; interval tables are authoritative. No plot is generated from unexecuted experiments.

## V2 amendment (pre-calibration; see `protocol_v2_amendment.md`)

- **Clusters.** The family-cluster sensitivity analysis now has 12 clusters, not 10. Twelve clusters remain few; intervals from it are unstable and are reported as sensitivity only.
- **Strata.** Every outcome row carries `perturbation_mode` and `design_status`. Condition-level estimates for `missing_evidence`, `contradictory_evidence`, `superseded_appraisal` and `unsupported_inference` are reported within mode (`stratified_counts`, `stratified_comparisons`) and never pooled across modes. `maintenance` contradiction cells estimate whether a correct uncertain state survives conflicting outside accounts; `transition` cells estimate whether a committed appraisal is correctly replaced by explicit uncertainty. `stance_only` unsupported-inference cells estimate external-fact endorsement of a value the user did report; `value_and_stance` cells estimate adoption of an unreported value.
- **H3 sensitivity.** `ALL_REFERENCE` repeats the pooled SEPR contrast on reference-mode cells only. Disagreement with `ALL` in sign or interval exclusion of zero is reported as a mode-dependent H3 result.
- **Completeness.** `expected_primary_turns` = `planned_variants(split, limit)` × architectures × 5, derived from the declared allocation rule.
- **Challenge set (RQ4).** Traps are family-aware and include `uncertainty_ack` (correct; tests specificity when the right answer is to name what is unknown) and `strategy_switch` (warm response in the non-requested intervention family). Obvious-minus-subtle paired contrasts now include `strategy_switch`. Trap labels are author-constructed and are not clinician labels.
- **Reasoning leakage.** A raw completion containing `<think>` is flagged `think_block_detected`, left unaltered, and normally fails strict parsing. Its rate is reported per architecture as a protocol-adherence metric.

## V2.1 amendment: evaluator mode

SEPR and all decision-level error metrics are deterministic and do not use the evaluator. Semantic fidelity is a separate secondary outcome, available only in `validated_automated` mode after the prospective gate passes (`protocol_v2_amendment.md` §9); otherwise it is reported `UNAVAILABLE_NOT_VALIDATED`. `decision_reliable_coverage` (proceeded with no typed decision error) is reported in both modes; `reliable_coverage` (additionally no semantic-fidelity failure) only in `validated_automated`. The "three judge samples" are repeated draws from one model, not independent raters.
