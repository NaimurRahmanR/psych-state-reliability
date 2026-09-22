from __future__ import annotations
import copy
from pathlib import Path
from psyr.common import Journal, digest, read_json, stable_seed, write_json
from psyr.benchmark.dataset import (CONDITIONS, COUNTS, evidence, latent_trajectory,
                                    applicable_conditions, perturbation_mode, classify_condition)
from psyr.degradations.conditions import apply_condition, fault_candidates, fault_free_control, history_fault_notes
from psyr.architectures.state import NaiveState, ReliableState, repair_slot
from psyr.architectures.prompts import extraction_messages, decision_messages, response_messages, judge_messages
from psyr.evaluation.schema import ParseError, parse_candidates, parse_decision, parse_judge
from psyr.evaluation.metrics import state_counts, state_errors, decision_violations, attribution, aggregate_judgments

def parse_call(backend, call_id, messages, seed, parser):
    result = backend.complete(call_id, messages, seed)
    if result["status"] != "ok":
        return None, "api_error"
    try:
        return parser(result["text"]), None
    except (ParseError, ValueError, TypeError):
        return None, "parser_error"

def repair_reference(case, turn, view, field):
    gold = case["gold"][turn-1]
    known = case["observable"][turn-1]
    fixed = repair_slot(view, field, gold[field], field in known)
    if field in fixed and "quote" in fixed[field]:
        for t in reversed(case["turns"][:turn]):
            match = [s for s in t["statements"] if s["field"] == field and s["value"] == gold[field]]
            if match:
                fixed[field].update(quote=match[-1]["text"], source_turn=t["turn"], episode=t["episode"], epistemic="explicit", uncertainty="confident")
                break
    return fixed

def run_case(case, backend, judge, config, outcomes, architectures=("A","B","C"), disabled=(), control=False):
    cid = case["latent"]["id"]
    condition = case["condition"]
    suffix = "control" if control else "primary"
    mode = "-".join(disabled) if disabled else "full"
    namespace = f"{cid}/{condition}/{suffix}/{mode}"
    states = {a:(NaiveState() if a == "B" else ReliableState(disabled, config["max_age_days"])) for a in architectures if a != "A"}
    for t in range(1,6):
        ev = evidence(case,t)
        seed = stable_seed(config["seed"],cid,condition,t)
        # This exact list is extracted once and shared, with deep copies to prevent mutation.
        updates, extract_error = parse_call(backend,f"{cid}/{condition}/shared/extract/{t}",extraction_messages(ev),seed,parse_candidates)
        candidates = (updates or []) + fault_candidates(case,t)
        for a in architectures:
            call_id = f"{namespace}/{a}/{t}"
            forced = False
            records = []
            if a == "A":
                view = None
            else:
                states[a].update(copy.deepcopy(candidates),ev)
                view = states[a].view()
                if a == "C":
                    records = [r for r in states[a].metadata() if r["status"] != "active"]
                    forced = states[a].should_defer()
            messages = decision_messages(a,ev,view,records,history_fault_notes(case,t),forced)
            decision, decision_error = parse_call(backend,call_id+"/decide",messages,seed,parse_decision)
            original_decision = copy.deepcopy(decision)
            if forced and decision is not None:
                # An auditable state-management policy, never a rewrite of the raw completion.
                decision.update(action="clarify",family="none")
            raw_response = None
            response_error = None
            judgments = []
            if decision is not None:
                response = backend.complete(call_id+"/respond",response_messages(ev,decision),seed)
                raw_response = response["text"] if response["status"] == "ok" else None
                if not raw_response or not raw_response.strip():
                    response_error = "api_or_empty_response"
                if raw_response and judge is not None:
                    observable_gold = {f:case["gold"][t-1][f] for f in case["observable"][t-1]}
                    for j in range(config["judge_repeats"]):
                        judgment, err = parse_call(judge,call_id+f"/judge/{j}",judge_messages(ev,raw_response,observable_gold),stable_seed(seed,j),parse_judge)
                        # A cited response span must actually occur, otherwise invalid judgment.
                        if judgment and any(s not in raw_response for s in judgment["evidence_spans"]):
                            judgment = None
                        judgments.append(judgment)
            gold, known = case["gold"][t-1], case["observable"][t-1]
            evaluated_view = view if a != "A" else (decision["targets"] if decision else {})
            bad = decision_violations(decision,gold,known,t)
            errors = state_errors(evaluated_view,gold,known)
            probes = []
            # A has no persistent-state repair point; it gets secondary target-error metrics only.
            if a != "A":
                for error in errors:
                    field = error["field"]
                    replay, re_err = parse_call(backend,call_id+f"/replay/{field}",messages,seed,parse_decision)
                    fixed_view = repair_reference(case,t,view,field)
                    fixed_messages = decision_messages(a,ev,fixed_view,records,history_fault_notes(case,t),forced)
                    repaired, fix_err = parse_call(backend,call_id+f"/repair/{field}",fixed_messages,seed,parse_decision)
                    if forced:
                        for d in (replay,repaired):
                            if d is not None:
                                d.update(action="clarify",family="none")
                    classification = attribution(bad if decision else None,
                        decision_violations(replay,gold,known,t) if replay else None,
                        decision_violations(repaired,gold,known,t) if repaired else None,field)
                    probes.append(dict(error,attribution=classification,replay_status=re_err,repair_status=fix_err,
                                       repaired_decision=repaired,replay_decision=replay))
            aggregate = aggregate_judgments(judgments)
            row = {"kind":"turn_outcome","key":call_id,"base_id":cid,"split":case["latent"]["split"],
                "context_family":case["latent"]["context_family"],"archetype":case["latent"]["archetype"],
                "relationship":case["latent"]["relationship"],
                "perturbation_mode":perturbation_mode(case["latent"],condition),
                "design_status":classify_condition(case["latent"],condition)["status"],
                "benchmark_version":case["latent"]["benchmark_version"],
                "condition":condition,"architecture":a,
                "control":control,"ablations":list(disabled),"turn":t,"evidence_hash":digest(ev),"evidence":ev,
                "candidate_hash":digest(candidates),"candidates":candidates,"state":evaluated_view,"state_records":records,
                "extract_error":extract_error if a!="A" else None,"decision_parse_error":decision_error,"response_error":response_error,
                "original_decision":original_decision,"decision":decision,"forced_clarification":forced,
                "response":raw_response,"proceeded":bool(decision and decision["action"]=="proceed" and raw_response and raw_response.strip()),
                "transition_appraisal_correct":(evaluated_view.get("appraisal",{}).get("value")==gold["appraisal"] and evaluated_view.get("appraisal",{}).get("stance")=="user_report") if condition in ("contradictory_evidence","superseded_appraisal") and t>=3 else None,
                "stale_active":sum(v.get("episode",ev[-1]["episode"])!=ev[-1]["episode"] for v in evaluated_view.values()) if a=="C" else None,
                "fault_appraisal_persists":(any(e["field"]=="appraisal" for e in errors) if condition in ("unsupported_inference","stale_state") and t>=3 else None),
                "violations":sorted(bad),"decision_error":bool(bad),"state_error_items":errors,
                "probes":probes,"judgments":judgments, **state_counts(evaluated_view,gold,known), **aggregate}
            outcomes.append(row)

