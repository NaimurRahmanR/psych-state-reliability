import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from psyr.common import ROOT, Journal, digest, read_json, write_json
from psyr.benchmark.dataset import FIELDS, CONDITIONS, CONTEXTS, VOCAB, latent_trajectory, render, evidence, build_split
from psyr.degradations.conditions import apply_condition, fault_free_control, fault_candidates
from psyr.architectures.state import NaiveState, ReliableState, repair_slot
from psyr.architectures.prompts import decision_messages, extraction_messages
from psyr.evaluation.schema import parse_candidates, parse_decision, parse_judge, ParseError
from psyr.evaluation.metrics import state_errors, state_counts, sepr_counts, coverage_counts, attribution, aggregate_judgments, classification_audit
from psyr.analysis.statistics import paired_ratio_bootstrap, exact_mcnemar
from psyr.analysis.report import analyze
from psyr.freeze import verify_final_freeze, finalize, source_manifest
from psyr.backend import Backend, BackendUnavailable
from psyr.runner import run_case, run_experiment

def candidate(field="appraisal",value="negative_judgment",turn=1,quote="I think they judge me negatively.",**kw):
    return dict(field=field,value=value,source_turn=turn,quote=quote,epistemic="explicit",uncertainty="confident",
                episode="session_topic_1",relation="assert",supersedes=[],stance="user_report")|kw

def ev(text="I think they judge me negatively.",turn=1,day=0,episode="session_topic_1"):
    return {"turn":turn,"day":day,"episode":episode,"role":"user","text":text}

class DatasetTests(unittest.TestCase):
    def test_deterministic_latent(self):
        self.assertEqual([latent_trajectory("calibration",i) for i in range(20)],[latent_trajectory("calibration",i) for i in range(20)])
    def test_unique_calibration_specs(self):
        specs=[latent_trajectory("calibration",i) for i in range(20)]
        self.assertEqual(len({s["id"] for s in specs}),20)
        self.assertEqual(len({digest(s) for s in specs}),20)
    def test_context_split_disjoint_without_heldout_generation(self):
        # V2 replaces V1's disjoint-family design (which made calibration uninformative
        # about held-out families). The invariant that matters is instance-level:
        # distinct IDs and seeds, and no held-out instance generated pre-freeze.
        from psyr.benchmark.dataset import SEEDS, allocation, COUNTS
        self.assertNotEqual(SEEDS["calibration"],SEEDS["heldout"])
        self.assertEqual({allocation("heldout",i)[0] for i in range(COUNTS["heldout"])},set(CONTEXTS))
        with self.assertRaises(RuntimeError): latent_trajectory("heldout",0)
    def test_no_future_turns(self):
        c=apply_condition(latent_trajectory("calibration",0),"clean")
        for t in range(1,6): self.assertEqual([x["turn"] for x in evidence(c,t)],list(range(1,t+1)))
    def test_future_mutation_cannot_change_prefix(self):
        c=apply_condition(latent_trajectory("calibration",0),"clean"); before=evidence(c,2)
        c["turns"][4]["statements"][0]["text"]="FUTURE SECRET"
        self.assertEqual(before,evidence(c,2))
    def test_gold_not_in_public_evidence(self):
        c=render(latent_trajectory("calibration",0))
        self.assertEqual(set(evidence(c,1)[0]),{"turn","day","episode","role","text"})
    def test_latent_precedes_render_and_not_mutated(self):
        x=latent_trajectory("calibration",0); before=copy.deepcopy(x)
        for cond in CONDITIONS: apply_condition(x,cond)
        self.assertEqual(x,before)
    def test_missing_only_appraisal_statement(self):
        x=latent_trajectory("calibration",0); a=render(x); b=apply_condition(x,"missing_evidence")
        self.assertEqual(a["turns"][1:],b["turns"][1:]); self.assertEqual(a["gold"],b["gold"])
        self.assertEqual([s for s in a["turns"][0]["statements"] if s["field"]!="appraisal"],b["turns"][0]["statements"])
    def test_contradiction_and_supersession_only_one_update(self):
        x=latent_trajectory("calibration",0); clean=render(x)
        for condition in ("contradictory_evidence","superseded_appraisal"):
            c=apply_condition(x,condition)
            self.assertEqual([i for i in range(5) if c["turns"][i]!=clean["turns"][i]],[2])
            for i in range(5):
                for field in FIELDS:
                    if field!="appraisal": self.assertEqual(c["gold"][i][field],clean["gold"][i][field])
    def test_unsupported_inference_keeps_all_user_evidence(self):
        x=latent_trajectory("calibration",0)
        self.assertEqual(evidence(render(x),5),evidence(apply_condition(x,"unsupported_inference"),5))
    def test_stale_has_matched_fault_free_control(self):
        c=apply_condition(latent_trajectory("calibration",0),"stale_state"); ctl=fault_free_control(c)
        self.assertEqual(c["turns"],ctl["turns"]); self.assertEqual(c["gold"],ctl["gold"])
        self.assertTrue(c["faults"]); self.assertFalse(ctl["faults"])
    def test_stale_new_appraisal_is_unobserved(self):
        c=apply_condition(latent_trajectory("calibration",0),"stale_state")
        self.assertNotIn("appraisal",c["observable"][2]); self.assertEqual(c["gold"][2]["appraisal"],"unknown")
    def test_no_fault_experiment_label_in_candidate(self):
        c=apply_condition(latent_trajectory("calibration",0),"unsupported_inference")
        self.assertNotIn("fault_type",fault_candidates(c,3)[0]); self.assertFalse(fault_candidates(c,2))
    def test_heldout_generation_gate(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError): build_split("heldout",Path(d)/"data.jsonl")
            self.assertFalse((Path(d)/"data.jsonl").exists())
    def test_all_calibration_variants_valid(self):
        # V2: every primary-matrix variant is valid; excluded cells must refuse to render.
        from psyr.benchmark.dataset import applicable_conditions
        for i in range(20):
            latent=latent_trajectory("calibration",i)
            for condition in CONDITIONS:
                if condition not in applicable_conditions(latent):
                    with self.assertRaises(ValueError): apply_condition(latent,condition)
                    continue
                c=apply_condition(latent,condition)
                self.assertEqual(len(c["gold"]),5)
                for row in c["gold"]:
                    self.assertTrue(all(row[f] in VOCAB[f] for f in FIELDS))

