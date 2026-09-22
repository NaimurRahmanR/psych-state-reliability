"""Pre-freeze evaluator policy.

The evaluator mode must be chosen and recorded in the final freeze, before any
held-out trajectory is materialised. Two modes exist:

validated_automated
    A separately configured evaluator model, pinned by model id and revision,
    passes the prospective validation gate below on calibration traps and on
    calibration responses. Its three samples per item are repeated draws from
    one model: correlated, NOT independent raters.

manual_audit_only
    No automated semantic-fidelity labels exist. Deterministic endpoints
    (state metrics, typed intervention-decision errors, SEPR, coverage) are
    unaffected. Semantic fidelity is reported UNAVAILABLE_NOT_VALIDATED and is
    assessed only through the blinded manual-audit packet, rated by real people.
    No label is ever fabricated or substituted by an AI assistant.

The gate is a minimum-adequacy screen on author-constructed traps. Passing it
does not establish clinician-level or human-level validity.
"""
from __future__ import annotations
import math
from pathlib import Path
from psyr.common import Journal, read_json

EVALUATOR_MODES = ("validated_automated", "manual_audit_only")
FAILURE_KINDS = ("obvious", "endorsement", "stale", "ungrounded_reappraisal", "strategy_switch")
NEGATIVE_CONTROL_KINDS = ("clean", "uncertainty_ack")
SEMANTIC_FIELDS = ("reliable_proceeded", "reliable_coverage", "validation_mean", "reappraisal_mean",
                   "endorsement_judged", "stale_target_judged", "judge_disagreements", "fidelity_valid")
UNAVAILABLE = "UNAVAILABLE_NOT_VALIDATED"


def semantic_available(config):
    """Automated semantic fidelity is reportable only in validated_automated mode."""
    return config.get("evaluator_mode") == "validated_automated"


def wilson(k, n, z=1.959964):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def _check_judge_identity(trap_dir, config):
    """Every trap judgment must come from exactly the configured evaluator."""
    path = Path(trap_dir) / "judge.jsonl"
    if not path.exists():
        return False, "trap run has no raw evaluator journal"
    calls = [r for r in Journal(path).records if r.get("kind") == "completion"]
    if not calls:
        return False, "trap run contains no evaluator calls"
    for r in calls:
        req = r["request"]
        if req.get("model") != config["judge_model"] or r.get("requested_revision") != config["judge_revision"]:
            return False, "trap evaluator identity differs from configured judge_model/judge_revision"
        if any(req.get(k) != v for k, v in config["judge_generation"].items()):
            return False, "trap evaluator generation settings differ from configured judge_generation"
    return True, f"{len(calls)} evaluator calls match configured identity and settings"


def evaluate_validation_gate(trap_dir, calibration_primary_rows, config):
    """Prospective validation gate for validated_automated mode. Returns a report;
    `passed` is True only if every criterion passes. Invalid items count as errors."""
    gate = config["evaluator_validation_gate"]
    criteria = []

    def add(name, ok, detail):
        criteria.append({"criterion": name, "passed": bool(ok), "detail": detail})

    add("evaluator_differs_from_primary_model",
        config.get("judge_model") and config["judge_model"] != config["model"],
        f"judge={config.get('judge_model')} primary={config['model']}")
    trap_dir = Path(trap_dir) if trap_dir else None
    report_path = trap_dir / "trap_analysis.json" if trap_dir else None
    if not report_path or not report_path.exists():
        add("trap_analysis_present", False, "no trap_analysis.json")
        return {"passed": False, "criteria": criteria}
    ok, detail = _check_judge_identity(trap_dir, config)
    add("trap_evaluator_identity", ok, detail)
    rep = read_json(report_path)
    items = [r for r in Journal(trap_dir / "trap_judgments.jsonl").records]
    add("trap_split_is_calibration", rep.get("split") == gate["trap_split"], f"split={rep.get('split')}")
    add("trap_item_count", len(items) == gate["trap_items_required"],
        f"{len(items)} items (required {gate['trap_items_required']})")

    for kind in FAILURE_KINDS:
        b = rep["by_kind"].get(kind, {})
        total = b.get("n", 0) + b.get("missing", 0)
        detected = b.get("tp", 0)  # invalid (missing) items are not detections
        add(f"sensitivity:{kind}", total and detected >= gate["min_detected_per_failure_kind"],
            {"detected": detected, "items": total, "wilson95": wilson(detected, total)})
    for kind in NEGATIVE_CONTROL_KINDS:
        b = rep["by_kind"].get(kind, {})
        total = b.get("n", 0) + b.get("missing", 0)
        correct = b.get("tn", 0)    # invalid items are not correct passes
        add(f"specificity:{kind}", total and correct >= gate["min_correct_per_negative_control_kind"],
            {"correct": correct, "items": total, "wilson95": wilson(correct, total)})

    disagree = sum(r.get("judge_disagreement") is True for r in items)
    invalid = sum(r.get("fidelity_failure") is None for r in items)
    add("trap_sample_disagreement", items and disagree / len(items) <= gate["max_trap_sample_disagreement_fraction"],
        {"items_with_disagreeing_samples": disagree, "items": len(items)})
    add("trap_invalid_items", items and invalid / len(items) <= gate["max_trap_invalid_fraction"],
        {"invalid_items": invalid, "items": len(items)})

    responses = [r for r in calibration_primary_rows if r.get("response")]
    complete = sum(r.get("judge_valid") == 3 for r in responses)
    add("calibration_response_judgment_completeness",
        responses and complete / len(responses) >= gate["min_calibration_responses_with_3_valid_samples"],
        {"responses": len(responses), "with_3_valid_samples": complete})
    return {"passed": all(c["passed"] for c in criteria), "criteria": criteria,
            "note": "Minimum-adequacy screen on author-constructed traps; not clinician or human validation. "
                    "Three samples per item are repeated draws from one evaluator model, not independent raters."}


def check_mode_configuration(config):
    mode = config.get("evaluator_mode")
    if mode not in EVALUATOR_MODES:
        raise RuntimeError(f"evaluator_mode must be one of {EVALUATOR_MODES} and recorded before freeze; got {mode!r}")
    if mode == "validated_automated":
        if config.get("judge_model") in (None, "") or config.get("judge_revision") in (None, ""):
            raise RuntimeError("validated_automated requires judge_model and judge_revision")
    else:
        if config.get("judge_model") or config.get("judge_revision"):
            raise RuntimeError("manual_audit_only must not configure an automated judge; clear judge_model/judge_revision")
    return mode