def run_experiment(root, split, backend, judge, config, limit=None, disabled=(), fixtures=False):
    if len(disabled)>1:
        raise ValueError("Only the predefined one-mechanism-at-a-time ablations are allowed")
    if split == "heldout":
        if limit is not None:
            raise RuntimeError("The frozen held-out design requires all 100 bases; subset tuning is prohibited")
        if fixtures or getattr(backend,"is_fixture",False) or getattr(judge,"is_fixture",False):
            raise RuntimeError("Fixture backend prohibited for held-out research")
        from psyr.freeze import verify_final_freeze
        verify_final_freeze(root,config)
    if limit is not None and not 1 <= limit <= COUNTS[split]:
        raise ValueError("Invalid trajectory limit")
    run_root = Path(backend.journal.path).parent
    out = Journal(run_root / "outcomes.jsonl")
    config_hash = digest(config)
    manifest_path = run_root / "run_manifest.json"
    manifest = {"split":split,"config_hash":config_hash,"config":config,"limit":limit,"ablations":list(disabled),
                "fixture":fixtures or getattr(backend,"is_fixture",False),"source_digest":None}
    from psyr.freeze import source_manifest
    manifest["source_digest"] = digest(source_manifest(root))
    if manifest_path.exists() and read_json(manifest_path) != manifest:
        raise RuntimeError("Cannot resume a changed run")
    if not manifest_path.exists():
        write_json(manifest_path,manifest,exclusive=True)
    completed = {r["key"] for r in out.records}
    class Sink:
        def append(self,row):
            if row["key"] not in completed:
                out.append(row)
                completed.add(row["key"])
    archs = ("C",) if disabled else ("A","B","C")
    for i in range(limit or COUNTS[split]):
        latent = latent_trajectory(split,i,allow_heldout=(split=="heldout"))
        for condition in applicable_conditions(latent):
            case = apply_condition(latent,condition)
            run_case(case,backend,judge,config,Sink(),archs,disabled)
            if condition in ("unsupported_inference","stale_state"):
                run_case(fault_free_control(case),backend,judge,config,Sink(),archs,disabled,control=True)
    return {"turn_outcomes":len(out.records),"fixture":manifest["fixture"],"split":split}
