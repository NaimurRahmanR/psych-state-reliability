# Freeze record

**FINAL EXPERIMENT FREEZE: NOT YET CREATED.**

Date of this record: 21 September 2026. Design version: `design-v2` (see `protocol_v2_amendment.md`).

No model calibration, no held-out materialisation and no held-out inference has occurred. `protocol/freeze_manifest.json` does not exist, so every supported held-out path (latent generation, `build_split`, the `dataset`/`run`/`judge-traps` CLI commands, held-out traps) refuses to run.

`protocol/design_lock.json` is a hashed snapshot of the V2 design submitted for independent review. It is **not** a final freeze and does not authorise held-out access. The V1 snapshot is retained at `protocol/archive/design_lock_v1.json` as an audit trail.

| Freeze element | Current state |
|---|---|
| H1–H4, architectures, SEPR | `protocol_v1.md` (unchanged by V2) |
| Benchmark, allocation, condition design | `protocol_v2_amendment.md`; `src/psyr/benchmark` |
| Primary model | `Qwen/Qwen3-8B`, non-thinking — **revision UNRESOLVED** |
| Generation configuration | Calibration starting point only (T 0.7, top_p 0.8, top_k 20, min_p 0) — **NOT FROZEN** |
| Evaluator mode | **UNDECIDED** (`validated_automated` or `manual_audit_only`; must be recorded in the freeze, before held-out materialisation) — `protocol_v2_amendment.md` §9 |
| Evaluator model | **UNSELECTED** (required only for `validated_automated`) |
| Prompts, parser, thresholds | `configs/`, `src/psyr/evaluation/schema.py` — subject to calibration-only revision |
| Statistical plan | `evaluation_spec.md` with V2 amendment |

`finalize` refuses to freeze while `model_revision` or `evaluator_mode` is unset, while calibration is incomplete against the V2 design, or while calibration parser/API failures exceed 5%. In `validated_automated` mode it additionally requires a pinned judge and a passing evaluator-validation gate; in `manual_audit_only` mode it requires that no judge is configured. The required order of operations is in `docs/gpu_execution_plan.md`.

These controls are procedural integrity checks, not a security boundary against a researcher who deliberately edits them. Independent review remains necessary.
