# Prospective protocol v1

**Working title:** From Evidence to Intervention: Longitudinal State Reliability in Structured LLM-Mediated Psychological Support.

Date: 2026-09-20. Status: implementation and prospective design; model study **NOT EXECUTED**. A source-hashed design lock is distinct from a final model-calibrated experiment freeze. This document is not externally registered preregistration.

## Research questions and hypotheses

RQ1: How reliably do architectures maintain psychologically relevant state over repeated interactions?
RQ2: When represented psychological state is wrong, how often does that error affect a downstream intervention decision?
RQ3: Does reliability-aware state management reduce propagation compared with naive structured state?
RQ4 (secondary): Do automated judges detect state-induced intervention failures despite fluent, empathetic language?

H1: Structured state improves clean-condition representation/retention compared with dialogue-history prompting.
H2: Incorrect structured state can persist into later observations and affect intervention decisions.
H3: Reliability-aware state reduces propagation relative to naive structured state, potentially at a cost in clarification/defer coverage.
H4: Automated evaluation detects obvious intervention violations more reliably than subtle state-induced errors that remain coherent and empathetic.

These hypotheses are prospective and unchanged by outcomes: no held-out outcomes exist.

## Design and units

Twenty calibration base trajectories and a target of 100 held-out base trajectories. Six primary conditions × three architectures × five observations yields **1,800 held-out architecture–condition trajectories and 9,000 primary decision points**, if completed. Two additional matched fault-free controls per base yield 600 supplementary trajectories and 3,000 decision points. They are reported separately, not counted as primary observations.

The latent generator defines states before rendering text. Fixed seeds are 18471 (calibration) and 90731 (held-out); inference seed 263901; bootstrap seed 77129; audit seed 63713. Deterministic IDs are CAL-001…020 and HLD-001…100. Calibration uses two context families, and held-out uses ten other families. Each has ten fixed combinations of appraisal, emotion, expressed goal, and prior-exercise feedback. Language has three template variants. This is a finite factorial synthetic benchmark, not 100 independent naturalistic conversations. Domain-cluster sensitivity analysis is mandatory because templates and transitions are shared.

Five scheduled observations occur at days 0, 3, 7, 10, and 14. The design **replays exogenous user evidence**. Generated responses are not fed back into later user turns; prior exercises and reactions are explicitly described as occurring outside this conversation between check-ins. This preserves paired evidence but cannot study a user's response to the system's own intervention. All systems receive full available user-history prefixes, with no unequal truncation. Short history means H1 can be null or reverse.

## Architecture specification

**A — HISTORY.** Full user dialogue-history prefix, plus any experimental assistant-note fault, enters one decision call. A reports transient state targets alongside its decision and then produces a response. No state object persists between observations and no extracted state is supplied to A. Its output instrumentation is not an independent measure of latent internal activations.

**B — STRUCTURED STATE.** A common LLM extractor reads the prefix and proposes only new updates from the latest turn. B uses a last-write update rule, supports explicit expiry/corrections, and retains field values and their stance. It does not receive reliability annotations in its memory view. Decision and response use the same prompts/model/configuration as C. B can consult original evidence and override mistaken memory; it is not forced to trust faults.

**C — RELIABILITY-AWARE STATE.** Receives exactly the same candidate list as B. Added mechanisms are exact-quote/source validation; public episode/time scoping; separation of explicit/inferred and uncertain claims; contradiction records and supersession links; and clarification gating if required supported state is absent. Temporal expiry is 14 days or a visible topic change. The explicitly carried goal is exempt from topic expiry. All thresholds are engineering assumptions, not psychological constants. Exact quote matching is **not semantic entailment verification**; C can retain a wrong interpretation of a correctly quoted statement. No latent gold enters a live architecture.

Public vocabulary, task instructions, and response generation are shared. C's longer metadata can change token consumption; this is logged and is part of the architecture, not held constant by silently truncating other systems. B/C extraction is executed once per case/turn and shared byte-for-byte. A uses fewer calls. Comparisons concern architecture under the same model, not equal compute. Extractor and generator are the same configured model. The judge may be a different pinned model; three samples from one judge are correlated judgments, not independent experts.

## Conditions and isolation

| Condition | Exact intervention | What remains matched |
|---|---|---|
| Clean | None | All latent states and evidence |
| Missing evidence | Remove only initial appraisal sentence | Other statements and latent state; appraisal becomes unobservable for scoring |
| Contradictory evidence | At observation 3, conflicting reports plus the user's explicit uncertainty | Other state dimensions; evidence prefix before 3 |
| Superseded appraisal | At 3, explicit user correction and revised interpretation | Other state dimensions; evidence prefix before 3 |
| Unsupported inference | At 3, inject one appraisal candidate with empty provenance, inferred status, and external-fact stance | Entire user evidence stream; matched no-fault control |
| Stale state | At 3, replay one old-topic appraisal after a shared visible topic change | Exactly matched topic-change/no-fault control |

