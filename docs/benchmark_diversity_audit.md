# Benchmark diversity audit (V2)

Date: 2026-09-21. Scope: the 20 calibration trajectories, plus the *declared* held-out allocation rule. No held-out trajectory was generated for this audit.

Every number below is produced by code and can be regenerated:

```bash
python scripts/psyr.py diversity-audit                  # -> results/processed/benchmark_diversity.json
python scripts/diversity_v1_v2.py <path/to/V1.zip>      # -> results/processed/diversity_v1_vs_v2.json
```

`diversity_v1_v2.py` loads the V1 generator directly from the authoritative V1 ZIP (member `src/psyr/benchmark/dataset.py`, SHA-256 `fc30bd25821e743c62da506e686a57a20619ebd8e01f43f85e11d9f876e93d71`) and applies **the same metric code** to both versions. A test asserts that the committed V2 audit JSON equals a fresh recomputation.

**Verdict in one line:** V2 fixes V1's *conceptual* narrowness (one situation → twelve families × eight transition archetypes, crossed) but only partly fixes *surface templating*: 0.5515 of rendered characters are statement strings reused across families.

## 1. Conceptual diversity (design variables)

These describe what the trajectories are *about*. They are counts of latent design choices, not of words.

| Dimension | V1 | V2 |
|---|---|---|
| Distinct situations | 1 (shared by all 20) | 12 (at most 2 trajectories each) |
| Scenario families in calibration | 2 activity nouns on one frame | 12 |
| Relationship types | 1 (organiser) | 12 |
| Sources of ambiguity | 1 (brief reply) | 12 |
| Transition archetypes | one fixed schedule: a goal flip at turn 4 in every trajectory | 8 |
| Transition types covered in clean trajectories | 3 of the 10 required (changed goal; ambiguous initial and persistent uncertainty in half); appraisal never revised | all 10, plus confident initial appraisal |
| Family × archetype crossing (held-out plan) | not applicable | every family meets all 8 archetypes |

Calibration distributions (V2, from `benchmark_diversity.json`):

| Variable | Distribution |
|---|---|
| Family | 8 families × 2, 4 families × 1 (social_exclusion, team_selection, volunteering_role, workplace_feedback) |
| Archetype | changed_circumstances 3, competing_interpretations 3, correction_then_reinstatement 3, goal_shift 3; confirmed_negative 2, disconfirmed_correction 2, emotion_shift 2, persistent_uncertainty 2 |
| Initial appraisal | negative_judgment 11, uncertain_meaning 9 |
| Final appraisal | negative_judgment 8, uncertain_meaning 7, resolved 3, situational_explanation 2 |
| Initial emotion | disappointed 9, hurt 4, worried 4, frustrated 3 |
| Final emotion | disappointed 7, hurt 4, worried 4, frustrated 3, calm 2 |
| Regulatory goal, turn 1 → turn 5 | explore_alternatives 11 → 9; feel_understood 9 → 11 |
| Intended intervention, turn 1 → turn 5 | reappraisal 11 → 9; validation 9 → 11 |
| Transition types (occurrences) | confident_initial 11, ambiguous_initial 9, obsolete_prior_state 8, changed_regulatory_goal 6, confirming_evidence 5, explicit_correction 5, persistent_uncertainty 5, changed_circumstances 3, competing_interpretations 3, changed_emotional_response 2, disconfirming_evidence 2 |

Observations: emotion is skewed toward *disappointed* (9/20 initially) because emotion is drawn by a seeded RNG from four values, not stratified; `disconfirming_evidence` and `changed_emotional_response` appear only twice each in calibration. Neither is balanced by design.

### Held-out allocation (declared rule only; 0 materialised)

`family = FAMILY_IDS[i mod 12]`, `archetype = ARCHETYPE_IDS[(floor(i/12) + 3·(i mod 12)) mod 8]`.

- Per family: academic_collaboration, family_plans, friendship_delay, hobby_critique 9 each; the other eight families 8 each.
- Per archetype: changed_circumstances, competing_interpretations, correction_then_reinstatement, goal_shift 13 each; the other four 12 each.
- Every family is paired with all 8 archetypes.

**Defect found and fixed during this audit.** The first V2 allocation used `archetype = (3i) mod 8`. For a fixed family the held-out members are `i = f + 12k`, giving `(3f + 4k) mod 8`, i.e. only **2** archetypes per family. Family-level results would have been confounded with transition type. The Latin-square-style rule above removes this; a test (`test_family_and_archetype_are_crossed_not_confounded`) guards it and was confirmed to fail under the old rule.

## 2. Degradation applicability

Condition applicability is now a prospective, rule-based design (`protocol_v2_amendment.md` §3), not an assumption that all six conditions apply everywhere.

| Condition | Calibration: status counts | Primary modes (calibration / held-out plan) |
|---|---|---|
| clean | clean 20 | — (20 / 100) |
| missing_evidence | clean 20 | blind_then_restated 13 / 63; blind_throughout 7 / 37 |
| contradictory_evidence | clean 6, stratified 9, **confounded 5** | transition 6 / 26; maintenance 9 / 49 |
| superseded_appraisal | clean 6, stratified 9, **non_applicable 5** | retraction 6 / 26; resolution_of_uncertainty 9 / 49 |
| unsupported_inference | clean 9, stratified 11 | value_and_stance 9 / 49; stance_only 11 / 51 |
| stale_state | clean 20 | topic_change 20 / 100 |