class StateTests(unittest.TestCase):
    def test_temporal_threshold_boundary(self):
        c=ReliableState(); c.update([candidate()],[ev()]); c.update([],[ev(),ev("check-in",2,14)])
        self.assertTrue(c.view()); c.update([],[ev(),ev("check-in",3,15)])
        self.assertFalse(c.view())
    def test_b_handles_correction(self):
        b=NaiveState(); b.update([candidate()], [ev()])
        b.update([candidate(value="uncertain_meaning",relation="correct")],[ev()])
        self.assertEqual(b.view()["appraisal"]["value"],"uncertain_meaning")
    def test_provenance_preserved(self):
        c=ReliableState(); x=candidate(); c.update([x],[ev()])
        self.assertEqual(c.view()["appraisal"]["quote"],x["quote"])
    def test_unknown_source_rejected(self):
        c=ReliableState(); c.update([candidate(turn=99)],[ev()]); self.assertFalse(c.view())
    def test_quote_mismatch_rejected(self):
        c=ReliableState(); c.update([candidate(quote="invented")],[ev()]); self.assertFalse(c.view())
    def test_exact_quote_not_treated_as_entailment_proof(self):
        c=ReliableState(); c.update([candidate(value="resolved")],[ev()])
        self.assertEqual(c.view()["appraisal"]["value"],"resolved")
        # This deliberate semantic error survives exact-span checks: no oracle guard.
    def test_inference_quarantined(self):
        c=ReliableState(); c.update([candidate(epistemic="inferred")],[ev()]); self.assertFalse(c.view())
    def test_external_appraisal_not_promoted(self):
        c=ReliableState(); c.update([candidate(stance="external_fact")],[ev()]); self.assertFalse(c.view())
    def test_supersession_link(self):
        c=ReliableState(); c.update([candidate()],[ev()])
        new=candidate(value="situational_explanation",turn=2,quote="I correct that.",relation="correct")
        c.update([new],[ev(),ev("I correct that.",2,3)])
        old=c.records[0]; self.assertEqual(old["status"],"superseded")
        self.assertEqual(old["superseded_by"],c.records[-1]["id"])
    def test_conflicting_candidates_preserved(self):
        c=ReliableState(); c.update([candidate()],[ev()])
        c.update([candidate(value="situational_explanation",turn=2,quote="Another interpretation.",relation="conflict")],[ev(),ev("Another interpretation.",2,3)])
        self.assertFalse(c.view()); self.assertEqual(sum(r["status"]=="competing" for r in c.records),2)
    def test_reported_uncertainty_is_valid_state(self):
        c=ReliableState(); c.update([candidate(value="uncertain_meaning",relation="conflict")],[ev()])
        self.assertIn("appraisal",c.view())
    def test_stale_episode_expires(self):
        c=ReliableState(); c.update([candidate()],[ev()]); c.update([],[ev(),ev("New activity.",2,3,"session_topic_2")])
        self.assertFalse(c.view()); self.assertEqual(c.records[0]["status"],"stale")
    def test_stale_replay_rejected(self):
        c=ReliableState(); c.update([candidate()],[ev(),ev("New activity.",2,3,"session_topic_2")])
        self.assertFalse(c.view())
    def test_temporal_ablation_disables_expiry(self):
        c=ReliableState(disabled=("temporal",)); c.update([candidate()],[ev(),ev("New activity.",2,3,"session_topic_2")])
        self.assertTrue(c.view())
    def test_provenance_ablation(self):
        c=ReliableState(disabled=("provenance",)); c.update([candidate(quote="invented")],[ev()]); self.assertTrue(c.view())
    def test_epistemic_ablation(self):
        c=ReliableState(disabled=("epistemic",)); c.update([candidate(epistemic="inferred")],[ev()]); self.assertTrue(c.view())
    def test_contradiction_ablation(self):
        c=ReliableState(disabled=("contradiction",)); c.update([candidate()],[ev()])
        c.update([candidate(value="resolved",relation="conflict")],[ev()]); self.assertEqual(c.view()["appraisal"]["value"],"resolved")
    def test_defer_ablation(self):
        self.assertTrue(ReliableState().should_defer()); self.assertFalse(ReliableState(disabled=("defer",)).should_defer())
    def test_repair_changes_only_one_slot(self):
        state={"appraisal":{"value":"negative_judgment","stance":"external_fact"},"emotion":{"value":"hurt","stance":"user_report"}}
        fixed=repair_slot(state,"appraisal","uncertain_meaning",True)
        self.assertEqual(state["emotion"],fixed["emotion"]); self.assertNotEqual(state["appraisal"],fixed["appraisal"])
        self.assertEqual(state["appraisal"]["value"],"negative_judgment")

