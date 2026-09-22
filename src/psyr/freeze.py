from __future__ import annotations
import datetime
import hashlib
from pathlib import Path
from psyr.common import digest, read_json, write_json, Journal

def source_manifest(root):
    root=Path(root)
    paths=[]
    for directory in ("src","configs","protocol","tests","scripts","data/calibration"):
        # Build metadata (*.egg-info, build/) is created by `pip install -e .` and is not source.
        paths.extend(p for p in (root/directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc"
                     and not any(part.endswith(".egg-info") or part=="build" for part in p.parts)
                     and p.name not in ("freeze_manifest.json","design_lock.json","FREEZE.md"))
    paths.extend(root/name for name in ("pyproject.toml","requirements.txt","requirements-analysis.txt",".python-version") if (root/name).exists())
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def design_lock(root):
    root=Path(root)
    record={"status":"PRE-EMPIRICAL DESIGN LOCK — NOT FINAL EXPERIMENT FREEZE","created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "files":source_manifest(root),"heldout_inference":"NOT_EXECUTED",
            "design_version":"design-v2.1",
            "blockers":["independent review and approval of benchmark V2",
                        "GPU environment with Qwen/Qwen3-8B weights; exact revision to be pinned",
                        "verified non-thinking mode","real 20-trajectory calibration",
                        "evaluator mode decision (validated_automated with a gate-passing pinned evaluator, or manual_audit_only)","final scientific freeze",
                        "independent human audit"]}
    write_json(root/"protocol/design_lock.json",record,exclusive=True)
    return record

def expected_calibration_cells():
    """Planned calibration cells under the V2 condition design (not a fixed 6-condition grid)."""
    from psyr.benchmark.dataset import COUNTS, latent_trajectory, applicable_conditions
    primary,controls=set(),set()
    for i in range(COUNTS["calibration"]):
        latent=latent_trajectory("calibration",i)
        for c in applicable_conditions(latent):
            for a in ("A","B","C"):
                for t in range(1,6):
                    primary.add((latent["id"],c,a,t))
                    if c in ("unsupported_inference","stale_state"):
                        controls.add((latent["id"],c,a,t))
    return primary,controls

def finalize(root,config,calibration_run,trap_dir=None):
    root=Path(root); run=Path(calibration_run)
    if any(config.get(k) in (None,"") for k in ("model","model_revision")):
        raise RuntimeError("Cannot freeze unspecified model identifiers/revisions")
    from psyr.evaluation.evaluator_policy import check_mode_configuration, evaluate_validation_gate
    mode=check_mode_configuration(config)
    manifest=read_json(run/"run_manifest.json")
    if manifest["fixture"] or manifest["split"]!="calibration" or manifest["limit"] not in (None,20) or manifest["ablations"]:
        raise RuntimeError("Full real-model calibration required")
    if manifest["config_hash"]!=digest(config) or manifest["source_digest"]!=digest(source_manifest(root)):
        raise RuntimeError("Code/config changed since calibration; recalibrate before freeze")
    outcomes=[r for r in Journal(run/"outcomes.jsonl").records if r["kind"]=="turn_outcome"]
    primary=[r for r in outcomes if not r["control"]]
    expected,expected_controls=expected_calibration_cells()
    if len(primary)!=len(expected) or len({r["key"] for r in primary})!=len(expected):
        raise RuntimeError("Calibration primary matrix incomplete")
    actual={(r["base_id"],r["condition"],r["architecture"],r["turn"]) for r in primary}
    if actual!=expected:
        raise RuntimeError("Calibration matrix cell identities do not match the planned V2 design")
    controls={(r["base_id"],r["condition"],r["architecture"],r["turn"]) for r in outcomes if r["control"]}
    if controls!=expected_controls:
        raise RuntimeError("Calibration matched-control cells do not match the planned V2 design")
    failures=sum(bool(r["decision_parse_error"] or r["response_error"] or r["extract_error"]) for r in primary)/len(primary)
    if failures>config["calibration_parser_failure_limit"]:
        raise RuntimeError("Calibration parser/API failure gate failed")
    if mode=="validated_automated":
        gate=evaluate_validation_gate(trap_dir,primary,config)
        if not gate["passed"]:
            raise RuntimeError("Evaluator validation gate failed; select another pre-registered candidate or use manual_audit_only: "
                               +"; ".join(c["criterion"] for c in gate["criteria"] if not c["passed"]))
        evaluator={"mode":mode,"judge_model":config["judge_model"],"judge_revision":config["judge_revision"],
                   "judge_generation":config["judge_generation"],"aggregation":config["judge_aggregation"],
                   "validation_gate":config["evaluator_validation_gate"],"validation_report":gate,
                   "semantic_fidelity":"AUTOMATED_GATE_PASSED_NOT_HUMAN_VALIDATED"}
    else:
        evaluator={"mode":mode,"semantic_fidelity":"UNAVAILABLE_NOT_VALIDATED",
                   "unvalidated_judgments_in_calibration":sum(r.get("judge_valid",0)>0 for r in primary),
                   "manual_audit":{"packet_command":"python scripts/psyr.py audit-packet","seed":config["audit_seed"],
                                   "trajectories":config["audit_trajectories"],"ratings":"real human raters only"}}
    record={"status":"FINAL_FROZEN","created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "config_hash":digest(config),"files":source_manifest(root),"calibration_chain":Journal(run/"outcomes.jsonl").previous,
            "calibration_parser_failure_rate":failures,"hypotheses":"protocol/protocol_v1.md",
            "design":"protocol/protocol_v2_amendment.md","model":config["model"],"model_revision":config["model_revision"],
            "judge_model":config["judge_model"],"judge_revision":config["judge_revision"],
            "generation":config["generation"],"evaluator":evaluator,
            "analysis":"protocol/evaluation_spec.md"}
    write_json(root/"protocol/freeze_manifest.json",record,exclusive=True)
    return record

def verify_final_freeze(root,config):
    root=Path(root)
    path=root/"protocol/freeze_manifest.json"
    if not path.exists():
        raise RuntimeError("Held-out access blocked: final model-calibrated experiment freeze is absent")
    lock=read_json(path)
    if lock["status"]!="FINAL_FROZEN" or lock["config_hash"]!=digest(config) or lock["files"]!=source_manifest(root):
        raise RuntimeError("Frozen files/config changed; record an amendment and a new experiment version")
    return lock
