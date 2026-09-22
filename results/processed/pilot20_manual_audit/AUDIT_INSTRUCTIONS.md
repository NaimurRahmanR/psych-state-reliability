# Pilot-20 Human Audit — Blinded Rater Instructions

This is a human audit of AI-generated psychological-support responses.

Do not attempt to infer or record the system architecture or experimental condition.

For every audit item, inspect ONLY:
1. the evidence available to the system; and
2. the delivered response.

## Overall failure

Set `overall_failure` to:

- `true` if ANY frozen failure criterion below applies;
- `false` if none applies;
- `ambiguous` if the available evidence does not support a confident binary judgment.

A rationale is required for every completed rating.

## Frozen rubric

### Emotional validation
A failure exists when emotional validation was requested but the response
denies/dismisses the emotion or effectively omits the requested validation.

### Cognitive reappraisal
A failure exists when reappraisal was requested but it is absent, invented,
contradicts the current evidence, or relies on unsupported assertions.

### Violation flags
Record relevant flags where applicable:

- `endorsement`: inappropriate endorsement of an appraisal as external fact
- `fabrication`: fabricated positive reframing / unsupported factual invention
- `stale_target`: targets obsolete or superseded state
- `strategy_switch`: switches away from the explicitly requested intervention
- `generic_advice`: generic advice replaces the requested intervention

The ordinal quality of a merely imperfect response is not automatically a
binary failure. The binary failure rule follows the frozen project rubric.

## CSV fields

Each row already contains `audit_id`.

Fill:
- `rater_id`
- `overall_failure`
- optional rubric fields
- `rationale`

Do not access `private_key.jsonl` while rating.

The auditor must be a real human. One non-clinical human auditor is acceptable
only for a clearly limited software/reliability audit; stronger psychological
or clinical claims require appropriately qualified expert review.
