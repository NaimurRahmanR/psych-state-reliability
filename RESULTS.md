# Frozen Pilot-20 Results

These are the frozen held-out pilot results used in the manuscript. Confidence intervals use 2,000 paired bootstrap repetitions clustered by base trajectory with seed 77129.

## Integrity

- 20 selected held-out bases
- 106 applicable primary base-condition variants
- 1,590 primary architecture-turn outcomes
- 600 matched-control outcomes
- 2,190 total outcomes
- 2,190 unique outcome keys
- 0 extra bases executed

The compute/time amendment was locked before held-out scientific performance was inspected.

## H1 - clean structured retention

- B - A state recall: **-0.0883**, 95% CI **[-0.1983, 0.0050]**
- B - A state precision: **-0.0039**, 95% CI **[-0.0791, 0.0616]**
- Prospective criterion: **not met**

## H2 - persistence and downstream burden

Unsupported inference, B fault minus matched control:

- persistence: **+0.2833** [0.1667, 0.4167]
- decision error: **+0.0200** [0.0000, 0.0600]
- coverage: **0.0000** [0.0000, 0.0000]

Stale state, B fault minus matched control:

- persistence: **+0.1000** [0.0000, 0.2500]
- decision error: **0.0000** [0.0000, 0.0000]
- coverage: **0.0000** [0.0000, 0.0000]

Interpretation: unsupported inference clearly persisted under the injected-fault condition, but the pilot did not establish the full prospective downstream cascade criterion.

## H3 - reliability-aware C versus structured B

Primary `ALL` contrast:

- C - B SEPR: **+0.1018** [0.0527, 0.1541]
- C - B propagation burden: **-0.1811** [-0.2648, -0.1060]
- C - B coverage: **-0.7698** [-0.8920, -0.6333]
- C - B decision-reliable coverage: **-0.0981** [-0.1473, -0.0537]

Reference-mode sensitivity (`ALL_REFERENCE`):

- C - B SEPR: **+0.1075** [0.0547, 0.1648]
- C - B propagation burden: **-0.2000** [-0.2784, -0.1266]
- C - B coverage: **-0.7468** [-0.8785, -0.6050]
- C - B decision-reliable coverage: **-0.0911** [-0.1418, -0.0474]

Prospective H3 criterion: **not met**. The direction was not mode-dependent under the frozen sensitivity rule.

The result should not be reduced to "C is worse". C substantially reduced the number of exposed/propagated opportunities, largely through deferral, while the conditional propagation probability among surviving erroneous-state exposures was higher. Absolute burden and conditional reliability therefore answer different questions.

## H4 - automated semantic evaluation

**Not tested.** The final evaluator mode was `manual_audit_only`; `automated_failure` was unavailable for all 324 manual-audit items. Sensitivity, specificity, agreement, and Cohen's kappa are therefore undefined rather than zero.

## Descriptive response-text audit

A deterministic seed selected 10 pilot bases and 324 response-text items. One non-clinical author rater completed all items while blinded to architecture and condition.

- pass: **322**
- fail: **1**
- ambiguous: **1**
- evaluable: **323**
- descriptive failure proportion among evaluable items: **1/323 = 0.00310**

By architecture: A 108/108 pass; B 107 pass + 1 ambiguous; C 107 pass + 1 fail. The single failure occurred in the stale-state condition. These subgroup counts are descriptive only because there is one author rater and only one failure event.

The audit is not an independent clinical validation. The rater was also the study author/developer, aggregate experiment results had been seen before audit completion, and the initial interface defaulted the overall field to `ambiguous`; the UI artifact was corrected before deblinded aggregate reporting using explicit human confirmation. Optional sub-rating fields from the initial UI are not used for manuscript inference.

## Post-freeze robustness audit

The prospective inference is unchanged; these are secondary sensitivity checks on the frozen 2,190-outcome journal.

For H3 `ALL`:

- **SEPR C - B:** frozen 2,000-draw CI [0.0527, 0.1541]; 10,000-draw CI [0.0539, 0.1544]; context-family-cluster CI [0.0421, 0.1608]. All 20 leave-one-base-out point estimates were positive (range **+0.0894 to +0.1126**).
- **Propagation burden C - B:** frozen CI [-0.2648, -0.1060]; 10,000-draw CI [-0.2685, -0.1038]; context-family-cluster CI [-0.3000, -0.0967]. All 20 leave-one-base-out estimates were negative (range **-0.1960 to -0.1600**).
- **Coverage C - B:** frozen CI [-0.8920, -0.6333]; 10,000-draw CI [-0.8927, -0.6370]; context-family-cluster CI [-0.9120, -0.6350]. All 20 leave-one-base-out estimates were negative (range **-0.8040 to -0.7560**).
- **Decision-reliable coverage C - B:** frozen CI [-0.1473, -0.0537]; 10,000-draw CI [-0.1471, -0.0528]; context-family-cluster CI [-0.1462, -0.0531]. All 20 leave-one-base-out estimates were negative.

H1 clean recall remained negative in all 20 leave-one-base-out point estimates, although its bootstrap interval remained borderline and included zero. Unsupported-inference persistence remained positive under all leave-one-base-out checks and under alternative clustering. Bootstrap endpoint variation across five fixed seeds was small for the main H3 effects and did not alter their directions.

These robustness checks are **post-freeze** and are not used to redefine the prospective criteria. They do not provide cross-model robustness, independent-rater robustness, or external/clinical validity. Full machine-readable results are in `results/publication/robustness_audit.json`.

## Secondary condition decomposition

`results/publication/condition_effects.csv` is a post-freeze publication derivation from the frozen outcome journal using the same paired bootstrap implementation. It is labelled secondary and did not alter any prospective criterion or system behavior.
