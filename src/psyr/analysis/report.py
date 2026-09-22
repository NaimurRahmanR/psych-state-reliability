import csv
from collections import defaultdict
from pathlib import Path
from psyr.common import Journal, read_json, write_json
from psyr.evaluation.metrics import ratio, sepr_counts, coverage_counts
from psyr.analysis.statistics import paired_ratio_bootstrap, exact_mcnemar

def summarize(rows):
    probes=[p for r in rows for p in r["probes"]]
    return {"turns":len(rows),"trajectories":len({r["base_id"] for r in rows}),
      "decision_errors":sum(r["decision_error"] for r in rows),
      "decision_error_rate":ratio(sum(r["decision_error"] for r in rows),len(rows)),
      "parse_or_api_failures":sum(bool(r["decision_parse_error"] or r["response_error"]) for r in rows),
      "extract_failures":sum(bool(r["extract_error"]) for r in rows),
      "state_error_exposures":sum(r["state_errors"] for r in rows),
      "state_error_exposures_per_turn":ratio(sum(r["state_errors"] for r in rows),len(rows)),
      "state_precision":ratio(sum(r["state_correct"] for r in rows),sum(r["state_asserted"] for r in rows)),
      "state_recall":ratio(sum(r["state_correct"] for r in rows),sum(r["state_required"] for r in rows)),
      "unsupported_assertions":sum(e["reason"]=="unsupported" for r in rows for e in r["state_error_items"]),
      "clarify_defer":sum(bool(r["decision"] and r["decision"]["action"]!="proceed") for r in rows),
      "judge_disagreements":sum(r["judge_disagreement"] is True for r in rows),
      "transition_appraisal_correct":sum(r.get("transition_appraisal_correct") is True for r in rows),
      "transition_appraisal_eligible":sum(r.get("transition_appraisal_correct") is not None for r in rows),
      "validation_mean":ratio(sum(r["validation"] for r in rows if r.get("validation") is not None),sum(r.get("validation") is not None for r in rows)),
      "reappraisal_mean":ratio(sum(r["reappraisal"] for r in rows if r.get("reappraisal") is not None),sum(r.get("reappraisal") is not None for r in rows)),
      "endorsement_judged":sum(r.get("endorsement") is True for r in rows),
      "stale_target_judged":sum(r.get("stale_target") is True for r in rows),
      "fidelity_valid":sum(r.get("fidelity_failure") is not None for r in rows),
      **coverage_counts(rows),**sepr_counts(probes)}

def metric_clusters(rows, metric, cluster="base_id"):
    acc=defaultdict(lambda:[0,0])
    for r in rows:
        p=acc[r[cluster]]
        if metric == "sepr":
            p[0]+=sum(x["attribution"]=="propagated" for x in r["probes"]); p[1]+=len(r["probes"])
        elif metric == "coverage":
            p[0]+=r["proceeded"]; p[1]+=1
        elif metric == "decision_reliable_coverage":
            p[0]+=r["proceeded"] and not r["decision_error"]; p[1]+=1
        elif metric == "reliable_coverage":
            p[0]+=r["proceeded"] and not r["decision_error"] and r["fidelity_failure"] is False; p[1]+=1
        elif metric == "state_recall":
            p[0]+=r["state_correct"]; p[1]+=r["state_required"]
        elif metric == "propagation_burden":
            p[0]+=any(x["attribution"]=="propagated" for x in r["probes"]); p[1]+=1
        elif metric == "persistence":
            p[0]+=r.get("fault_appraisal_persists") is True; p[1]+=r.get("fault_appraisal_persists") is not None
        elif metric == "decision_error_rate":
            p[0]+=r["decision_error"]; p[1]+=1
        else:
            raise ValueError(metric)
    return dict(acc)

def metrics_for(cfg):
    from psyr.evaluation.evaluator_policy import semantic_available
    base=["sepr","coverage","decision_reliable_coverage","state_recall","decision_error_rate","propagation_burden"]
    return base+(["reliable_coverage"] if semantic_available(cfg) else [])

def mask_semantic(summary,cfg):
    from psyr.evaluation.evaluator_policy import semantic_available, SEMANTIC_FIELDS
    if not semantic_available(cfg):
        for k in SEMANTIC_FIELDS:
            if k in summary: summary[k]=None
    return summary

