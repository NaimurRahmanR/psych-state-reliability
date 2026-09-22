#!/usr/bin/env python3
"""Create manuscript figures from the frozen pilot-20 results."""
from pathlib import Path
import csv, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import numpy as np

analysis = json.loads((ROOT / "results/processed/pilot20_final/pilot20_analysis.json").read_text())
rows = list(csv.DictReader((ROOT / "results/processed/pilot20_final/condition_architecture_metrics.csv").open()))

# Primary effects from the authoritative frozen analysis.
h3 = analysis["H3"]["ALL"]
keys = ["sepr", "propagation_burden", "coverage", "decision_reliable_coverage"]
labels = ["SEPR", "Propagation burden", "Coverage", "Decision-reliable coverage"]
eff = np.array([h3[k]["difference_b_minus_a"] for k in keys])
lo = np.array([h3[k]["ci_low"] for k in keys])
hi = np.array([h3[k]["ci_high"] for k in keys])
y = np.arange(len(labels))[::-1]
fig, ax = plt.subplots(figsize=(6.6, 3.8))
ax.errorbar(eff, y, xerr=[eff-lo, hi-eff], fmt="o", capsize=4)
ax.axvline(0, linewidth=1)
ax.set_yticks(y, labels)
ax.set_xlabel("C - B difference")
ax.set_title("Primary paired effects (95% bootstrap CI)")
ax.grid(axis="x", alpha=.25)
fig.tight_layout()
fig.savefig(OUT / "primary_effects.pdf")
fig.savefig(OUT / "primary_effects.png", dpi=220)
plt.close(fig)

conditions = ["clean", "missing_evidence", "contradictory_evidence", "superseded_appraisal", "unsupported_inference", "stale_state"]
short = ["Clean", "Missing", "Contradictory", "Superseded", "Unsupported", "Stale"]
lookup = {(r["condition"], r["architecture"]): r for r in rows}
x = np.arange(len(conditions)); w = .36

for metric, ylabel, filename in [
    ("coverage", "Coverage", "coverage_by_condition"),
    ("sepr", "SEPR", "sepr_by_condition"),
]:
    b = [float(lookup[(c,"B")][metric]) for c in conditions]
    cvals = [float(lookup[(c,"C")][metric]) for c in conditions]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    if metric == "coverage":
        ax.bar(x-w/2, b, w, label="B structured")
        ax.bar(x+w/2, cvals, w, label="C reliability-aware")
    else:
        ax.plot(x, b, marker="o", label="B structured")
        ax.plot(x, cvals, marker="s", label="C reliability-aware")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x, short, rotation=25, ha="right")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    fig.savefig(OUT / f"{filename}.pdf")
    fig.savefig(OUT / f"{filename}.png", dpi=220)
    plt.close(fig)

# Overall architecture coverage and SEPR are useful compact sanity figures.
arches=["A","B","C"]
coverage=[analysis["overall"][a]["coverage"] for a in arches]
fig,ax=plt.subplots(figsize=(5.2,3.6))
ax.bar(arches,coverage)
ax.set_ylim(0,1.05); ax.set_ylabel("Coverage"); ax.set_xlabel("Architecture")
ax.set_title("Overall decision coverage")
ax.grid(axis="y",alpha=.25)
fig.tight_layout(); fig.savefig(OUT/'overall_coverage.pdf'); fig.savefig(OUT/'overall_coverage.png',dpi=220); plt.close(fig)

sepr=[analysis["overall"][a]["sepr"] for a in ["B","C"]]
fig,ax=plt.subplots(figsize=(5.2,3.6))
ax.bar(["B","C"],sepr)
ax.set_ylim(0,1.05); ax.set_ylabel("SEPR"); ax.set_xlabel("Architecture")
ax.set_title("Conditional state-error propagation")
ax.grid(axis="y",alpha=.25)
fig.tight_layout(); fig.savefig(OUT/'overall_sepr.pdf'); fig.savefig(OUT/'overall_sepr.png',dpi=220); plt.close(fig)

print("FIGURES=COMPLETE")
print("SOURCE=FROZEN_ANALYSIS")