class MetricsTests(unittest.TestCase):
    def test_hypothetical_alternative_not_asserted_error(self):
        self.assertEqual(state_errors({"appraisal":{"value":"resolved","stance":"hypothesis"}},{"appraisal":"negative_judgment"},[]),[])
    def test_sepr_hand_computed(self):
        r=sepr_counts([{"attribution":x} for x in ("propagated","not_demonstrated","ambiguous","propagated")])
        self.assertEqual(r["sepr"],.5); self.assertEqual(r["sepr_upper_bound"],.75)
    def test_zero_denominator_is_undefined(self): self.assertIsNone(sepr_counts([])["sepr"])
    def test_coverage_includes_failures(self):
        x=coverage_counts([{"proceeded":True,"decision_error":False,"fidelity_failure":False},{"proceeded":False},{"proceeded":True,"fidelity_failure":None}])
        self.assertEqual(x["coverage"],2/3); self.assertEqual(x["reliable_coverage"],1/3)
    def test_unsupported_lucky_guess_is_error(self):
        g=latent_trajectory("calibration",0)["states"][0]
        x={"appraisal":{"value":g["appraisal"],"stance":"user_report"}}
        self.assertEqual(state_errors(x,g,["emotion"])[0]["reason"],"unsupported")
    def test_user_appraisal_is_not_external_truth(self):
        g=latent_trajectory("calibration",0)["states"][0]
        x={"appraisal":{"value":g["appraisal"],"stance":"user_report"}}
        self.assertEqual(state_errors(x,g,FIELDS),[])
        x["appraisal"]["stance"]="external_fact"; self.assertEqual(len(state_errors(x,g,FIELDS)),1)
    def test_precision_recall_known_example(self):
        g=latent_trajectory("calibration",0)["states"][0]; x={"emotion":{"value":g["emotion"],"stance":"user_report"}}
        c=state_counts(x,g,FIELDS); self.assertEqual((c["state_correct"],c["state_asserted"],c["state_required"]),(1,1,6))
    def test_attribution_needs_replay_agreement(self):
        self.assertEqual(attribution({"appraisal"},{"goal"},set(),"appraisal"),"ambiguous")
    def test_attribution_requires_repair_effect(self):
        self.assertEqual(attribution({"appraisal"},{"appraisal"},{"appraisal"},"appraisal"),"not_demonstrated")
        self.assertEqual(attribution({"appraisal"},{"appraisal"},set(),"appraisal"),"propagated")
    def test_aggregation_missing_not_pass(self):
        self.assertIsNone(aggregate_judgments([None,None,None])["fidelity_failure"])
    def test_audit_confusion_matrix(self):
        x=classification_audit([True,True,False,False],[True,False,True,False])
        self.assertEqual((x["tp"],x["fn"],x["fp"],x["tn"]),(1,1,1,1)); self.assertEqual(x["cohen_kappa"],0)
    def test_bootstrap_paired_constant_difference(self):
        r=paired_ratio_bootstrap({"x":(0,1),"y":(0,1)},{"x":(1,1),"y":(1,1)},100)
        self.assertEqual((r["difference_b_minus_a"],r["ci_low"],r["ci_high"]),(1,1,1))
    def test_bootstrap_reproducible(self):
        args=({"x":(0,1),"y":(1,1)},{"x":(1,1),"y":(0,1)})
        self.assertEqual(paired_ratio_bootstrap(*args),paired_ratio_bootstrap(*args))
    def test_bootstrap_rejects_unpaired(self):
        with self.assertRaises(ValueError): paired_ratio_bootstrap({"a":(1,1)},{"b":(1,1)})
    def test_exact_mcnemar_known(self):
        self.assertEqual(exact_mcnemar([False]*5,[True]*5)["p_exact"],.0625)