def analyze(run_dir,out_dir,allow_fixture=False):
    run_dir=Path(run_dir); out_dir=Path(out_dir)
    manifest=read_json(run_dir/"run_manifest.json")
    if manifest["fixture"] and not allow_fixture:
        raise RuntimeError("Fixture records are not research results")
    rows=[r for r in Journal(run_dir/"outcomes.jsonl").records if r["kind"]=="turn_outcome"]
    if not rows:
        raise RuntimeError("No executed model outcomes; no results to analyze")
    grouped=defaultdict(list)
    for r in rows:
        grouped[(r["condition"],r["architecture"],r["control"])].append(r)
        grouped[("ALL",r["architecture"],r["control"])].append(r)
        if r.get("design_status")=="clean":
            # Prespecified sensitivity aggregate: reference-mode cells only.
            grouped[("ALL_REFERENCE",r["architecture"],r["control"])].append(r)
    table=[]
    cfg=manifest["config"]
    for (condition,arch,control),rs in sorted(grouped.items()):
        s=mask_semantic(summarize(rs),cfg)
        if arch == "A":
            s.update(sepr=None,sepr_upper_bound=None,error_exposures=None,propagated=None,ambiguous=None)
        table.append(dict(condition=condition,architecture=arch,control=control,**s))
    comparisons=[]
    cfg=manifest["config"]
    for condition in sorted({r["condition"] for r in rows}|{"ALL","ALL_REFERENCE"}):
        for left,right in (("B","C"),("A","B")):
            aa=grouped.get((condition,left,False),[]); bb=grouped.get((condition,right,False),[])
            if not aa or not bb:
                continue
            for metric in metrics_for(cfg):
                if left=="A" and metric in ("sepr","propagation_burden"):
                    continue
                for cluster in ("base_id","context_family"):
                    ca=metric_clusters(aa,metric,cluster); cb=metric_clusters(bb,metric,cluster)
                    if set(ca)!=set(cb):
                        comparisons.append(dict(condition=condition,comparison=f"{right}-{left}",metric=metric,error="incomplete paired clusters"))
                        continue
                    comparisons.append(dict(condition=condition,comparison=f"{right}-{left}",metric=metric,cluster=cluster,
                        **paired_ratio_bootstrap(ca,cb,cfg["bootstrap_repetitions"],cfg["bootstrap_seed"])))
    control_comparisons=[]
    persistence=[]
    for condition in ("unsupported_inference","stale_state"):
        for arch in ("A","B","C"):
            fault=grouped.get((condition,arch,False),[]); control=grouped.get((condition,arch,True),[])
            if not fault or not control: continue
            for metric in ("persistence","decision_error_rate","coverage"):
                ca=metric_clusters(control,metric); cb=metric_clusters(fault,metric)
                if set(ca)==set(cb):
                    control_comparisons.append(dict(condition=condition,architecture=arch,metric=metric,comparison="fault-minus-matched-control",
                        **paired_ratio_bootstrap(ca,cb,cfg["bootstrap_repetitions"],cfg["bootstrap_seed"])))
            for t in (3,4,5):
                rs=[r for r in fault if r["turn"]==t]
                persistence.append(dict(condition=condition,architecture=arch,lag=t-3,errors=sum(r.get("fault_appraisal_persists") is True for r in rs),eligible=len(rs)))
    # Only independent base-level any-error outcomes are used for the optional paired test.
    mcnemar=[]
    for condition in sorted({r["condition"] for r in rows}):
        aa=grouped.get((condition,"B",False),[]); bb=grouped.get((condition,"C",False),[])
        ag=defaultdict(list); bg=defaultdict(list)
        for r in aa: ag[r["base_id"]].append(r)
        for r in bb: bg[r["base_id"]].append(r)
        ids=sorted(set(ag)&set(bg))
        if ids and all(len(ag[i])==5 and len(bg[i])==5 for i in ids):
            mcnemar.append(dict(condition=condition,**exact_mcnemar([any(r["decision_error"] for r in ag[i]) for i in ids],[any(r["decision_error"] for r in bg[i]) for i in ids])))
    # V2: perturbation modes with distinct estimands are compared within mode only.
    strata=defaultdict(list)
    for r in rows:
        if r.get("perturbation_mode") is not None and not r["control"]:
            strata[(r["condition"],r["perturbation_mode"],r["architecture"])].append(r)
    stratified_counts=[dict(condition=c,perturbation_mode=m,architecture=a,**mask_semantic(summarize(rs),cfg))
                       for (c,m,a),rs in sorted(strata.items())]
    stratified_comparisons=[]
    for (c,m) in sorted({(c,m) for c,m,_ in strata}):
        for left,right in (("B","C"),("A","B")):
            aa=strata.get((c,m,left),[]); bb=strata.get((c,m,right),[])
            if not aa or not bb: continue
            for metric in metrics_for(cfg):
                if left=="A" and metric in ("sepr","propagation_burden"): continue
                ca=metric_clusters(aa,metric); cb=metric_clusters(bb,metric)
                if set(ca)!=set(cb):
                    stratified_comparisons.append(dict(condition=c,perturbation_mode=m,comparison=f"{right}-{left}",metric=metric,error="incomplete paired clusters")); continue
                stratified_comparisons.append(dict(condition=c,perturbation_mode=m,comparison=f"{right}-{left}",metric=metric,cluster="base_id",
                    **paired_ratio_bootstrap(ca,cb,cfg["bootstrap_repetitions"],cfg["bootstrap_seed"])))
    primary=[r for r in rows if not r["control"]]
    from psyr.benchmark.dataset import planned_variants
    expected=planned_variants(manifest["split"],manifest.get("limit"))*(1 if manifest["ablations"] else 3)*5
    report={"split":manifest["split"],"fixture":manifest["fixture"],"complete_primary":len(primary)==expected,
            "completed_primary_turns":len(primary),"expected_primary_turns":expected,
            "counts":table,"paired_comparisons":comparisons,"control_comparisons":control_comparisons,"persistence_by_lag":persistence,"exploratory_mcnemar":mcnemar,
            "stratified_counts":stratified_counts,"stratified_comparisons":stratified_comparisons,
            "manual_audit":"NOT_EXECUTED_UNLESS_SEPARATELY_RECORDED",
            "evaluator_mode":cfg.get("evaluator_mode"),
            "semantic_fidelity":"AUTOMATED_GATE_PASSED_NOT_HUMAN_VALIDATED" if cfg.get("evaluator_mode")=="validated_automated" else "UNAVAILABLE_NOT_VALIDATED"}
    out_dir.mkdir(parents=True,exist_ok=True)
    write_json(out_dir/"analysis.json",report)
    for name,items in (("summary.csv",table),("paired_effects.csv",comparisons)):
        if items:
            keys=sorted(set().union(*(x.keys() for x in items)))
            with (out_dir/name).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(items)
    return report

