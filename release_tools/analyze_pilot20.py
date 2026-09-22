#!/usr/bin/env python3
"""Recompute the locked pilot-20 statistics from the committed merged outcome journal.

This is a post-freeze release wrapper. It does not alter the frozen source, protocol,
or authoritative result files. It reuses the frozen metric/bootstrap implementation
and validates the amended 20-base denominator fixed before held-out performance was seen.
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from psyr.analysis.report import metric_clusters, summarize
from psyr.analysis.statistics import paired_ratio_bootstrap
from psyr.common import read_json

SELECTED = {
    "HLD-001", "HLD-002", "HLD-003", "HLD-004", "HLD-005",
    "HLD-012", "HLD-018", "HLD-027", "HLD-029", "HLD-032",
    "HLD-047", "HLD-048", "HLD-049", "HLD-066", "HLD-067",
    "HLD-068", "HLD-083", "HLD-089", "HLD-097", "HLD-100",
}
EXPECTED_CONDITION_BASES = {
    "clean": 20,
    "contradictory_evidence": 13,
    "missing_evidence": 20,
    "stale_state": 20,
    "superseded_appraisal": 13,
    "unsupported_inference": 20,
}
REPS = 2000
SEED = 77129


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def effect(e):
    return {
        "difference": e["difference_b_minus_a"],
        "ci_low": e["ci_low"],
        "ci_high": e["ci_high"],
        "clusters": e["clusters"],
    }


def paired(left, right, metric):
    a = metric_clusters(left, metric, "base_id")
    b = metric_clusters(right, metric, "base_id")
    assert set(a) == set(b)
    return paired_ratio_bootstrap(a, b, repetitions=REPS, seed=SEED)


def precision_clusters(rows):
    out = defaultdict(lambda: [0, 0])
    for r in rows:
        out[r["base_id"]][0] += r["state_correct"]
        out[r["base_id"]][1] += r["state_asserted"]
    return dict(out)


def paired_precision(left, right):
    a, b = precision_clusters(left), precision_clusters(right)
    assert set(a) == set(b)
    return paired_ratio_bootstrap(a, b, repetitions=REPS, seed=SEED)


def close(a, b, tol=1e-12):
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol)


def check_effect(name, got, frozen):
    for gk, fk in [("difference", "difference_b_minus_a"), ("ci_low", "ci_low"), ("ci_high", "ci_high")]:
        assert close(got[gk], frozen[fk]), f"{name} {gk}: {got[gk]} != {frozen[fk]}"


def main():
    merged = ROOT / "results/processed/pilot20_final/outcomes_merged.jsonl"
    frozen_path = ROOT / "results/processed/pilot20_final/pilot20_analysis.json"
    rows = load_jsonl(merged)
    frozen = read_json(frozen_path)

    assert len(rows) == 2190
    assert len({r["key"] for r in rows}) == 2190
    assert {r["base_id"] for r in rows} == SELECTED
    assert all(r["split"] == "heldout" and r["kind"] == "turn_outcome" for r in rows)

    primary = [r for r in rows if not r["control"]]
    controls = [r for r in rows if r["control"]]
    assert len(primary) == 1590 and len(controls) == 600
    for condition, bases in EXPECTED_CONDITION_BASES.items():
        assert sum(r["condition"] == condition for r in primary) == bases * 15

    overall = {a: summarize([r for r in primary if r["architecture"] == a]) for a in "ABC"}
    for arch in "ABC":
        for k in ["turns", "state_recall", "state_precision", "decision_error_rate", "coverage", "sepr"]:
            assert close(overall[arch].get(k), frozen["overall"][arch].get(k)), f"overall {arch} {k}"

    clean_a = [r for r in primary if r["condition"] == "clean" and r["architecture"] == "A"]
    clean_b = [r for r in primary if r["condition"] == "clean" and r["architecture"] == "B"]
    h1_recall = effect(paired(clean_a, clean_b, "state_recall"))
    h1_precision = effect(paired_precision(clean_a, clean_b))
    check_effect("H1 recall", h1_recall, frozen["H1"]["state_recall_B_minus_A"])
    check_effect("H1 precision", h1_precision, frozen["H1"]["state_precision_B_minus_A"])

    h2 = {}
    for condition in ("unsupported_inference", "stale_state"):
        fault = [r for r in rows if not r["control"] and r["condition"] == condition and r["architecture"] == "B"]
        control = [r for r in rows if r["control"] and r["condition"] == condition and r["architecture"] == "B"]
        h2[condition] = {
            "persistence_fault_minus_control": effect(paired(control, fault, "persistence")),
            "decision_error_fault_minus_control": effect(paired(control, fault, "decision_error_rate")),
            "coverage_fault_minus_control": effect(paired(control, fault, "coverage")),
        }
        for k, got in h2[condition].items():
            check_effect(f"H2 {condition} {k}", got, frozen["H2"][condition][k])

    def h3(subset):
        b = [r for r in subset if r["architecture"] == "B"]
        c = [r for r in subset if r["architecture"] == "C"]
        return {
            "sepr": effect(paired(b, c, "sepr")),
            "propagation_burden": effect(paired(b, c, "propagation_burden")),
            "coverage": effect(paired(b, c, "coverage")),
            "decision_reliable_coverage": effect(paired(b, c, "decision_reliable_coverage")),
        }

    h3_all = h3(primary)
    h3_ref = h3([r for r in primary if r.get("design_status") == "clean"])
    for mode, got in [("ALL", h3_all), ("ALL_REFERENCE", h3_ref)]:
        for k, e in got.items():
            check_effect(f"H3 {mode} {k}", e, frozen["H3"][mode][k])

    out = {
        "integrity": {"bases": 20, "outcomes": 2190, "primary": 1590, "controls": 600, "unique_keys": 2190},
        "H1": {"state_recall_B_minus_A": h1_recall, "state_precision_B_minus_A": h1_precision},
        "H2": h2,
        "H3": {"ALL": h3_all, "ALL_REFERENCE": h3_ref},
        "overall": overall,
    }
    out_dir = ROOT / "results/recomputed"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pilot20_core_recomputed.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("FROZEN_OUTCOMES=VALID")
    print("BASES=20/20")
    print("OUTCOMES=2190/2190")
    print("PRIMARY=1590/1590")
    print("CONTROLS=600/600")
    print("REPORTED_CORE_STATISTICS=EXACT_MATCH")
    print("MODEL_CALLS=0")


if __name__ == "__main__":
    main()
