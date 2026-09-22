"""Benchmark V2 scientific invariants.

These tests check properties the experiment's validity depends on, not merely
that functions execute. No test generates, reads or inspects held-out content.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from psyr.common import ROOT, digest, read_json, read_jsonl
from psyr.benchmark import dataset as ds
from psyr.benchmark.dataset import (ARCHETYPES, ARCHETYPE_IDS, CONDITIONS, COUNTS, FIELDS, PERTURBATION_TURN,
                                    SEEDS, TRANSITION_TYPES, VOCAB, allocation, applicable_conditions,
                                    archetype_shape, build_split, classify_condition, evidence,
                                    latent_trajectory, manifest_row, planned_variants, render)
from psyr.benchmark.families import FAMILIES, FAMILY_IDS
from psyr.benchmark.diversity import audit, content_tokens, jaccard
from psyr.degradations.conditions import apply_condition, fault_candidates, fault_free_control
from psyr.architectures.prompts import decision_messages, extraction_messages
from psyr.architectures.state import NaiveState, ReliableState

CAL = [latent_trajectory("calibration", i) for i in range(COUNTS["calibration"])]


def primary_cases():
    for latent in CAL:
        for condition in applicable_conditions(latent):
            yield latent, condition, apply_condition(latent, condition)


class FamilyDiversityTests(unittest.TestCase):
    def test_twelve_families_with_distinct_relationships_and_ambiguity(self):
        self.assertEqual(len(FAMILY_IDS), 12)
        self.assertEqual(len({f["relationship"] for f in FAMILIES.values()}), 12)
        self.assertEqual(len({f["ambiguity_source"] for f in FAMILIES.values()}), 12)

    def test_situations_are_not_noun_substitutions(self):
        # V1 used one situation for every trajectory. Here no two authored situations
        # may share most of their content vocabulary.
        sits = {k: content_tokens(f["situation"]) for k, f in FAMILIES.items()}
        keys = sorted(sits)
        worst = max(jaccard(sits[a], sits[b]) for i, a in enumerate(keys) for b in keys[i + 1:])
        self.assertLess(worst, 0.25)

    def test_family_specific_degradation_texts_all_distinct(self):
        for field in ("contradiction", "supersession", "confirming", "competing", "changed_circumstances"):
            texts = [f[field] for f in FAMILIES.values()]
            self.assertEqual(len(set(texts)), 12, field)
        self.assertEqual(len({f["second_topic"]["label"] for f in FAMILIES.values()}), 12)

    def test_calibration_covers_every_family_and_archetype(self):
        self.assertEqual({l["context_family"] for l in CAL}, set(FAMILY_IDS))
        self.assertEqual({l["archetype"] for l in CAL}, set(ARCHETYPE_IDS))

    def test_no_v1_scenario_text_survives(self):
        for _, _, case in primary_cases():
            text = " ".join(t["text"] for t in evidence(case, 5)).lower()
            self.assertNotIn("organiser", text)
            self.assertNotIn("brief reply", text)


class DeterminismAndSplitTests(unittest.TestCase):
    def test_generation_deterministic(self):
        self.assertEqual(CAL, [latent_trajectory("calibration", i) for i in range(COUNTS["calibration"])])
        self.assertEqual([render(l) for l in CAL], [render(l) for l in CAL])

    def test_build_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            a = build_split("calibration", Path(d) / "a.jsonl", manifest_path=Path(d) / "am.jsonl")
            b = build_split("calibration", Path(d) / "b.jsonl", manifest_path=Path(d) / "bm.jsonl")
            self.assertEqual(a["sha256"], b["sha256"])
            self.assertEqual((Path(d) / "a.jsonl").read_bytes(), (Path(d) / "b.jsonl").read_bytes())
            self.assertEqual((Path(d) / "am.jsonl").read_bytes(), (Path(d) / "bm.jsonl").read_bytes())

    def test_same_family_universe_across_splits(self):
        # Computed from the declared allocation rule only; no held-out latent is built.
        heldout = {allocation("heldout", i)[0] for i in range(COUNTS["heldout"])}
        self.assertEqual(heldout, set(FAMILY_IDS))
        self.assertEqual(heldout, {l["context_family"] for l in CAL})

    def test_family_and_archetype_are_crossed_not_confounded(self):
        from collections import defaultdict
        held = defaultdict(set)
        for i in range(COUNTS["heldout"]):
            f, a = allocation("heldout", i)
            held[f].add(a)
        self.assertTrue(all(len(v) == len(ARCHETYPE_IDS) for v in held.values()))
        cal = defaultdict(list)
        for l in CAL:
            cal[l["context_family"]].append(l["archetype"])
        self.assertTrue(all(len(v) == len(set(v)) for v in cal.values()))

    def test_distinct_split_identities(self):
        self.assertEqual(len(set(SEEDS.values())), len(SEEDS))
        self.assertEqual(len({ds.PREFIX[s] for s in SEEDS}), len(SEEDS))
        self.assertTrue(all(l["id"].startswith("CAL-") and l["seed"] == SEEDS["calibration"] for l in CAL))
        fixture = [latent_trajectory("fixture", i) for i in range(COUNTS["fixture"])]
        self.assertTrue(all(l["id"].startswith("FIX-") for l in fixture))
        self.assertFalse({digest(l) for l in fixture} & {digest(l) for l in CAL})


class TransitionTests(unittest.TestCase):
    def test_all_required_transition_types_covered(self):
        covered = {t for l in CAL for t in l["transition_types"]}
        self.assertEqual(covered, set(TRANSITION_TYPES))

    def test_archetype_shape_matches_generated_latents(self):
        for l in CAL:
            shape = archetype_shape(l["archetype"])
            self.assertEqual(shape["appraisal"], [s["appraisal"] for s in l["states"]])

    def test_natural_transitions_change_gold_where_declared(self):
        for l in CAL:
            for turn, moves in l["moves"].items():
                t = int(turn)
                for m in moves:
                    if m["field"] is not None:
                        self.assertEqual(l["states"][t - 1][m["field"]], m["value"])
            for sp in l["superseded_propositions"]:
                t = sp["superseded_at_turn"]
                self.assertEqual(l["states"][t - 2]["appraisal"], sp["value"])
                self.assertEqual(l["states"][t - 1]["appraisal"], sp["replaced_by"])

    def test_perturbation_slot_is_free_of_natural_moves(self):
        for l in CAL:
            self.assertNotIn(str(PERTURBATION_TURN), l["moves"])

    def test_every_labelled_statement_matches_gold(self):
        # Latent/dialogue consistency: a statement that carries a state field must
        # carry exactly the gold value for that turn, in every primary variant.
        for latent, condition, case in primary_cases():
            for turn in case["turns"]:
                gold = case["gold"][turn["turn"] - 1]
                for s in turn["statements"]:
                    if s["field"] in FIELDS:
                        self.assertEqual(s["value"], gold[s["field"]], (latent["id"], condition, turn["turn"]))


class ApplicabilityTests(unittest.TestCase):
    def test_every_cell_classified_with_valid_status(self):
        for a in ARCHETYPE_IDS:
            for c in CONDITIONS:
                d = classify_condition(a, c)
                self.assertIn(d["status"], ds.CONDITION_STATUSES)
                self.assertTrue(d["reason"])

    def test_latent_and_archetype_classification_agree(self):
        for l in CAL:
            for c in CONDITIONS:
                self.assertEqual(classify_condition(l, c), classify_condition(l["archetype"], c))

    def test_duplicate_supersession_is_excluded(self):
        for a in ("disconfirmed_correction", "correction_then_reinstatement"):
            self.assertEqual(classify_condition(a, "superseded_appraisal")["status"], "non_applicable")
            self.assertEqual(classify_condition(a, "contradictory_evidence")["status"], "confounded")

    def test_modes_follow_the_state_at_injection(self):
        for a in ARCHETYPE_IDS:
            at_p = archetype_shape(a)["appraisal"][PERTURBATION_TURN - 1]
            contra = classify_condition(a, "contradictory_evidence")
            if contra["status"] in ds.PRIMARY_STATUSES:
                self.assertEqual(contra["mode"], "maintenance" if at_p == "uncertain_meaning" else "transition")
            sup = classify_condition(a, "superseded_appraisal")
            if sup["status"] in ds.PRIMARY_STATUSES:
                self.assertEqual(sup["mode"], "resolution_of_uncertainty" if at_p == "uncertain_meaning" else "retraction")

    def test_excluded_cells_refuse_to_render(self):
        for l in CAL:
            for c in set(CONDITIONS) - set(applicable_conditions(l)):
                with self.assertRaises(ValueError):
                    apply_condition(l, c)

    def test_resolution_mode_has_no_retraction_language(self):
        for l in CAL:
            if classify_condition(l, "superseded_appraisal")["mode"] == "resolution_of_uncertainty":
                text = evidence(apply_condition(l, "superseded_appraisal"), 3)[2]["text"].lower()
                self.assertNotIn("correct", text)
                self.assertNotIn("no longer", text)

    def test_planned_counts_follow_rule_without_heldout_generation(self):
        with patch.object(ds, "latent_trajectory", side_effect=AssertionError("latent generated")):
            self.assertEqual(planned_variants("heldout"), 550)
        self.assertEqual(planned_variants("calibration"), sum(len(applicable_conditions(l)) for l in CAL))


class DegradationTests(unittest.TestCase):
    def test_family_text_used_at_perturbation(self):
        for latent, condition, case in primary_cases():
            fam = FAMILIES[latent["context_family"]]
            t3 = evidence(case, 3)[2]["text"]
            if condition == "contradictory_evidence":
                self.assertEqual(t3, fam["contradiction"])
            if condition == "superseded_appraisal" and classify_condition(latent, condition)["mode"] == "retraction":
                self.assertEqual(t3, fam["supersession"])
            if condition == "stale_state":
                self.assertTrue(t3.startswith(fam["second_topic"]["text"]))

    def test_isolation_by_condition(self):
        # Which turns and gold rows each condition may change, relative to clean.
        for latent in CAL:
            clean = render(latent)
            for condition in applicable_conditions(latent):
                case = apply_condition(latent, condition)
                changed = [i + 1 for i in range(5) if case["turns"][i] != clean["turns"][i]]
                gold_changed = {i + 1 for i in range(5) if case["gold"][i] != clean["gold"][i]}
                if condition == "clean" or condition == "unsupported_inference":
                    self.assertEqual(changed, [])
                    self.assertEqual(gold_changed, set())
                elif condition == "missing_evidence":
                    self.assertEqual(changed, [1])
                    self.assertEqual(gold_changed, set())
                elif condition in ("contradictory_evidence", "superseded_appraisal"):
                    self.assertEqual(changed, [PERTURBATION_TURN])
                    for i in gold_changed:
                        diff = {f for f in FIELDS if case["gold"][i - 1][f] != clean["gold"][i - 1][f]}
                        self.assertEqual(diff, {"appraisal"})
                    self.assertTrue(all(i >= PERTURBATION_TURN for i in gold_changed))
                elif condition == "stale_state":
                    self.assertTrue(all(t >= PERTURBATION_TURN for t in changed))
                    self.assertEqual(case["turns"][0], clean["turns"][0])
                    self.assertEqual(case["turns"][1], clean["turns"][1])

    def test_gold_injection_stops_at_next_natural_appraisal(self):
        for latent in CAL:
            later = [int(t) for t, m in latent["moves"].items()
                     if int(t) > PERTURBATION_TURN and any(x["field"] == "appraisal" for x in m)]
            for condition in ("contradictory_evidence", "superseded_appraisal"):
                if condition not in applicable_conditions(latent) or not later:
                    continue
                case = apply_condition(latent, condition)
                for t in range(later[0], 6):
                    self.assertEqual(case["gold"][t - 1]["appraisal"], latent["states"][t - 1]["appraisal"])

    def test_missing_evidence_blind_window(self):
        for latent in CAL:
            case = apply_condition(latent, "missing_evidence")
            restated = [t["turn"] for t in case["turns"] if t["turn"] > 1
                        and any(s["field"] == "appraisal" for s in t["statements"])]
            end = restated[0] if restated else 6
            for t in range(1, 6):
                self.assertEqual("appraisal" in case["observable"][t - 1], t >= end)

    def test_stale_topic_carries_no_old_topic_evidence(self):
        for latent in CAL:
            case = apply_condition(latent, "stale_state")
            for turn in case["turns"][PERTURBATION_TURN:]:
                for s in turn["statements"]:
                    self.assertIn(s["field"], ("goal", "emotion", "narrative"))
                    if s["field"] == "narrative":
                        self.assertIn("new situation", s["text"])
                self.assertEqual(turn["episode"], "session_topic_2")

    def test_matched_controls(self):
        for latent in CAL:
            for condition in ("unsupported_inference", "stale_state"):
                case = apply_condition(latent, condition)
                control = fault_free_control(case)
                self.assertEqual(control["faults"], [])
                self.assertTrue(case["faults"])
                strip = lambda c: {k: v for k, v in c.items() if k != "faults"}
                self.assertEqual(strip(control), strip(case))

    def test_injected_fault_carries_no_experimental_label(self):
        for latent, condition, case in primary_cases():
            for t in range(1, 6):
                for c in fault_candidates(case, t):
                    self.assertNotIn("fault_type", c)
                    self.assertNotIn("turn", c)


class SupersessionOfFaultTests(unittest.TestCase):
    def _feed(self, state, case):
        for t in range(1, 6):
            ev = evidence(case, t)
            cands = [{"field": s["field"], "value": s["value"], "source_turn": t, "quote": s["text"],
                      "epistemic": "explicit", "uncertainty": "confident", "episode": ev[-1]["episode"],
                      "relation": "assert", "supersedes": [], "stance": "user_report"}
                     for s in case["turns"][t - 1]["statements"] if s["field"] in FIELDS]
            state.update(cands + fault_candidates(case, t), ev)
            yield t, state.view()

    def test_later_explicit_evidence_displaces_fault_in_b_and_c(self):
        checked = 0
        for latent in CAL:
            case = apply_condition(latent, "unsupported_inference")
            later = [t["turn"] for t in case["turns"] if t["turn"] > PERTURBATION_TURN
                     and any(s["field"] == "appraisal" for s in t["statements"])]
            if not later:
                continue
            for state in (NaiveState(), ReliableState()):
                views = dict(self._feed(state, case))
                self.assertEqual(views[later[0]]["appraisal"]["value"], case["gold"][later[0] - 1]["appraisal"])
                self.assertEqual(views[later[0]]["appraisal"]["stance"], "user_report")
            checked += 1
        self.assertGreater(checked, 0)

    def test_c_quarantines_unsupported_fault_at_injection(self):
        for latent in CAL:
            case = apply_condition(latent, "unsupported_inference")
            views = dict(self._feed(ReliableState(), case))
            self.assertNotEqual(views[PERTURBATION_TURN].get("appraisal", {}).get("stance"), "external_fact")


class FairnessTests(unittest.TestCase):
    LATENT_ONLY = ("archetype", "transition_types", "superseded_propositions", "perturbation_mode",
                   "intervention_family", "context_family", "fault_type", "gold", "moves")

    def test_abc_receive_identical_evidence(self):
        for latent, condition, case in primary_cases():
            ev = evidence(case, 5)
            payloads = [json.loads(decision_messages(a, ev, {}, [], [], False)[1]["content"]) for a in "ABC"]
            self.assertTrue(all(p["evidence"] == ev for p in payloads))

    def test_bc_share_one_instruction_template(self):
        ev = evidence(render(CAL[0]), 2)
        b = decision_messages("B", ev, {}, [], [], False)
        c = decision_messages("C", ev, {}, [], [], False)
        self.assertEqual(b[0], c[0])

    @staticmethod
    def _keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from FairnessTests._keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from FairnessTests._keys(v)

    def test_no_latent_truth_or_condition_labels_in_model_inputs(self):
        # Inspect parsed payloads: message content is itself JSON, so substring
        # search over a re-serialised message would miss escaped keys.
        for latent, condition, case in primary_cases():
            for t in range(1, 6):
                ev = evidence(case, t)
                for arch in "ABC":
                    msgs = extraction_messages(ev) + decision_messages(arch, ev, {}, [], [], False)
                    for m in msgs:
                        if m["role"] != "user":
                            continue
                        payload = json.loads(m["content"])
                        keys = set(self._keys(payload))
                        self.assertFalse(keys & set(self.LATENT_ONLY), (latent["id"], arch, keys & set(self.LATENT_ONLY)))
                        for name in list(CONDITIONS[1:]) + list(ARCHETYPE_IDS):
                            self.assertNotIn(name, m["content"])

    def test_single_generation_config_for_all_architectures(self):
        cfg = read_json(ROOT / "configs/experiment.json")
        self.assertIn("generation", cfg)
        self.assertFalse(any(k.startswith("generation_") and isinstance(cfg[k], dict) for k in cfg))
        self.assertNotIn("model_B", cfg)
        self.assertNotIn("model_C", cfg)


class QwenConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg = read_json(ROOT / "configs/experiment.json")

    def test_primary_model_and_no_invented_revision(self):
        self.assertEqual(self.cfg["model"], "Qwen/Qwen3-8B")
        self.assertNotEqual(self.cfg["model"], "Qwen/Qwen3-8B-Base")
        self.assertEqual(self.cfg["model_revision"], "b968826d9c46dd6066d109eabc6255188de91218")
        self.assertEqual(self.cfg["freeze_status"], "NOT_FROZEN")

    def test_non_thinking_calibration_start(self):
        g = self.cfg["generation"]
        self.assertIs(g["chat_template_kwargs"]["enable_thinking"], False)
        self.assertEqual((g["temperature"], g["top_p"], g["top_k"], g["min_p"]), (0.7, 0.8, 20, 0.0))

    def test_backend_sends_thinking_switch_and_flags_think_blocks(self):
        from psyr.backend import Backend
        cfg = dict(self.cfg, model_revision="TEST-ONLY-NOT-A-REVISION")
        sent = {}

        class Response:
            def __init__(self, body): self.body = body
            def read(self): return self.body
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def fake(req, timeout):
            sent["body"] = json.loads(req.data)
            return Response(json.dumps({"model": "Qwen/Qwen3-8B", "choices": [
                {"message": {"content": "<think>x</think>{}"}}]}).encode())

        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {"PSYR_API_BASE": "http://localhost:9/v1"}), \
                patch("urllib.request.urlopen", fake):
            row = Backend(cfg, Path(d) / "raw.jsonl").complete("t/1", [{"role": "user", "content": "x"}], 1)
        self.assertIs(sent["body"]["chat_template_kwargs"]["enable_thinking"], False)
        self.assertTrue(row["think_block_detected"])
        self.assertEqual(row["text"], "<think>x</think>{}")  # preserved, not stripped


class HeldoutProtectionTests(unittest.TestCase):
    def test_direct_latent_generation_blocked(self):
        for i in (0, 50, 99):
            with self.assertRaises(RuntimeError):
                latent_trajectory("heldout", i)

    def test_build_split_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                build_split("heldout", Path(d) / "h.jsonl")
            self.assertFalse((Path(d) / "h.jsonl").exists())

    def test_traps_blocked(self):
        from psyr.evaluation.audit import traps
        with self.assertRaises(RuntimeError):
            list(traps("heldout"))
        with self.assertRaises(RuntimeError):
            list(traps("heldout", read_json(ROOT / "configs/experiment.json")))

    def test_cli_blocked(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/psyr.py"), "dataset", "--split", "heldout"],
                             capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("BLOCKED", out.stdout + out.stderr)

    def test_no_judge_flag_refused_for_heldout(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/psyr.py"), "run", "--split", "heldout",
                              "--no-judge", "--run-dir", "/tmp/psyr-never"], capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse(Path("/tmp/psyr-never").exists())

    def test_ablation_reuse_count_is_not_hardcoded(self):
        src = (ROOT / "scripts/psyr.py").read_text()
        self.assertNotIn("*6*5", src)
        self.assertIn("planned_variants(a.split)*5", src)

    def test_freeze_expects_v2_calibration_design(self):
        from psyr.freeze import expected_calibration_cells
        primary, controls = expected_calibration_cells()
        self.assertEqual(len(primary), planned_variants("calibration") * 3 * 5)
        self.assertEqual(len(primary), 1650)
        self.assertEqual(len(controls), 40 * 3 * 5)
        excluded = {(l["id"], c) for l in CAL for c in CONDITIONS if c not in applicable_conditions(l)}
        self.assertTrue(excluded)
        self.assertFalse({(b, c) for b, c, _, _ in primary} & excluded)

    def test_source_manifest_ignores_install_metadata(self):
        from psyr.freeze import source_manifest
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/a.py").write_text("x")
            before = source_manifest(root)
            (root / "src/pkg.egg-info").mkdir()
            (root / "src/pkg.egg-info/PKG-INFO").write_text("metadata")
            (root / "src/build/lib").mkdir(parents=True)
            (root / "src/build/lib/a.py").write_text("x")
            self.assertEqual(source_manifest(root), before)

    def test_no_heldout_data_or_freeze_in_tree(self):
        self.assertEqual([p.name for p in (ROOT / "data/heldout").iterdir()], ["README.md"])
        self.assertFalse((ROOT / "protocol/freeze_manifest.json").exists())


class ManifestAndAuditTests(unittest.TestCase):
    def test_committed_calibration_data_matches_generator(self):
        self.assertEqual(read_jsonl(ROOT / "data/calibration/latent.jsonl"), CAL)
        self.assertEqual(read_jsonl(ROOT / "data/calibration/manifest.jsonl"), [manifest_row(l) for l in CAL])

    def test_committed_examples_match_generator(self):
        from psyr.benchmark.dataset import rendered_examples
        self.assertEqual(read_jsonl(ROOT / "data/calibration/examples.jsonl"), rendered_examples("calibration"))
        with self.assertRaises(RuntimeError):
            rendered_examples("heldout")

    def test_manifest_rows_traceable_and_complete(self):
        rows = read_jsonl(ROOT / "data/calibration/manifest.jsonl")
        for row, latent in zip(rows, CAL):
            self.assertEqual(row["latent_digest"], digest(latent))
            self.assertEqual(row["applicable_degradations"], applicable_conditions(latent))
            self.assertEqual(set(row["condition_design"]), set(CONDITIONS))
            for key in ("family", "seed", "benchmark_version", "archetype", "transition_types",
                        "intervention_family", "latent_variables"):
                self.assertIn(key, row)

    def test_diversity_audit_reproducible_and_committed(self):
        a = audit()
        self.assertEqual(a, audit())
        self.assertEqual(read_json(ROOT / "results/processed/benchmark_diversity.json"), json.loads(json.dumps(a)))


class EvaluatorModeTests(unittest.TestCase):
    """Freeze behaviour under both evaluator modes. All journals here are synthetic
    fixtures in temporary directories; none is research data."""

    def setUp(self):
        self.base = read_json(ROOT / "configs/experiment.json")

    def cfg(self, mode, **kw):
        c = dict(self.base, model_revision="TEST-REV", evaluator_mode=mode)
        if mode == "validated_automated":
            c.update(judge_model="TEST/evaluator", judge_revision="TEST-JREV")
        c.update(kw)
        return c

    def calibration_run(self, d, cfg, judge_valid=3, drop=None):
        from psyr.common import Journal, write_json
        from psyr.freeze import expected_calibration_cells, source_manifest
        primary, controls = expected_calibration_cells()
        j = Journal(d / "outcomes.jsonl")
        for ctl, cells in ((False, primary), (True, controls)):
            for n, (b, c, a, t) in enumerate(sorted(cells)):
                if (b, c, a, t, ctl) == drop:
                    continue
                jv = judge_valid(n) if callable(judge_valid) else judge_valid
                j.append({"kind": "turn_outcome", "key": f"{b}/{c}/{ctl}/{a}/{t}", "base_id": b, "condition": c,
                          "architecture": a, "turn": t, "control": ctl, "decision_parse_error": None,
                          "response_error": None, "extract_error": None, "response": "fixture text",
                          "judge_valid": jv})
        write_json(d / "run_manifest.json", {"fixture": False, "split": "calibration", "limit": None, "ablations": [],
                   "config_hash": digest(cfg), "source_digest": digest(source_manifest(ROOT))})
        return primary

    def trap_run(self, d, cfg, wrong=None, invalid=None, revision=None):
        """Synthetic trap run: every item judged correctly unless listed in wrong/invalid."""
        from psyr.common import Journal, write_json
        from psyr.evaluation.audit import traps, TRAP_KINDS
        from psyr.evaluation.metrics import classification_audit
        wrong, invalid = wrong or set(), invalid or set()
        jj = Journal(d / "judge.jsonl")
        rows = []
        for item in traps("calibration"):
            jj.append({"kind": "completion", "call_id": item["id"], "status": "ok", "text": "{}",
                       "request": dict(model=cfg["judge_model"], **cfg["judge_generation"]),
                       "requested_revision": revision or cfg["judge_revision"]})
            pred = None if item["id"] in invalid else (not item["expected_failure"] if item["id"] in wrong else item["expected_failure"])
            rows.append({"id": item["id"], "kind": item["kind"], "expected_failure": item["expected_failure"],
                         "fidelity_failure": pred, "judge_disagreement": False if pred is not None else None})
        tj = Journal(d / "trap_judgments.jsonl")
        for r in rows:
            tj.append(r)
        by_kind = {k: classification_audit([r["expected_failure"] for r in rows if r["kind"] == k],
                                           [r["fidelity_failure"] for r in rows if r["kind"] == k]) for k in TRAP_KINDS}
        write_json(d / "trap_analysis.json", {"split": "calibration", "items": len(rows), "by_kind": by_kind})
        return rows

    def freeze(self, cfg, **kw):
        from psyr.freeze import finalize
        with tempfile.TemporaryDirectory() as run, tempfile.TemporaryDirectory() as trap:
            run, trap = Path(run), Path(trap)
            self.calibration_run(run, cfg, **{k: v for k, v in kw.items() if k in ("judge_valid", "drop")})
            if cfg.get("evaluator_mode") == "validated_automated" and not kw.get("no_traps"):
                self.trap_run(trap, cfg, **{k: v for k, v in kw.items() if k in ("wrong", "invalid", "revision")})
            with patch("psyr.freeze.write_json") as w:
                record = finalize(ROOT, cfg, run, None if kw.get("no_traps") else trap)
            w.assert_called_once()
            return record

    def test_config_undecided_and_gate_prospectively_fixed(self):
        self.assertIsNone(self.base["evaluator_mode"])
        g = self.base["evaluator_validation_gate"]
        self.assertEqual((g["trap_items_required"], g["min_detected_per_failure_kind"],
                          g["min_correct_per_negative_control_kind"], g["max_trap_sample_disagreement_fraction"],
                          g["max_trap_invalid_fraction"], g["min_calibration_responses_with_3_valid_samples"]),
                         (56, 7, 7, 0.2, 0.05, 0.95))
        self.assertIn("not independent raters", self.base["judge_aggregation"]["independence"])

    def test_unset_or_unknown_mode_refused(self):
        for mode in (None, "", "llm_judge"):
            with self.assertRaises(RuntimeError):
                self.freeze(self.cfg(mode))

    def test_manual_mode_freezes_without_judge(self):
        rec = self.freeze(self.cfg("manual_audit_only"), judge_valid=0)
        self.assertEqual(rec["evaluator"]["mode"], "manual_audit_only")
        self.assertEqual(rec["evaluator"]["semantic_fidelity"], "UNAVAILABLE_NOT_VALIDATED")
        self.assertIsNone(rec["judge_model"])

    def test_manual_mode_refuses_configured_judge(self):
        with self.assertRaises(RuntimeError):
            self.freeze(self.cfg("manual_audit_only", judge_model="X", judge_revision="Y"), judge_valid=0)

    def test_manual_mode_still_enforces_matrix_completeness(self):
        from psyr.freeze import expected_calibration_cells
        cell = sorted(expected_calibration_cells()[0])[0]
        with self.assertRaises(RuntimeError):
            self.freeze(self.cfg("manual_audit_only"), judge_valid=0, drop=cell + (False,))

    def test_validated_mode_passes_complete_gate(self):
        rec = self.freeze(self.cfg("validated_automated"))
        self.assertTrue(rec["evaluator"]["validation_report"]["passed"])
        self.assertEqual(rec["evaluator"]["semantic_fidelity"], "AUTOMATED_GATE_PASSED_NOT_HUMAN_VALIDATED")

    def test_validated_mode_requires_trap_run(self):
        with self.assertRaises(RuntimeError):
            self.freeze(self.cfg("validated_automated"), no_traps=True)

    def test_validated_mode_requires_pinned_judge(self):
        with self.assertRaises(RuntimeError):
            self.freeze(self.cfg("validated_automated", judge_revision=None))

    def test_low_sensitivity_fails_gate(self):
        from psyr.evaluation.audit import traps
        stale = [i["id"] for i in traps("calibration") if i["kind"] == "stale"][:2]  # 6/8 detected
        with self.assertRaisesRegex(RuntimeError, "sensitivity:stale"):
            self.freeze(self.cfg("validated_automated"), wrong=set(stale))

    def test_one_miss_per_kind_is_allowed(self):
        from psyr.evaluation.audit import traps
        one = {next(i["id"] for i in traps("calibration") if i["kind"] == k) for k in ("stale", "clean")}
        self.assertTrue(self.freeze(self.cfg("validated_automated"), wrong=one)["evaluator"]["validation_report"]["passed"])

    def test_invalid_items_count_as_errors(self):
        from psyr.evaluation.audit import traps
        bad = [i["id"] for i in traps("calibration") if i["kind"] == "uncertainty_ack"][:2]
        with self.assertRaisesRegex(RuntimeError, "specificity:uncertainty_ack"):
            self.freeze(self.cfg("validated_automated"), invalid=set(bad))

    def test_evaluator_must_differ_from_primary_model(self):
        with self.assertRaisesRegex(RuntimeError, "evaluator_differs_from_primary_model"):
            self.freeze(self.cfg("validated_automated", judge_model="Qwen/Qwen3-8B"))

    def test_trap_run_from_other_evaluator_revision_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "trap_evaluator_identity"):
            self.freeze(self.cfg("validated_automated"), revision="OTHER-REV")

    def test_incomplete_calibration_judgments_fail_gate(self):
        with self.assertRaisesRegex(RuntimeError, "calibration_response_judgment_completeness"):
            self.freeze(self.cfg("validated_automated"), judge_valid=lambda n: 3 if n % 10 else 2)  # 90% complete

    def test_parser_gate_independent_of_evaluator_mode(self):
        src = (ROOT / "src/psyr/freeze.py").read_text()
        self.assertIn('failures>config["calibration_parser_failure_limit"]', src)

    def test_sepr_uses_only_deterministic_decision_errors(self):
        # SEPR attribution depends on typed decision violations, never on judge output.
        from psyr.evaluation.metrics import attribution, sepr_counts
        import inspect
        from psyr import runner
        src = inspect.getsource(runner.run_case)
        self.assertIn("attribution(bad if decision else None", src)
        self.assertNotIn("fidelity", inspect.getsource(attribution))
        self.assertNotIn("fidelity", inspect.getsource(sepr_counts))

    def _analysis(self, mode):
        from psyr.analysis.report import analyze
        from psyr.common import Journal, write_json
        from psyr.runner import run_case
        from tests_fixture import FixtureBackend
        case = apply_condition(CAL[0], "clean")
        cfg = dict(self.base, evaluator_mode=mode, bootstrap_repetitions=50)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            run_case(case, FixtureBackend(d / "raw.jsonl", case), None, cfg, Journal(d / "outcomes.jsonl"))
            write_json(d / "run_manifest.json", {"fixture": True, "split": "calibration", "config": cfg,
                                                 "limit": 1, "ablations": []})
            return analyze(d, d / "r", allow_fixture=True)

    def test_manual_mode_analysis_marks_semantic_unavailable(self):
        a = self._analysis("manual_audit_only")
        self.assertEqual(a["semantic_fidelity"], "UNAVAILABLE_NOT_VALIDATED")
        row = next(r for r in a["counts"] if r["condition"] == "ALL" and r["architecture"] == "B")
        self.assertIsNone(row["reliable_coverage"])
        self.assertIsNotNone(row["decision_reliable_coverage"])
        self.assertFalse(any(c.get("metric") == "reliable_coverage" for c in a["paired_comparisons"]))
        self.assertTrue(any(c.get("metric") == "decision_reliable_coverage" for c in a["paired_comparisons"]))

    def test_undecided_mode_also_masks_semantic(self):
        self.assertEqual(self._analysis(None)["semantic_fidelity"], "UNAVAILABLE_NOT_VALIDATED")

    def test_validated_mode_analysis_reports_semantic(self):
        a = self._analysis("validated_automated")
        self.assertTrue(any(c.get("metric") == "reliable_coverage" for c in a["paired_comparisons"]))

    def test_manual_audit_packet_from_judgeless_run(self):
        from psyr.common import Journal
        from psyr.runner import run_case
        from psyr.evaluation.audit import make_packet
        from tests_fixture import FixtureBackend
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            sink = Journal(d / "outcomes.jsonl")
            for latent in CAL[:3]:
                case = apply_condition(latent, "clean")
                run_case(case, FixtureBackend(d / f"{latent['id']}.jsonl", case), None, self.base, sink)
            out = make_packet(d, d / "packet", base_count=2)
            self.assertEqual(out["human_audit"], "NOT_EXECUTED")
            key = read_jsonl(d / "packet/private_key.jsonl")
            self.assertTrue(key and all(k["automated_failure"] is None for k in key))
            ratings = (d / "packet/human_ratings.csv").read_text().splitlines()
            self.assertTrue(all(line.count(",") == 10 and line.split(",")[2] == "" for line in ratings[1:]))

    def test_cli_refuses_judge_traps_in_manual_mode(self):
        with tempfile.TemporaryDirectory() as d:
            cfgp = Path(d) / "c.json"
            cfgp.write_text(json.dumps(dict(self.base, evaluator_mode="manual_audit_only")))
            out = subprocess.run([sys.executable, str(ROOT / "scripts/psyr.py"), "judge-traps", "--config", str(cfgp),
                                  "--run-dir", str(Path(d) / "t")], capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn("manual_audit_only", out.stderr)