Primary condition variants: calibration 110 (naive 120); held-out 550 (naive 600) → 1,650 architecture–condition trajectories, 8,250 decision points.

The interim report stated that 14/20 calibration trajectories had "perturbation–archetype interactions". That label conflated three different things. Rendering every archetype under every condition showed the actual situation:

1. **Different estimand, still valid** (now `stratified`): contradiction when the user is already uncertain; supersession when the user never committed; unsupported inference whose value matches the user's own report.
2. **No contrast** (now `non_applicable`): injected correction duplicates a verbatim natural correction one turn later.
3. **Confounded** (now `confounded`): a natural retraction follows an injected contradiction and retracts a commitment the user had already abandoned.

It also exposed defects the value-level labels missed, now fixed: a gold/dialogue mismatch in `competing_interpretations × superseded` (gold said *situational* while the user said "I hold both at once"); retraction wording applied to users who had never held the retracted view (also present in V1); and old-topic narrative evidence leaking into the new topic in `stale_state`.

## 3. Lexical diversity (surface words)

Computed over the rendered clean calibration dialogue, content words only.

| Metric | V1 | V2 |
|---|---|---|
| Content tokens | 1,270 | 1,530 |
| Distinct content tokens | 74 | 357 |
| Type–token ratio | 0.058 | 0.233 |
| Mean pairwise Jaccard (all 190 pairs) | 0.735 | 0.324 |
| Mean Jaccard, same family | 0.772 | 0.652 |
| Mean Jaccard, different family | 0.701 | 0.310 |
| Maximum pairwise Jaccard | 0.961 | **0.917** |

Lexical statistics are necessary but not sufficient evidence of conceptual diversity: V1 could have raised its type–token ratio by synonym substitution without changing what any trajectory was about. They are reported here only alongside §1.

The maximum pairwise Jaccard of 0.917 is a genuine residual weakness. It comes from same-family pairs: two trajectories in one family share the situation sentence and draw appraisal wording from the same three variants.

## 4. Structural and template reuse

| Metric | V1 | V2 |
|---|---|---|
| Statements rendered | 240 | 245 |
| Distinct statement strings | 26 (0.108) | 79 (0.322) |
| Distinct turn field-frames | 4 | 8 |
| Most common turn frame share | 0.40 | 0.36 |
| Characters from shared-template *fields* | 0.8340 | **0.6151** |
| Characters from strings reused across ≥2 families | 0.9451 | **0.5515** |

Two template-dependence measures are reported because they answer different questions:

- *Shared-template fields* counts characters from fields whose text is not family-authored in V2 (context, emotion, goal, prior exercise, reaction to exercise, "no new information" filler). It is label-based and **flatters V1**, because V1's single situation sentence is labelled narrative and is therefore counted as non-shared although all 20 trajectories use it.
- *Cross-family reuse* is empirical: a statement string counts as reused if it appears in trajectories of two or more families. It does not depend on field labels.

**Residual template dependence (recomputed, not carried over from the interim estimate): 0.6151 of V2 rendered characters come from shared-template fields, and 0.5515 come from strings reused across families** (about 62% and 55%). The interim figure (~62%) was close for the first measure; the second measure is new.

What remains templated in V2:

- Emotion self-report: three sentence frames with the emotion word substituted ("I feel hurt.").
- Regulatory goal: two fixed sentences.
- Prior exercise and reaction: fixed sentences.
- Context statement: one frame ("This is about …") with a family phrase.
- The turn-3 "no new information today" filler in clean trajectories, which also makes turn 3 recognisably empty in the clean condition.

## 5. Qualitative inspection

Rendered variants for all 110 calibration primary cells are in `data/calibration/examples.jsonl` (these include gold and must never reach a live architecture). Inspection points:

- Situations genuinely differ in what is ambiguous and why; the benign explanations differ in kind (workload, fieldwork, rotation policy, automated filter, shift pattern, template convention, family emergency).
- The regular turn structure remains visible: turn 1 always states situation, context, appraisal, emotion, goal and "no exercise yet" in that order; turn 2 always reports an outside exercise; turn 3 is empty in clean trajectories. A model could learn nothing from this (there is no training), but the regularity limits realism and makes every trajectory look like a structured intake form rather than a conversation.
- Appraisal wording is family-specific but still declarative and explicit ("My interpretation is that …"). Real users rarely label their appraisals this cleanly, so the benchmark tests state management under unusually legible evidence.
- All twelve families concern social-evaluative ambiguity with a potentially rejecting other party. Other everyday stressors (practical, health-adjacent, financial) are deliberately excluded for non-clinical scope, which also narrows the construct.

## 6. Residual limitations

1. Surface templating remains substantial (55–62% by the two measures).
2. Same-family trajectory pairs are lexically close (max Jaccard 0.917).
3. The turn schedule is identical across trajectories; perturbations always land at turn 3.
4. Emotion is not stratified and is skewed toward *disappointed* in calibration.
5. Reference-mode cells for contradiction (`transition`) and supersession (`retraction`) are small: 26 held-out trajectories each.
6. Families, archetypes and wording are authored by the designers; no psychologist or lay reader has reviewed them for plausibility.
7. English only; one cultural register.

V2 is a materially stronger controlled benchmark than V1. It is not a naturalistic one, and nothing in this audit supports claims about generalisation to real conversations.