class PlumbingTests(unittest.TestCase):
    def test_prompt_evidence_equivalence(self):
        e=evidence(render(latent_trajectory("calibration",0)),2)
        payloads=[json.loads(decision_messages(a,e,{})[1]["content"]) for a in ("A","B","C")]
        self.assertEqual(payloads[0]["evidence"],payloads[1]["evidence"]); self.assertEqual(payloads[1]["evidence"],payloads[2]["evidence"])
    def test_bc_identical_instruction_template(self):
        self.assertEqual(decision_messages("B",[ev()],{})[0],decision_messages("C",[ev()],{})[0])
    def test_no_state_input_to_a(self): self.assertNotIn("state",json.loads(decision_messages("A",[ev()])[1]["content"]))
    def test_strict_parser_duplicate_rejected(self):
        with self.assertRaises(ParseError): parse_candidates('{"updates":[],"updates":[]}')
    def test_strict_parser_extra_field_rejected(self):
        with self.assertRaises(ParseError): parse_candidates('{"updates":[],"reason":"foo"}')
    def test_parser_future_not_silently_corrected(self):
        x=candidate(turn=99); self.assertEqual(parse_candidates(json.dumps({"updates":[x]}))[0]["source_turn"],99)
    def test_invalid_decision_visible(self):
        with self.assertRaises(ParseError): parse_decision('{"action":"proceed","family":"none","targets":{},"basis":[]}')
    def test_append_only_journal_detects_edit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"raw.jsonl"; j=Journal(p); j.append({"text":"original"}); j.append({"text":"second"})
            self.assertEqual(len(Journal(p).records),2)
            p.write_text(p.read_text().replace("original","altered"))
            with self.assertRaises(ValueError): Journal(p)
    def test_heldout_requires_final_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError): verify_final_freeze(Path(d),{})
    def test_cannot_freeze_unset_models(self):
        cfg=read_json(ROOT/"configs/experiment.json"); cfg["model"]=None
        with self.assertRaises(RuntimeError): finalize(ROOT,cfg,Path("nonexistent"))
    def test_backend_no_fake_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=read_json(ROOT/"configs/experiment.json"); cfg["model"]=None
            with self.assertRaises(BackendUnavailable): Backend(cfg,Path(d)/"raw.jsonl")
    def test_source_freeze_covers_prompts_and_scripts(self):
        m=source_manifest(ROOT)
        self.assertIn("configs/prompts/decide.txt",m); self.assertIn("scripts/psyr.py",m); self.assertIn("src/psyr/runner.py",m)

if __name__=="__main__": unittest.main()
