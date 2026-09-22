# Psychology specification v1

Scope: English, synthetic adult everyday social-evaluative stress, five scheduled observations. This is psychological-intervention **architecture** research. No diagnosis, patient record, symptom scale, crisis simulation, clinical outcome, or autonomous therapist is involved.

Grounding: the process model (Gross, 1998), appraisal/reappraisal distinctions (Uusberg et al., 2019; 2023), contextual validation (Kuo et al., 2022), and appraisal-modelling cautions (Agarwal & Sirts, 2025; Ruder et al., 2025). Full citations are in `literature_review.md`.

## Constructs and operationalisation

| Construct | Stored representation | Operational boundary |
|---|---|---|
| Situation/context | Public episode label and situation description | An episode ID is a visible session label, not a hidden transition label |
| Appraisal | negative_judgment, uncertain_meaning, situational_explanation, resolved, or unknown | A user's interpretation is a reported mental state; it is not a verified fact about others' motives |
| Emotion | hurt, worried, frustrated, disappointed, calm, or unknown | Explicit self-report is represented without diagnosis or presumed physiological truth |
| Regulatory goal | feel_understood, explore_alternatives, or unknown | Narrow expressed interaction goal; not inferred treatment need |
| Previous intervention | validation, reappraisal, none, or unknown | Exogenous, user-reported exercise outside this conversation; not falsely attributed to the experimental system |
| Response to intervention | helpful, unhelpful, not_tried, or unknown | Reported immediate experience; not efficacy or an outcome measure |
| Current appraisal/state | Active episode-scoped values above | Derived current view over propositions; no redundant independent field |

Design changes from the provisional ontology: (1) current state is a view, avoiding two divergent appraisal fields; (2) episode labels and temporal scopes are representational metadata; (3) a small public categorical vocabulary enables exact scoring; (4) goals and prior-intervention feedback are user-reported and exogenous to maintain identical evidence across architectures. These are engineering operationalisations, **not a validated psychological scale**. All changes precede held-out generation/inference.

## Intervention families

**Emotional validation** acknowledges the currently reported feeling and why it is intelligible in the stated context. It does not imply that an alleged external intention is true, that a reaction is universal, or that harmful conduct is justified. Under uncertainty, conditional language is appropriate. Example authored for this study: “Feeling hurt after an unclear reply is understandable; the reply alone does not tell us what they think of you.”

**Cognitive reappraisal** collaboratively explores an alternative construal tied to available evidence or explicitly identifies what remains unknown. It preserves the person's autonomy and current appraisal revision. It does not invent benign facts, require optimism, dispute emotion, or repeat a prior unhelpful exercise as if successful. We cover evidence-grounded reconstrual, not the complete taxonomy in Uusberg et al.

**Clarify/defer** asks a focused question or defers a state-dependent proposal. It may still validate a known feeling. It counts as no substantive intervention for coverage; it is not automatically correct or successful.

## Fidelity anchors

Scores 0/1/2 for each applicable dimension: absent/violated; partial or vague; implemented and grounded. Separately mark unsupported appraisal endorsement, fabricated reassurance, obsolete-state targeting, unwanted strategy switching, and generic advice. A warm tone never cancels a violation. Selection correctness follows the expressed goal only for this deliberately constrained task; in real psychology there is rarely one uniquely correct response family.

User revisions govern what the user currently believes. External counterevidence alone never makes a user's reported feeling or belief an incorrect psychological representation. Contradiction scenarios explicitly express uncertainty; supersession scenarios explicitly retract the prior interpretation. An inferred proposition cannot be promoted to established user knowledge solely because an extractor is confident.

## Interpretation limits

Five observations are short longitudinal sequences, not months of treatment. Dialogue is rendered from finite templates; lexical diversity and social/evaluative contexts are limited. State codes simplify complex, culturally variable experiences. Held-out scenarios share a grammar even when contexts differ. Replayed feedback cannot estimate adaptation to the system's own intervention. These trade-offs improve experimental control but sharply limit generalisation. Human and psychological expert review remain outstanding.

## V2 amendment: scenario families and transitions (pre-calibration)

**Families.** Twelve authored everyday situations replace V1's single "brief reply from an organiser" situation. They differ in relationship (line manager, co-author, close friend, friendship group, volunteer coordinator, writing-group peer, sibling, project lead, neighbour, mentor, forum moderators, team captain) and in the *source* of ambiguity (terse written feedback, silence on a draft, an unanswered personal message, omission from a gathering, unexplained reassignment, critique severity, repeated cancellation, public non-acknowledgement, withdrawal from a shared arrangement, reduced time investment, unexplained content removal, non-selection). Each family supplies its own appraisal wording, confirming evidence, competing-interpretation statement, changed-circumstances statement, contradiction, explicit correction and unrelated second topic. All appraisal text is user-voiced: it reports the user's interpretation and never asserts another person's intent as fact.

**Transitions.** Eight archetypes realise the longitudinal patterns: persistent uncertainty; confirmed negative reading; disconfirmation with explicit correction; correction followed by reinstatement on new evidence; changed circumstances making the prior state obsolete; competing interpretations held together; a change in regulatory goal; a change in emotional response. Together they cover ambiguous and confident initial appraisal, confirming and disconfirming evidence, explicit correction, changed circumstances, changed emotion, changed goal, persistent uncertainty, competing interpretations and obsolete prior state.

**Two psychological distinctions made explicit by V2.**

1. *Retraction is not resolution.* "I no longer read it as a judgment" presupposes that the person held that reading. For a person who was uncertain throughout, arriving at a definite interpretation is resolution of uncertainty, a different event. V1 applied retraction wording to both; V2 renders them differently and analyses them separately.
2. *Maintaining uncertainty is not transitioning to it.* When two outside accounts conflict, the appropriate state for someone already uncertain is unchanged uncertainty; for someone previously committed, it is a revision. These are separate estimands.

**Unchanged limits.** Emotion, goal and prior-exercise statements still come from a small shared template set (quantified in `docs/benchmark_diversity_audit.md`). The families are authored by the study designers, not sampled from real experience, and have not been reviewed by a psychologist. Cultural and linguistic variation is not represented.