Stale-state versus ordinary clean is **not** an isolated one-factor contrast, because topic change is also present. The primary fault effect is stale-injection minus its topic-change/no-injection control. Unsupported-inference also has a no-injection control. These controls are necessary to avoid attributing ordinary context shift to injection.

For A, the injected proposition is presented as a possibly mistaken prior assistant note; B/C receive it through their candidate-memory channel. Underlying user evidence and fault semantics match, but injection sites differ by architecture. Therefore A's injected-condition comparisons are descriptive; B–C is the primary mechanism contrast. Faults contain no hidden truth. Their metadata reflects what a memory writer could expose, and represents detectable faults; it does not establish robustness to forged provenance or falsely confident explicit labels.

## Execution and stopping

1. Run software tests and calibration data checks; inspect calibration examples.
2. Select genuinely accessible generation/judge models and record immutable snapshot/revision identifiers, endpoints, and serving configuration. No IDs are invented in this package.
3. Run the real 20-base calibration matrix and evaluator challenge items. Review malformed outputs and fidelity rubric on calibration only. Any changes require recalibration with matching source hashes.
4. Generate final freeze manifest, pinning code, prompts, configs, tests, dependencies, and calibration dataset. Held-out access through the supported CLI is blocked until then.
5. Generate/execute the held-out matrix. Do not change prompts, ontology, thresholds, or analysis after observing its outcomes.
6. Analyze raw journals, prepare blinded audit, and execute the predefined ablations if justified.

One network attempt per call; failures are recorded and cached, with no silent selective retry. A new replay of failed calls must be a separately labelled run/version. Max 150,000 calls per backend is a fail-stop limit, not a spend estimate. Each request times out after 45 seconds. Inference is sequential and resumable. Approximate primary held-out budget: 3,000 shared extraction + 9,000 selection + 9,000 response + 27,000 judge calls, plus counterfactual repairs/replays. Supplementary controls add up to 3,000 selection + 3,000 response + 9,000 judgments. Actual calls/tokens must be counted from raw journals. No fees or completion time can be credibly estimated until an actual backend is selected.

## Failure and unsupported-hypothesis criteria

H1 is supported only if the clean B−A state-recall paired confidence interval is above zero, without evidence of a precision trade-off that invalidates the interpretation. A's transient output report versus B's stored representation is explicitly a measurement limitation. Otherwise no superiority claim.

H2 requires increased post-injection appraisal-error persistence and downstream error burden for B versus its matched no-fault control, with directionally consistent trajectory-cluster confidence intervals. An injection that is present only momentarily, does not change decisions, or has an effect indistinguishable from the control does not support a cascade claim.

H3's prespecified meaningful SEPR reduction is 5 percentage points (C−B ≤ −0.05), with a 95% paired interval below zero, plus reported propagation burden and coverage. A coverage loss exceeding 10 points is reported as a material trade-off, never hidden. These margins are research-design choices, not clinical thresholds. If C has zero erroneous-state exposures, its SEPR is undefined, not zero: report reduced error incidence/burden, without claiming demonstrated conditional SEPR improvement. A large ambiguous-attribution fraction weakens or blocks a causal claim.

H4 tests obvious minus subtle failure sensitivity using paired challenge sets. Null differences are retained. Automated/human binary disagreement above 20% triggers an explicit evaluator-unreliability finding; this is an operational flag, not a validated clinical standard. No actual human audit means fidelity remains unvalidated regardless of automated scores.

Parser/API failures above 5% in calibration block final freeze. Missing judge judgments block that freeze. Post-freeze failures stay in denominators; incomplete runs are labelled incomplete. Model identity drift, invariant violation, or frozen-file changes stop execution. An unavoidable correction requires an append-only amendment, new version/run directory, and disclosure of what held-out data had been seen; it cannot retain an unqualified untouched-test claim.

## Ablations

Five C ablations are implemented: remove provenance, temporal status, explicit/inferred gating, contradiction handling, or clarification gating. Execute all if feasible after a meaningful C−B difference, reusing the primary extraction journal. If budget prevents all, prioritize temporal and epistemic mechanisms and declare omitted runs. The held-out set is reused for explanatory ablations, not for tuning or a second confirmatory claim. Redundant guards may make individual ablations null; that is a valid result. Do not choose ablations only after inspecting appealing examples.
