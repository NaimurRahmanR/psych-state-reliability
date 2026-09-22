"""Canned protocol fixtures in temporary directories; never research outputs."""
import copy
import http.server
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from psyr.common import ROOT, Journal, canonical, digest, read_json, write_json
from psyr.benchmark.dataset import latent_trajectory, evidence
from psyr.degradations.conditions import apply_condition
from psyr.runner import run_case, run_experiment
from psyr.analysis.report import analyze
from psyr.evaluation.audit import make_packet, analyze_human, traps
from psyr.backend import Backend, BackendUnavailable
from psyr.freeze import source_manifest, verify_final_freeze

class FixtureBackend:
    is_fixture=True
    def __init__(self,path,case,broken=False):
        self.journal=Journal(path); self.case=case; self.broken=broken
    def complete(self,call_id,messages,seed):
        old=[r for r in self.journal.records if r.get("call_id")==call_id]
        if old: return old[0]
        data=json.loads(messages[-1]["content"])
        if "/extract/" in call_id:
            turn=data["evidence"][-1]["turn"]; updates=[]
            for s in self.case["turns"][turn-1]["statements"]:
                if s["field"]=="narrative": continue
                updates.append({"field":s["field"],"value":s["value"],"source_turn":turn,"quote":s["text"],
                    "epistemic":"explicit","uncertainty":"confident","episode":data["evidence"][-1]["episode"],
                    "relation":"assert","supersedes":[],"stance":"user_report"})
            text=canonical({"updates":updates})
        elif call_id.endswith("/respond"):
            text="This is a canned software fixture, not an LLM response or a psychological intervention."
        else:
            targets={f:{"value":v["value"],"stance":v["stance"]} for f,v in data.get("state",{}).items()}
            goal=targets.get("goal",{}).get("value")
            text=canonical({"action":"proceed","family":"validation" if goal=="feel_understood" else "reappraisal", "targets":targets,"basis":[1]})
            if self.broken and "/A/2/decide" in call_id: text="malformed fixture"
        return self.journal.append({"call_id":call_id,"status":"ok","text":text,"messages":messages,"seed":seed,"fixture":True})

