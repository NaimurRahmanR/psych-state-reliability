"""Degradation conditions.

V2 change: degradation text is drawn from the trajectory's scenario family rather
than from a single hardcoded organiser/brief-reply scenario, and gold propagation
now stops at the trajectory's next natural appraisal transition instead of
overwriting the remainder of the trajectory.
"""
import copy
from psyr.benchmark.dataset import (CONDITIONS, PERTURBATION_TURN, phrase, render,
                                    applicable_conditions, classify_condition)
from psyr.benchmark.families import FAMILIES


def _natural_appraisal_turns(latent):
    return sorted(int(t) for t, moves in latent["moves"].items()
                  if any(m["field"] == "appraisal" for m in moves))


def _appraisal_statement_turns(case):
    return [t["turn"] for t in case["turns"] if any(s["field"] == "appraisal" for s in t["statements"])]


def apply_condition(latent, condition):
    if condition not in CONDITIONS:
        raise ValueError(condition)
    design = classify_condition(latent, condition)
    if condition not in applicable_conditions(latent):
        raise ValueError(f"{condition} is {design['status']} for {latent['id']}: {design['reason']}")
    case = render(latent)
    case["condition"] = condition
    family = FAMILIES[latent["context_family"]]
    p = PERTURBATION_TURN

    if condition == "missing_evidence":
        # Remove only the initial appraisal sentence. Appraisal becomes unobservable
        # for scoring until the trajectory next states an appraisal explicitly.
        case["turns"][0]["statements"] = [s for s in case["turns"][0]["statements"] if s["field"] != "appraisal"]
        later = [t for t in _appraisal_statement_turns(case) if t > 1]
        blind_until = later[0] if later else 6
        for turn_index in range(blind_until - 1):
            if "appraisal" in case["observable"][turn_index]:
                case["observable"][turn_index].remove("appraisal")

    elif condition in ("contradictory_evidence", "superseded_appraisal"):
        value = "uncertain_meaning" if condition == "contradictory_evidence" else "situational_explanation"
        if condition == "contradictory_evidence":
            text = family["contradiction"]
        elif design["mode"] == "resolution_of_uncertainty":
            # The user never committed to a negative reading, so retraction language
            # ("I no longer read it as a judgment") would presuppose a state that never
            # existed. Use the family's own definite reinterpretation instead.
            text = phrase("appraisal", value, latent["wording_variant"], latent["context_family"])
        else:
            text = family["supersession"]
        case["turns"][p - 1]["statements"] = [{"field": "appraisal", "value": value, "text": text}]
        # Hold the injected value only until the trajectory's own next appraisal move.
        nxt = [t for t in _natural_appraisal_turns(latent) if t > p]
        stop = nxt[0] if nxt else 6
        for turn_index in range(p - 1, stop - 1):
            case["gold"][turn_index]["appraisal"] = value

    elif condition == "unsupported_inference":
        # Same deliberately corrupted candidate for B and C, not a hidden true fact.
        case["faults"] = [{"turn": p, "field": "appraisal", "value": "negative_judgment",
                           "source_turn": p, "quote": "", "epistemic": "inferred", "uncertainty": "confident",
                           "episode": latent["episode"], "relation": "assert", "supersedes": [],
                           "fault_type": "unsupported_inference", "stance": "external_fact"}]

    elif condition == "stale_state":
        # The topic change is shared evidence for every architecture. The sole
        # intended fault is replay of an old appraisal; `fault_free_control`
        # generates the matched topic-change control.
        topic = family["second_topic"]
        case["turns"][p - 1]["statements"] = [
            {"field": "context", "value": "new_activity", "text": topic["text"] + " Please keep my stated support goal."},
            {"field": "emotion", "value": latent["states"][p - 1]["emotion"],
             "text": phrase("emotion", latent["states"][p - 1]["emotion"], latent["wording_variant"],
                            latent["context_family"])}]
        for i in range(p - 1, 5):
            case["turns"][i]["episode"] = "session_topic_2"
            case["gold"][i].update(context="new_activity", appraisal="unknown",
                                   previous_intervention="none", response_to_intervention="not_tried")
            case["observable"][i] = ["context", "emotion", "goal"]
        # Later natural statements belong to the old topic. Only the user's support
        # goal and self-reported emotion carry across; old-topic narrative evidence
        # and "same issue" filler are removed so they cannot support the old appraisal.
        for i in range(p, 5):
            kept = [s for s in case["turns"][i]["statements"] if s["field"] in ("goal", "emotion")]
            case["turns"][i]["statements"] = kept or [
                {"field": "narrative", "value": None,
                 "text": "I am checking in about the new situation; there is no new information today."}]
        prior = next(s for s in case["turns"][0]["statements"] if s["field"] == "appraisal")
        case["faults"] = [{"turn": p, "field": "appraisal", "value": prior["value"], "source_turn": 1,
                           "quote": prior["text"], "epistemic": "explicit", "uncertainty": "confident",
                           "episode": latent["episode"], "relation": "assert", "supersedes": [],
                           "fault_type": "stale_state", "stance": "user_report"}]
    return case


def fault_free_control(case):
    control = copy.deepcopy(case)
    control["faults"] = []
    return control


def fault_candidates(case, turn):
    # Drop experimental labels before the architecture sees a fault.
    return [{k: v for k, v in f.items() if k not in ("turn", "fault_type")}
            for f in case["faults"] if f["turn"] == turn]


def history_fault_notes(case, turn):
    return [{"turn": f["turn"], "role": "assistant_memory_note",
             "text": f"Earlier assistant interpretation (may be mistaken): {f['field']}={f['value']}; "
                     f"stance={f['stance']}; originating topic={f['episode']}.",
             "source_turn": f["source_turn"]} for f in case["faults"] if f["turn"] <= turn]
