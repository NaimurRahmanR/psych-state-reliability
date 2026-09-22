#!/usr/bin/env python3
"""Post-freeze robustness audit for the locked 20-base pilot.

This script performs analysis-only sensitivity checks on the frozen merged outcome
journal. It does not alter the prospective hypotheses, architectures, model outputs,
or authoritative frozen result files.

Checks:
1. Reproduce the primary paired base-cluster bootstrap effects.
2. Bootstrap seed stability across five fixed seeds (2,000 draws each).
3. Bootstrap repetition stability at 10,000 draws using the frozen seed.
4. Alternative context-family clustering sensitivity where pairing is complete.
5. Leave-one-base-out (LOBO) influence ranges for key point estimates.
6. Confirm the prespecified ALL_REFERENCE H3 sensitivity direction.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from psyr.analysis.report import metric_clusters
from psyr.analysis.statistics import paired_ratio_bootstrap
from psyr.evaluation.metrics import ratio

FROZEN_SEED = 77129
FROZEN_REPS = 2000
ROBUST_SEEDS = [77129, 1, 2026, 63713, 263901]
ROBUST_REPS = 10000


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def precision_clusters(rows, cluster="base_id"):
    out = defaultdict(lambda: [0, 0])
    for r in rows:
        out[r[cluster]][0] += r["state_correct"]
        out[r[cluster]][1] += r["state_asserted"]
    return dict(out)


def paired_effect(left, right, metric, cluster="base_id", reps=FROZEN_REPS, seed=FROZEN_SEED):
    if metric == "state_precision":
        a = precision_clusters(left, cluster)
        b = precision_clusters(right, cluster)
    else:
        a = metric_clusters(left, metric, cluster)
        b = metric_clusters(right, metric, cluster)
    if set(a) != set(b):
        return {"error": "incomplete paired clusters", "left_clusters": len(a), "right_clusters": len(b)}
    return paired_ratio_bootstrap(a, b, repetitions=reps, seed=seed)


def point_effect(left, right, metric, cluster="base_id"):
    if metric == "state_precision":
        a = precision_clusters(left, cluster)
        b = precision_clusters(right, cluster)
    else:
        a = metric_clusters(left, metric, cluster)
        b = metric_clusters(right, metric, cluster)
    if set(a) != set(b) or not a:
        return None
    ids = sorted(a)
    av = ratio(sum(a[i][0] for i in ids), sum(a[i][1] for i in ids))
    bv = ratio(sum(b[i][0] for i in ids), sum(b[i][1] for i in ids))
    if av is None or bv is None:
        return None
    return bv - av


def lobo(left, right, metric):
    ids = sorted({r["base_id"] for r in left} & {r["base_id"] for r in right})
    values = []
    for drop in ids:
        ll = [r for r in left if r["base_id"] != drop]
        rr = [r for r in right if r["base_id"] != drop]
        val = point_effect(ll, rr, metric, "base_id")
        values.append({"dropped_base": drop, "effect": val})
    numeric = [x["effect"] for x in values if x["effect"] is not None]
    return {
        "n_leave_one_out": len(values),
        "min_effect": min(numeric) if numeric else None,
        "max_effect": max(numeric) if numeric else None,
        "signs": {
            "negative": sum(v < 0 for v in numeric),
            "zero": sum(math.isclose(v, 0.0, abs_tol=1e-15) for v in numeric),
            "positive": sum(v > 0 for v in numeric),
        },
        "values": values,
    }


def seed_stability(left, right, metric):
    out = []
    for seed in ROBUST_SEEDS:
        e = paired_effect(left, right, metric, reps=FROZEN_REPS, seed=seed)
        out.append({"seed": seed, **e})
    return out


def main():
    rows = load_jsonl(ROOT / "results/processed/pilot20_final/outcomes_merged.jsonl")
    primary = [r for r in rows if not r["control"]]

    assert len(rows) == 2190
    assert len(primary) == 1590
    assert len({r["key"] for r in rows}) == 2190

    clean_a = [r for r in primary if r["condition"] == "clean" and r["architecture"] == "A"]
    clean_b = [r for r in primary if r["condition"] == "clean" and r["architecture"] == "B"]

    unsupported_fault = [r for r in rows if not r["control"] and r["condition"] == "unsupported_inference" and r["architecture"] == "B"]
    unsupported_control = [r for r in rows if r["control"] and r["condition"] == "unsupported_inference" and r["architecture"] == "B"]

    stale_fault = [r for r in rows if not r["control"] and r["condition"] == "stale_state" and r["architecture"] == "B"]
    stale_control = [r for r in rows if r["control"] and r["condition"] == "stale_state" and r["architecture"] == "B"]

    b_all = [r for r in primary if r["architecture"] == "B"]
    c_all = [r for r in primary if r["architecture"] == "C"]
    ref = [r for r in primary if r.get("design_status") == "clean"]
    b_ref = [r for r in ref if r["architecture"] == "B"]
    c_ref = [r for r in ref if r["architecture"] == "C"]

    contrasts = {
        "H1_clean_state_recall_B_minus_A": (clean_a, clean_b, "state_recall"),
        "H1_clean_state_precision_B_minus_A": (clean_a, clean_b, "state_precision"),
        "H2_unsupported_persistence_fault_minus_control": (unsupported_control, unsupported_fault, "persistence"),
        "H2_unsupported_decision_error_fault_minus_control": (unsupported_control, unsupported_fault, "decision_error_rate"),
        "H2_stale_persistence_fault_minus_control": (stale_control, stale_fault, "persistence"),
        "H3_ALL_SEPR_C_minus_B": (b_all, c_all, "sepr"),
        "H3_ALL_propagation_burden_C_minus_B": (b_all, c_all, "propagation_burden"),
        "H3_ALL_coverage_C_minus_B": (b_all, c_all, "coverage"),
        "H3_ALL_decision_reliable_coverage_C_minus_B": (b_all, c_all, "decision_reliable_coverage"),
    }

    report = {
        "status": "POST_FREEZE_ROBUSTNESS_AUDIT",
        "source": "results/processed/pilot20_final/outcomes_merged.jsonl",
        "model_calls": 0,
        "protocol_tuning": False,
        "frozen_bootstrap": {"cluster": "base_id", "repetitions": FROZEN_REPS, "seed": FROZEN_SEED},
        "checks": {},
        "prespecified_H3_ALL_REFERENCE": {
            "sepr": paired_effect(b_ref, c_ref, "sepr"),
            "propagation_burden": paired_effect(b_ref, c_ref, "propagation_burden"),
            "coverage": paired_effect(b_ref, c_ref, "coverage"),
            "decision_reliable_coverage": paired_effect(b_ref, c_ref, "decision_reliable_coverage"),
        },
        "limitations": [
            "Single model/revision; no cross-model replication.",
            "Synthetic non-clinical benchmark; no real-user validation.",
            "Only 20 selected base trajectories; context-family clustering has 10 clusters.",
            "Human audit has one author-rater and is descriptive only.",
            "Bootstrap checks assess sampling/influence stability of the frozen pilot, not external validity.",
        ],
    }

    for name, (left, right, metric) in contrasts.items():
        frozen = paired_effect(left, right, metric)
        context = paired_effect(left, right, metric, cluster="context_family")
        tenk = paired_effect(left, right, metric, reps=ROBUST_REPS, seed=FROZEN_SEED)
        seeds = seed_stability(left, right, metric)
        loo = lobo(left, right, metric)
        report["checks"][name] = {
            "metric": metric,
            "frozen_base_cluster_bootstrap": frozen,
            "context_family_cluster_bootstrap": context,
            "ten_thousand_draw_bootstrap": tenk,
            "seed_stability_2000_draws": seeds,
            "leave_one_base_out": loo,
        }

    out_dir = ROOT / "results/publication"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "robustness_audit.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Concise machine-readable summary for reviewers/readme.
    summary = {}
    for name, block in report["checks"].items():
        f = block["frozen_base_cluster_bootstrap"]
        t = block["ten_thousand_draw_bootstrap"]
        cf = block["context_family_cluster_bootstrap"]
        loo = block["leave_one_base_out"]
        summary[name] = {
            "point_effect": f.get("difference_b_minus_a"),
            "frozen_ci": [f.get("ci_low"), f.get("ci_high")],
            "10k_ci": [t.get("ci_low"), t.get("ci_high")],
            "context_family_effect": cf.get("difference_b_minus_a"),
            "context_family_ci": [cf.get("ci_low"), cf.get("ci_high")],
            "lobo_range": [loo.get("min_effect"), loo.get("max_effect")],
            "lobo_signs": loo.get("signs"),
        }
    (out_dir / "robustness_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("ROBUSTNESS_AUDIT=COMPLETE")
    print("MODEL_CALLS=0")
    print("FROZEN_BOOTSTRAP=2000_PAIRED_BASE_CLUSTER")
    print("SEED_STABILITY_SEEDS=5")
    print("BOOTSTRAP_10000_DRAW_SENSITIVITY=COMPLETE")
    print("CONTEXT_FAMILY_CLUSTER_SENSITIVITY=COMPLETE")
    print("LEAVE_ONE_BASE_OUT=COMPLETE")
    print(out_path)


if __name__ == "__main__":
    main()