def figures(analysis_path,out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    report=read_json(analysis_path)
    if report["fixture"]:
        raise RuntimeError("No research figure from fixture outputs")
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    rows=[r for r in report["counts"] if r["condition"]=="ALL" and not r["control"]]
    fig,axes=plt.subplots(1,2,figsize=(9,4),layout="constrained")
    for r in rows:
        if r["architecture"]!="A" and r["sepr"] is not None:
            axes[0].scatter(r["coverage"],r["sepr"],label=r["architecture"])
        axes[1].bar(r["architecture"],r["decision_error_rate"])
    axes[0].set(xlabel="Coverage",ylabel="SEPR lower bound",xlim=(0,1),ylim=(0,1))
    axes[1].set(ylabel="Decision error rate",ylim=(0,1))
    if axes[0].collections: axes[0].legend()
    fig.suptitle(f"Synthetic {report['split']} — {'complete' if report['complete_primary'] else 'INCOMPLETE'}")
    fig.savefig(out_dir/"reliability_coverage.png",dpi=180)
    fig.savefig(out_dir/"reliability_coverage.pdf")
    plt.close(fig)

def compare_ablation(primary_dir,ablation_dir,out_dir):
    primary_dir=Path(primary_dir); ablation_dir=Path(ablation_dir)
    pm=read_json(primary_dir/"run_manifest.json"); am=read_json(ablation_dir/"run_manifest.json")
    if pm["fixture"] or am["fixture"] or pm["ablations"] or len(am["ablations"])!=1:
        raise RuntimeError("Real primary and one-mechanism ablation runs required")
    for k in ("config_hash","source_digest","split"):
        if pm[k]!=am[k]: raise RuntimeError("Incomparable experiment versions")
    left=[r for r in Journal(primary_dir/"outcomes.jsonl").records if r.get("architecture")=="C" and not r.get("control")]
    right=[r for r in Journal(ablation_dir/"outcomes.jsonl").records if r.get("architecture")=="C" and not r.get("control")]
    key=lambda r:(r["base_id"],r["condition"],r["turn"])
    if set(map(key,left))!=set(map(key,right)): raise RuntimeError("Incomplete matched ablation cells")
    table=[]; cfg=pm["config"]
    for condition in sorted({r["condition"] for r in left}|{"ALL"}):
        aa=[r for r in left if condition=="ALL" or r["condition"]==condition]
        bb=[r for r in right if condition=="ALL" or r["condition"]==condition]
        for metric in [m for m in metrics_for(cfg) if m!="state_recall"]:
            table.append(dict(condition=condition,metric=metric,comparison="ablation-minus-full-C",
                **paired_ratio_bootstrap(metric_clusters(aa,metric),metric_clusters(bb,metric),cfg["bootstrap_repetitions"],cfg["bootstrap_seed"])))
    result={"disabled":am["ablations"],"matched_turns":len(left),"contrasts":table}
    write_json(Path(out_dir)/"ablation_comparison.json",result)
    return result
