#!/usr/bin/env python3
"""Repository-local command runner; no installation required."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from psyr.common import ROOT, read_json, write_json, digest
from psyr.benchmark.dataset import (build_split, latent_trajectory, evidence, CONDITIONS,
                                    applicable_conditions, COUNTS as SPLIT_COUNTS)
from psyr.degradations.conditions import apply_condition
from psyr.freeze import design_lock, finalize, verify_final_freeze, source_manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["doctor","dataset","calibration-checks","run","freeze","design-lock","analyze","compare-ablation","figures","audit-packet","audit-analyze","judge-traps","diversity-audit"])
    p.add_argument("--config",default=str(ROOT/"configs/experiment.json"))
    p.add_argument("--split",choices=["calibration","heldout"],default="calibration")
    p.add_argument("--run-dir",type=Path)
    p.add_argument("--out-dir",type=Path)
    p.add_argument("--limit",type=int)
    p.add_argument("--disable",choices=["provenance","temporal","epistemic","contradiction","defer"],action="append",default=[])
    p.add_argument("--reuse-extractions",type=Path)
    p.add_argument("--comparison-dir",type=Path)
    p.add_argument("--trap-dir",type=Path,help="freeze in validated_automated mode: calibration judge-traps run directory")
    p.add_argument("--no-judge",action="store_true",help="calibration only: run generation before an evaluator is selected")
    a=p.parse_args(); config=read_json(a.config)
    if a.command=="doctor":
        packages={}
        for name in ("numpy","scipy","matplotlib"):
            try: packages[name]=importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: packages[name]=None
        result={"python":sys.version,"platform":platform.platform(),"packages":packages,
          "model_configured":bool(config["model"] and config["model_revision"]),
          "judge_configured":bool(config["judge_model"] and config["judge_revision"]),
          "endpoint_present":bool(os.getenv(config["endpoint_env"])),"key_present":bool(os.getenv(config["api_key_env"])),
          "status":"INFERENCE_NOT_EXECUTED"}
        write_json(ROOT/"docs/environment.json",result)
    elif a.command=="dataset":
        if a.split=="heldout": verify_final_freeze(ROOT,config)
        result=build_split(a.split,ROOT/f"data/{a.split}/latent.jsonl",allow_heldout=a.split=="heldout",
                           manifest_path=ROOT/f"data/{a.split}/manifest.jsonl")
        if a.split=="calibration":
            from psyr.common import write_jsonl
            from psyr.benchmark.dataset import rendered_examples
            write_jsonl(ROOT/"data/calibration/examples.jsonl",rendered_examples("calibration"),exclusive=True)
    elif a.command=="calibration-checks":
        count=0; hashes=[]
        for i in range(SPLIT_COUNTS["calibration"]):
            latent=latent_trajectory("calibration",i)
            for condition in applicable_conditions(latent):
                case=apply_condition(latent,condition)
                assert len(case["turns"])==len(case["gold"])==5
                for t in range(1,6):
                    ev=evidence(case,t)
                    assert max(x["turn"] for x in ev)==t
                    assert not any("gold" in x or "condition" in x for x in ev)
                count+=1; hashes.append(digest(case))
        result={"status":"ENGINEERING_CHECKS_ONLY","calibration_base_trajectories":SPLIT_COUNTS["calibration"],"condition_variants":count,
                "interaction_points":count*5,"llm_calls":0,"heldout_generated":0,"variant_hash":digest(hashes)}
        write_json(ROOT/"results/processed/calibration_integrity.json",result)
    elif a.command=="diversity-audit":
        from psyr.benchmark.diversity import audit
        result=audit("calibration")
        write_json(ROOT/"results/processed/benchmark_diversity.json",result)
    elif a.command=="design-lock": result=design_lock(ROOT)
    elif a.command=="freeze":
        if not a.run_dir: p.error("--run-dir required")
        result=finalize(ROOT,config,a.run_dir,a.trap_dir)
    elif a.command in ("run","judge-traps"):
        if not a.run_dir: p.error("--run-dir required")
        if a.split=="heldout": verify_final_freeze(ROOT,config)
        if a.disable and not a.reuse_extractions: p.error("Ablations require --reuse-extractions pointing to the primary raw journal")
        from psyr.backend import Backend
        from psyr.common import Journal
        if a.reuse_extractions:
            prior=read_json(a.reuse_extractions.parent/"run_manifest.json")
            if prior["split"]!=a.split or prior["config_hash"]!=digest(config) or prior["source_digest"]!=digest(source_manifest(ROOT)) or prior["ablations"] or prior["fixture"]:
                raise RuntimeError("Ablation extraction source must be the same frozen primary experiment")
            source=Journal(a.reuse_extractions)
            from psyr.benchmark.dataset import planned_variants
            extraction_ids={r.get("call_id") for r in source.records if "/shared/extract/" in r.get("call_id","")}
            if len(extraction_ids)!=planned_variants(a.split)*5:
                raise RuntimeError("Ablation requires all primary shared extractions")
            target=Journal(a.run_dir/"generation.jsonl")
            have={r.get("call_id") for r in target.records}
            for row in source.records:
                if "/shared/extract/" in row.get("call_id","") and row["call_id"] not in have:
                    target.append({k:v for k,v in row.items() if k not in ("seq","previous_hash","record_hash")})
        if config.get("evaluator_mode")=="manual_audit_only":
            # No automated semantic labels in this mode; the judge is never constructed.
            if a.command=="judge-traps":
                p.error("judge-traps is unavailable in manual_audit_only mode")
            judge=None
        elif a.no_judge:
            # A judgeless run cannot satisfy the freeze gate (three valid judgments per
            # primary response), so it can never become the frozen calibration run.
            if a.split!="calibration" or a.command!="run":
                p.error("--no-judge is allowed only for calibration runs")
            judge=None
        else:
            judge=Backend(config,a.run_dir/"judge.jsonl",judge=True)
        if a.command=="judge-traps":
            from psyr.evaluation.audit import run_traps
            result=run_traps(a.split,judge,config,a.out_dir or a.run_dir)
        else:
            from psyr.runner import run_experiment
            backend=Backend(config,a.run_dir/"generation.jsonl")
            result=run_experiment(ROOT,a.split,backend,judge,config,a.limit,tuple(a.disable))
    elif a.command=="analyze":
        if not a.run_dir or not a.out_dir: p.error("--run-dir and --out-dir required")
        from psyr.analysis.report import analyze
        result=analyze(a.run_dir,a.out_dir)
    elif a.command=="compare-ablation":
        if not a.run_dir or not a.comparison_dir or not a.out_dir: p.error("--run-dir, --comparison-dir and --out-dir required")
        from psyr.analysis.report import compare_ablation
        result=compare_ablation(a.run_dir,a.comparison_dir,a.out_dir)
    elif a.command=="figures":
        if not a.run_dir or not a.out_dir: p.error("--run-dir (analysis folder) and --out-dir required")
        from psyr.analysis.report import figures
        figures(a.run_dir/"analysis.json",a.out_dir); result={"figures":"created"}
    elif a.command=="audit-packet":
        if not a.run_dir or not a.out_dir: p.error("--run-dir and --out-dir required")
        from psyr.evaluation.audit import make_packet
        result=make_packet(a.run_dir,a.out_dir,config["audit_seed"],config["audit_trajectories"])
    else:
        if not a.run_dir: p.error("--run-dir (audit packet directory) required")
        from psyr.evaluation.audit import analyze_human
        result=analyze_human(a.run_dir)
    if isinstance(result,dict) and "files" in result:
        result={k:v for k,v in result.items() if k!="files"}|{"tracked_files":len(result["files"])}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    try: main()
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        print(json.dumps({"status":"BLOCKED","reason":str(error)}),file=sys.stderr)
        sys.exit(2)