class PipelineTests(unittest.TestCase):
    def config(self): return read_json(ROOT/"configs/experiment.json")
    def test_shared_candidates_and_same_evidence_every_turn(self):
        case=apply_condition(latent_trajectory("calibration",0),"unsupported_inference")
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",case); sink=Journal(Path(d)/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            self.assertEqual(len(sink.records),15)
            for t in range(1,6):
                rs=[r for r in sink.records if r["turn"]==t]
                self.assertEqual(len({r["evidence_hash"] for r in rs}),1)
                self.assertEqual(len({r["candidate_hash"] for r in rs}),1)
            extracts=[r for r in backend.journal.records if "/shared/extract/" in r["call_id"]]
            self.assertEqual(len(extracts),5)
            for t in range(1,6):
                decisions=[r for r in backend.journal.records if f"/{t}/decide" in r["call_id"]]
                self.assertEqual(len({r["seed"] for r in decisions}),1)
    def test_repair_does_not_mutate_live_state(self):
        # V2: the injected fault persists in B's naive state from the injection turn
        # until the trajectory next states an appraisal explicitly. Under V1 no
        # trajectory ever restated an appraisal, so this was simply "turns >= 3".
        case=apply_condition(latent_trajectory("calibration",0),"unsupported_inference")
        injection=case["faults"][0]["turn"]
        later=[t["turn"] for t in case["turns"]
               if t["turn"]>injection and any(s["field"]=="appraisal" for s in t["statements"])]
        window=range(injection,(later[0] if later else 6))
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",case); sink=Journal(Path(d)/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            b=[r for r in sink.records if r["architecture"]=="B" and r["turn"] in window]
            self.assertTrue(b)
            self.assertTrue(all(r["state"]["appraisal"]["stance"]=="external_fact" for r in b))
            self.assertTrue(any(r["probes"] for r in b))

    def test_explicit_user_evidence_supersedes_injected_fault(self):
        """V2 invariant: a later explicit user appraisal statement must be able to
        displace an injected fault in B. Otherwise the benchmark would measure an
        architecture's inability to update rather than fault propagation."""
        case=apply_condition(latent_trajectory("calibration",0),"unsupported_inference")
        injection=case["faults"][0]["turn"]
        later=[t["turn"] for t in case["turns"]
               if t["turn"]>injection and any(s["field"]=="appraisal" for s in t["statements"])]
        self.assertTrue(later,"calibration index 0 should restate an appraisal after injection")
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",case); sink=Journal(Path(d)/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            row=next(r for r in sink.records if r["architecture"]=="B" and r["turn"]==later[0])
            self.assertEqual(row["state"]["appraisal"]["stance"],"user_report")
    def test_parser_failures_preserve_eligible_rows(self):
        case=apply_condition(latent_trajectory("calibration",0),"clean")
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",case,True); sink=Journal(Path(d)/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            row=next(r for r in sink.records if r["architecture"]=="A" and r["turn"]==2)
            self.assertEqual(row["decision_parse_error"],"parser_error"); self.assertFalse(row["proceeded"])
            self.assertEqual(len(sink.records),15)
    def test_fixture_cannot_enter_heldout(self):
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",None)
            with self.assertRaises(RuntimeError): run_experiment(ROOT,"heldout",backend,None,self.config())
    def test_partial_heldout_and_combined_ablation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            backend=FixtureBackend(Path(d)/"raw.jsonl",None)
            with self.assertRaises(RuntimeError): run_experiment(ROOT,"heldout",backend,None,self.config(),limit=1)
            with self.assertRaises(ValueError): run_experiment(ROOT,"calibration",backend,None,self.config(),disabled=("temporal","epistemic"))
    def test_analysis_rejects_fixture_and_is_reproducible(self):
        case=apply_condition(latent_trajectory("calibration",0),"clean")
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); backend=FixtureBackend(d/"raw.jsonl",case); sink=Journal(d/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            write_json(d/"run_manifest.json",{"fixture":True,"split":"calibration","config":self.config(),"limit":1,"ablations":[]})
            with self.assertRaises(RuntimeError): analyze(d,d/"report")
            a=analyze(d,d/"report",allow_fixture=True); first=(d/"report/analysis.json").read_bytes()
            b=analyze(d,d/"report",allow_fixture=True)
            self.assertEqual(a,b); self.assertEqual(first,(d/"report/analysis.json").read_bytes())
            self.assertFalse(a["complete_primary"])
    def test_v2_complete_run_counts_and_stratified_outputs(self):
        # One base trajectory, every applicable condition plus matched controls.
        from psyr.benchmark.dataset import applicable_conditions, planned_variants
        from psyr.degradations.conditions import fault_free_control
        latent=latent_trajectory("calibration",0)
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); sink=Journal(d/"outcomes.jsonl")
            for n,condition in enumerate(applicable_conditions(latent)):
                case=apply_condition(latent,condition)
                run_case(case,FixtureBackend(d/f"raw{n}.jsonl",case),None,self.config(),sink)
                if condition in ("unsupported_inference","stale_state"):
                    ctl=fault_free_control(case)
                    run_case(ctl,FixtureBackend(d/f"rawc{n}.jsonl",ctl),None,self.config(),sink,control=True)
            write_json(d/"run_manifest.json",{"fixture":True,"split":"calibration","config":self.config(),"limit":2,"ablations":[]})
            # limit=2 expects two bases; only one was run, so the run must be flagged incomplete.
            self.assertFalse(analyze(d,d/"r2",allow_fixture=True)["complete_primary"])
            write_json(d/"run_manifest.json",{"fixture":True,"split":"calibration","config":self.config(),"limit":1,"ablations":[]},exclusive=False)
            self.assertEqual(planned_variants("calibration",1),len(applicable_conditions(latent)))
            a=analyze(d,d/"r1",allow_fixture=True)
            self.assertTrue(a["complete_primary"])
            self.assertEqual(a["expected_primary_turns"],len(applicable_conditions(latent))*3*5)
            self.assertTrue(all(r.get("design_status") in ("clean","stratified") for r in sink.records))
            self.assertIn("ALL_REFERENCE",{r["condition"] for r in a["counts"]})
            modes={(r["condition"],r["perturbation_mode"]) for r in a["stratified_counts"]}
            self.assertTrue(modes)
            self.assertFalse(any(r["condition"]=="clean" for r in a["stratified_counts"]))

    def test_manual_packet_blinded_and_blank(self):
        case=apply_condition(latent_trajectory("calibration",0),"clean")
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); backend=FixtureBackend(d/"raw.jsonl",case); sink=Journal(d/"outcomes.jsonl")
            run_case(case,backend,None,self.config(),sink)
            make_packet(d,d/"packet")
            text=(d/"packet/blinded_packet.jsonl").read_text()
            self.assertNotIn('"architecture"',text); self.assertNotIn('"automated_failure"',text)
            write_json(d/"packet/auditor.json",{"auditor_type":"human","rater_id":"test","qualifications":"Test only"})
            with self.assertRaises(ValueError): analyze_human(d/"packet")
    def test_calibration_traps_marked_authored(self):
        # V2: 8 calibration bases x 7 kinds (2 negative controls, 5 expected failures).
        items=list(traps("calibration")); self.assertEqual(len(items),56)
        self.assertTrue(all(x["author_constructed"] for x in items)); self.assertEqual(sum(not x["expected_failure"] for x in items),16)
        self.assertGreaterEqual(len({x["family"] for x in items}),6)
        for x in items:  # no V1 organiser-scenario text can leak into a diversified benchmark
            self.assertNotIn("organiser",x["response"].lower()); self.assertNotIn("scheduling issue",x["response"].lower())
        with self.assertRaises(RuntimeError): list(traps("heldout"))
    def test_frozen_code_mutation_blocks_heldout(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"src").mkdir(); (root/"src/x.py").write_text("first")
            write_json(root/"protocol/freeze_manifest.json",{"status":"FINAL_FROZEN","config_hash":digest({}),"files":source_manifest(root)})
            verify_final_freeze(root,{})
            (root/"src/x.py").write_text("changed")
            with self.assertRaises(RuntimeError): verify_final_freeze(root,{})
    def test_actual_http_adapter_records_response_and_caches(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            calls=0
            model="test-fixture-v1"
            def do_POST(self):
                type(self).calls+=1
                self.rfile.read(int(self.headers["Content-Length"]))
                payload=canonical({"model":type(self).model,"choices":[{"message":{"content":"wire fixture"}}],"system_fingerprint":"test-only"}).encode()
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(payload)
            def log_message(self,*args): pass
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{"PSYR_API_BASE":f"http://127.0.0.1:{server.server_port}/v1"}):
                cfg=self.config(); cfg.update(model="test-fixture-v1",model_revision="test-only")
                backend=Backend(cfg,Path(d)/"raw.jsonl"); m=[{"role":"user","content":"test"}]
                first=backend.complete("test",m,1); second=backend.complete("test",m,1)
                self.assertEqual(first,second); self.assertEqual(Handler.calls,1); self.assertEqual(first["text"],"wire fixture")
                with self.assertRaises(RuntimeError): backend.complete("test",m,2)
                Handler.model="unexpected-fixture"
                with self.assertRaises(BackendUnavailable): backend.complete("drift",m,1)
                with self.assertRaises(BackendUnavailable): backend.complete("drift",m,1)
                self.assertEqual(backend.journal.records[-1]["error_type"],"ModelIdentityDrift")
        finally:
            server.shutdown(); server.server_close(); thread.join()

if __name__=="__main__": unittest.main()
