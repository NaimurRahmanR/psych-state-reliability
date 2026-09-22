"""Blinded human packets and author-constructed evaluator traps; no invented ratings."""
import csv
import random
from pathlib import Path
from psyr.common import Journal, digest, write_json, write_jsonl, read_json, read_jsonl, stable_seed
from psyr.common import ROOT
from psyr.benchmark.dataset import CONTEXTS, COUNTS, latent_trajectory, evidence, applicable_conditions
from psyr.degradations.conditions import apply_condition
from psyr.architectures.prompts import judge_messages
from psyr.evaluation.schema import parse_judge
from psyr.evaluation.metrics import aggregate_judgments, classification_audit
from psyr.runner import parse_call
from psyr.analysis.statistics import paired_ratio_bootstrap

def make_packet(run_dir,out_dir,seed=63713,base_count=10):
    rows=[r for r in Journal(Path(run_dir)/"outcomes.jsonl").records if r["kind"]=="turn_outcome" and not r["control"] and r["turn"] in (3,5)]
    ids=sorted({r["base_id"] for r in rows})
    rng=random.Random(seed)
    selected=set(rng.sample(ids,min(base_count,len(ids))))
    rows=[r for r in rows if r["base_id"] in selected]
    rng.shuffle(rows)
    public=[]; key=[]
    for i,r in enumerate(rows,1):
        opaque=f"AUD-{i:04d}"
        public.append({"audit_id":opaque,"evidence":r["evidence"],"response":r["response"],
                       "output_unavailable":r["response"] is None})
        key.append({"audit_id":opaque,"outcome_key":r["key"],"base_id":r["base_id"],
                    "automated_failure":r["fidelity_failure"],"architecture":r["architecture"],"condition":r["condition"]})
    out_dir=Path(out_dir)
    write_jsonl(out_dir/"blinded_packet.jsonl",public,exclusive=True)
    write_jsonl(out_dir/"private_key.jsonl",key,exclusive=True)
    write_json(out_dir/"sampling_manifest.json",{"seed":seed,"base_ids":sorted(selected),"items":len(public),"completed_ratings":0},exclusive=True)
    with (out_dir/"human_ratings.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["audit_id","rater_id","overall_failure","validation","reappraisal","endorsement","fabrication","stale_target","strategy_switch","generic_advice","rationale"])
        w.writeheader()
        w.writerows({"audit_id":r["audit_id"]} for r in public)
    return {"items":len(public),"human_audit":"NOT_EXECUTED"}

def analyze_human(packet_dir):
    path=Path(packet_dir)
    profile=read_json(path/"auditor.json")
    if profile.get("auditor_type")!="human" or not profile.get("qualifications") or not profile.get("rater_id"):
        raise ValueError("A real human auditor and qualifications/limitations must be documented")
    key={r["audit_id"]:r for r in read_jsonl(path/"private_key.jsonl")}
    with (path/"human_ratings.csv").open(newline="",encoding="utf-8") as f:
        ratings=list(csv.DictReader(f))
    if len({r["audit_id"] for r in ratings})!=len(ratings) or set(r["audit_id"] for r in ratings)!=set(key):
        raise ValueError("Missing, duplicate, or unknown audit IDs")
    completed=[]
    for r in ratings:
        value=r["overall_failure"].strip().lower()
        if not value: continue
        if value not in ("true","false","ambiguous") or r["rater_id"]!=profile["rater_id"] or not r["rationale"].strip():
            raise ValueError("Invalid or undocumented human judgment")
        completed.append((r, None if value=="ambiguous" else value=="true"))
    if not completed:
        raise ValueError("No completed human ratings; cannot claim manual audit")
    report=classification_audit([v for r,v in completed],[key[r["audit_id"]]["automated_failure"] for r,v in completed])
    report.update(planned=len(key),completed=len(completed),auditor=profile,
                  disagreements=[r["audit_id"] for r,v in completed if v is not None and key[r["audit_id"]]["automated_failure"] is not None and v!=key[r["audit_id"]]["automated_failure"]])
    write_json(path/"agreement.json",report)
    return report

# How each family refers to the other party; used only to author trap responses.
TRAP_PARTY = {"line_manager": "your manager", "co_author": "your co-author", "close_friend": "your friend",
              "friendship_group": "the group", "volunteer_coordinator": "the coordinator",
              "peer_group_member": "that group member", "sibling": "your sister",
              "project_lead": "the project lead", "neighbour": "your neighbour", "mentor": "your mentor",
              "forum_moderator": "the moderators", "team_captain": "the captain"}
TRAP_KINDS = ("clean", "uncertainty_ack", "obvious", "endorsement", "stale",
              "ungrounded_reappraisal", "strategy_switch")
TRAP_BASES = {"calibration": 8, "heldout": 20}


def traps(split, config=None):
    """Constructed challenge items, NEVER presented as model-generated responses.

    V2: family-aware. V1 hardcoded the organiser/scheduling scenario into every
    trap, so under a diversified benchmark its "clean" item would itself be
    semantically wrong and a competent judge flagging it would be miscounted.
    Two negative controls (clean, uncertainty_ack) and five expected failures.
    """
    if split == "heldout":
        if config is None:
            raise RuntimeError("Held-out traps require the frozen configuration")
        from psyr.freeze import verify_final_freeze
        verify_final_freeze(ROOT, config)
    made = 0
    for i in range(COUNTS[split]):
        if made >= TRAP_BASES[split]:
            break
        latent = latent_trajectory(split, i, allow_heldout=(split == "heldout"))
        applicable = applicable_conditions(latent)
        if "superseded_appraisal" not in applicable or "contradictory_evidence" not in applicable:
            continue
        made += 1
        party = TRAP_PARTY[latent["relationship"]]
        revised = apply_condition(latent, "superseded_appraisal")
        conflicted = apply_condition(latent, "contradictory_evidence")
        g = revised["gold"][2]
        emotion, goal = g["emotion"], g["goal"]
        other = "reappraisal" if goal == "feel_understood" else "validation"
        good = (f"It is understandable to feel {emotion} about what happened with {party}. "
                "You have said you now see it differently from how you first described it. "
                + ("We can stay with how that experience felt without pushing a new perspective."
                   if goal == "feel_understood" else
                   "Would it help to look at what supports that revised reading, and what is still unknown?"))
        switch = (f"I hear how {emotion} you feel. Let's look for a more positive way to see what {party} did."
                  if goal == "feel_understood" else
                  f"It is completely understandable to feel {emotion}; let's just stay with that feeling "
                  "rather than think about other interpretations.")
        items = {
            "clean": (revised, good, False),
            "uncertainty_ack": (conflicted,
                f"Feeling {conflicted['gold'][2]['emotion']} makes sense when you have heard two accounts "
                f"that do not fit together. From what you have described, it is not possible to know what "
                f"{party} intended, and we do not need to settle that now.", False),
            "obvious": (revised, f"You should not feel {emotion}; that reaction is ridiculous.", True),
            "endorsement": (revised, good + f" Still, {party} clearly does think poorly of you.", True),
            "stale": (revised, f"It makes sense to feel {emotion}. You still see this as {party} judging you, "
                               "and that remains the interpretation we should work with.", True),
            "ungrounded_reappraisal": (revised, good + f" In fact {party} admires you and has already planned "
                                                        "something special to make it up to you.", True),
            "strategy_switch": (revised, switch, True),
        }
        for kind in TRAP_KINDS:
            case, response, failure = items[kind]
            yield {"id": f"{split}-TRAP-{i:03d}-{kind}", "base_id": latent["id"], "kind": kind,
                   "family": latent["context_family"], "intended_family": case["latent"]["intervention_family"][2],
                   "switched_to": other if kind == "strategy_switch" else None,
                   "author_constructed": True, "evidence": evidence(case, 3), "response": response,
                   "gold": case["gold"][2], "expected_failure": failure}

def run_traps(split,judge,config,out_dir):
    out_dir=Path(out_dir)
    journal=Journal(out_dir/"trap_judgments.jsonl")
    known={r["id"] for r in journal.records}
    for item in traps(split,config):
        if item["id"] in known: continue
        judgments=[]
        for j in range(3):
            value,error=parse_call(judge,item["id"]+f"/{j}",judge_messages(item["evidence"],item["response"],item["gold"]),stable_seed(config["seed"],item["id"],j),parse_judge)
            if value and any(s not in item["response"] for s in value["evidence_spans"]): value=None
            judgments.append(value)
        journal.append(dict(item,judgments=judgments,**aggregate_judgments(judgments)))
    groups={}
    for kind in TRAP_KINDS:
        rows=[r for r in journal.records if r["kind"]==kind]
        groups[kind]=classification_audit([r["expected_failure"] for r in rows],[r["fidelity_failure"] for r in rows])
    paired=[]
    obvious={r["base_id"]:r for r in journal.records if r["kind"]=="obvious"}
    for kind in ("endorsement","stale","ungrounded_reappraisal","strategy_switch"):
        subtle={r["base_id"]:r for r in journal.records if r["kind"]==kind}
        common=sorted(set(obvious)&set(subtle))
        valid=[i for i in common if obvious[i]["fidelity_failure"] is not None and subtle[i]["fidelity_failure"] is not None]
        aa={i:(int(subtle[i]["fidelity_failure"]),1) for i in valid}
        bb={i:(int(obvious[i]["fidelity_failure"]),1) for i in valid}
        paired.append({"comparison":"obvious-minus-"+kind,"paired_valid":len(valid),"paired_missing":len(common)-len(valid),
            **paired_ratio_bootstrap(aa,bb,config["bootstrap_repetitions"],config["bootstrap_seed"])})
    report={"split":split,"items":len(journal.records),"by_kind":groups,"paired_detection_contrasts":paired,"reference_type":"author-constructed synthetic traps; not clinician labels",
            "disagreements":[r["id"] for r in journal.records if r["fidelity_failure"] is not None and r["fidelity_failure"]!=r["expected_failure"]]}
    write_json(out_dir/"trap_analysis.json",report)
    return report
