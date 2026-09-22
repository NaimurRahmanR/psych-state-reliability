#!/usr/bin/env python3
"""Pre-packaging verification: documentation vs code, integrity sweeps. Exit 1 on any failure."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from psyr.benchmark.dataset import ARCHETYPE_IDS, CONDITIONS, classify_condition, planned_variants
from psyr.benchmark.diversity import audit
fails, notes = [], []
def check(ok, msg):
    (notes if ok else fails).append(("PASS " if ok else "FAIL ") + msg)

t = json.loads((ROOT / "docs/test_summary.json").read_text())
check(t["successful"] and not t["failures"] and not t["errors"] and not t["skipped"], f"test summary {t['tests_run']} passed")
for doc in ("Research_Execution_Status.md", "docs/V2_CHANGELOG.md"):
    check(f"{t['tests_run']}" in (ROOT / doc).read_text(), f"{doc} states test count {t['tests_run']}")

check([p.name for p in (ROOT / "data/heldout").iterdir()] == ["README.md"], "no held-out data materialised")
check(not (ROOT / "protocol/freeze_manifest.json").exists(), "no final freeze manifest")
raw = [p for p in (ROOT / "results").rglob("*") if p.is_file() and p.name in ("generation.jsonl", "judge.jsonl", "outcomes.jsonl", "trap_judgments.jsonl")]
check(not raw, "no model/judge journals (real calls = 0)")
cfg = json.loads((ROOT / "configs/experiment.json").read_text())
check(cfg["model"] == "Qwen/Qwen3-8B" and cfg["model_revision"] is None and cfg["judge_revision"] is None, "no invented model/judge revision")
check(cfg["generation"]["chat_template_kwargs"]["enable_thinking"] is False, "non-thinking configured")
check(cfg["evaluator_mode"] is None, "evaluator mode undecided (no silent default)")
from psyr.evaluation.evaluator_policy import EVALUATOR_MODES
for doc in ("protocol/protocol_v2_amendment.md", "protocol/FREEZE.md", "docs/gpu_execution_plan.md", "Research_Execution_Status.md", "README.md"):
    txt = (ROOT / doc).read_text()
    check(all(m in txt for m in EVALUATOR_MODES), f"{doc} documents both evaluator modes")
g = cfg["evaluator_validation_gate"]; am = (ROOT / "protocol/protocol_v2_amendment.md").read_text()
check(f"≥ {g['min_detected_per_failure_kind']} of 8" in am and f"≥ {g['min_correct_per_negative_control_kind']} of 8" in am
      and f"≤ {int(g['max_trap_invalid_fraction']*100)}%" in am and f"≤ {int(g['max_trap_sample_disagreement_fraction']*100)}%" in am
      and f"≥ {int(g['min_calibration_responses_with_3_valid_samples']*100)}%" in am, "protocol gate thresholds match config")
lock = json.loads((ROOT / "protocol/design_lock.json").read_text())
check(lock["status"] == "PRE-EMPIRICAL DESIGN LOCK — NOT FINAL EXPERIMENT FREEZE", "design lock labelled pre-empirical, not a freeze")

# Protocol amendment grid must match the implemented classification.
amend = (ROOT / "protocol/protocol_v2_amendment.md").read_text()
short = {"clean": "clean", "stratified": "stratified", "non_applicable": "**non_applicable**", "confounded": "**confounded**"}
for a in ARCHETYPE_IDS:
    row = next(l for l in amend.splitlines() if l.startswith(f"| {a} |"))
    cells = [c.strip() for c in row.strip("|").split("|")][1:]
    for cell, cond in zip(cells, ("missing_evidence", "contradictory_evidence", "superseded_appraisal", "unsupported_inference", "stale_state")):
        d = classify_condition(a, cond)
        ok = cell.startswith(short[d["status"]]) and (d["mode"] is None or d["status"] not in ("clean", "stratified")
              or d["mode"].split("_")[0] in cell.replace("(", "").replace(")", "") or cond in ("missing_evidence", "stale_state"))
        check(ok, f"amendment grid {a} x {cond}: '{cell}' vs {d['status']}:{d['mode']}")
check(planned_variants("heldout") == 550 and planned_variants("calibration") == 110, "planned variants 550/110")
for doc in ("protocol/protocol_v2_amendment.md", "README.md", "Research_Execution_Status.md", "docs/gpu_execution_plan.md"):
    txt = (ROOT / doc).read_text()
    check(all(n in txt for n in ("1,650",)), f"{doc} states 1,650 planned trajectories")

# Diversity numbers quoted in the audit must equal the recomputed outputs.
a = audit(); cmp_ = json.loads((ROOT / "results/processed/diversity_v1_vs_v2.json").read_text())
check(json.loads((ROOT / "results/processed/benchmark_diversity.json").read_text()) == json.loads(json.dumps(a)), "committed diversity audit reproducible")
aud = (ROOT / "docs/benchmark_diversity_audit.md").read_text()
v2s, v2l = cmp_["v2"]["structural"], cmp_["v2"]["lexical"]
for label, val in (("shared-template", v2s["shared_template_char_fraction"]), ("cross-family", v2s["cross_family_reused_char_fraction"]),
                   ("max Jaccard", v2l["max_pairwise_jaccard"]), ("TTR", v2l["type_token_ratio"]), ("mean Jaccard", v2l["mean_pairwise_jaccard"])):
    check(f"{val:.3f}" in aud or f"{val*100:.1f}%" in aud, f"audit quotes {label} = {val}")
check(str(v2l["distinct_content_tokens"]) in aud and str(cmp_["v1"]["lexical"]["distinct_content_tokens"]) in aud, "audit quotes distinct tokens")

# Sweeps over text files.
text_files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in (".py", ".md", ".json", ".jsonl", ".txt", ".toml")
              and "evidence" not in p.parts and "__pycache__" not in p.parts]
secret = re.compile(r"(sk-[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,})")
check(not [p for p in text_files if secret.search(p.read_text(errors="ignore"))], "no credential-like strings")
todo = re.compile(r"\b(TODO|FIXME|XXX|TBD)\b")
todos = [str(p.relative_to(ROOT)) for p in text_files if todo.search(p.read_text(errors="ignore")) and p.name != "verify_package.py"]
check(not todos, f"no TODO/FIXME/XXX/TBD markers {todos}")
clinical = re.compile(r"(clinically (effective|validated)|improves? (mental health|wellbeing)|reduces? symptoms|treats? (depression|anxiety)|therapeutic(ally)? effective|patient benefit)", re.I)
hits = []
for p in text_files:
    if p.name == "verify_package.py":
        continue
    for line in p.read_text(errors="ignore").splitlines():
        if clinical.search(line) and not re.search(r"\b(no|not|never|nor|without|does not|do not|cannot|neither)\b", line, re.I):
            hits.append(f"{p.relative_to(ROOT)}: {line.strip()[:100]}")
check(not hits, f"no unnegated clinical-benefit claims {hits}")
empirical = re.compile(r"\bSEPR\s*(=|was|of)\s*0?\.\d", re.I)
check(not [p for p in text_files if empirical.search(p.read_text(errors="ignore"))], "no numeric SEPR result claimed")
check(not [p for p in text_files if re.search(r"FAMILY_KEYS|family_pool|CALIBRATION_FAMILIES", p.read_text(errors="ignore"))
           and p.name not in ("provenance.md", "V2_CHANGELOG.md", "verify_package.py")], "no unknown-provenance identifiers in source")

print("\n".join(notes + fails)); print(f"\n{len(notes)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
