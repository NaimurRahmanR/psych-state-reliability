# Public audit note

The frozen internal analysis archive contains the complete author-rating CSV, including free-text rationales and optional interface fields. The public repository distributes only the fields needed to reproduce the manuscript's descriptive audit result: `audit_id`, `rater_id`, `overall_failure`, plus the deblinding mapping.

The initial rating interface incorrectly defaulted `overall_failure` to `ambiguous`. Before deblinded aggregate reporting, the author explicitly confirmed that the exact rationale `valid response` meant pass/no overall failure, and the remaining ambiguous items were explicitly reviewed with no default selection. Final overall counts were 322 pass, 1 fail, and 1 genuinely ambiguous.

Optional validation/reappraisal/violation subfields from the initial interface are not used for manuscript inference. Automated semantic failure labels were unavailable for all 324 items because the final evaluator mode was `manual_audit_only`; therefore the `agreement.json` file records no comparable automated-human pairs (`n=0`). This is not missing human audit data.

The audit is descriptive author-blinded evidence, not independent clinical validation.
