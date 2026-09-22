from __future__ import annotations
import copy
import random
from psyr.common import digest, write_jsonl
from psyr.benchmark.families import FAMILIES, FAMILY_IDS

BENCHMARK_VERSION = "v2"

FIELDS = ("context", "appraisal", "emotion", "goal", "previous_intervention", "response_to_intervention")

# Public activity labels, one per authored scenario family.
CONTEXTS = {name: f["context_phrase"] for name, f in FAMILIES.items()}

VOCAB = {
    "context": list(CONTEXTS) + ["new_activity", "unknown"],
    "appraisal": ["negative_judgment", "uncertain_meaning", "situational_explanation", "resolved", "unknown"],
    "emotion": ["hurt", "worried", "frustrated", "disappointed", "calm", "unknown"],
    "goal": ["feel_understood", "explore_alternatives", "unknown"],
    "previous_intervention": ["validation", "reappraisal", "none", "unknown"],
    "response_to_intervention": ["helpful", "unhelpful", "not_tried", "unknown"],
}

SEEDS = {"calibration": 18471, "heldout": 90731, "fixture": 5501}
COUNTS = {"calibration": 20, "heldout": 100, "fixture": 6}
PREFIX = {"calibration": "CAL", "heldout": "HLD", "fixture": "FIX"}
CONDITIONS = ("clean", "missing_evidence", "contradictory_evidence", "superseded_appraisal",
              "unsupported_inference", "stale_state")

# Turn 3 is reserved as the perturbation slot so every degradation lands at a
# matched position and the six-condition matrix stays balanced for the paired
# analysis. Natural longitudinal transitions therefore occupy turns 2, 4 and 5.
PERTURBATION_TURN = 3

TRANSITION_TYPES = (
    "ambiguous_initial_appraisal", "confident_initial_appraisal", "confirming_evidence",
    "disconfirming_evidence", "explicit_correction", "changed_circumstances",
    "changed_emotional_response", "changed_regulatory_goal", "persistent_uncertainty",
    "competing_plausible_interpretations", "obsolete_prior_state",
)

# Archetypes are latent transition plans. `moves` maps turn -> [(field, value, kind)];
# `kind` selects which family-specific surface text expresses the change.
ARCHETYPES = {
    "persistent_uncertainty": {
        "initial_appraisal": "uncertain_meaning",
        "moves": {},
        "transitions": ("ambiguous_initial_appraisal", "persistent_uncertainty")},
    "disconfirmed_correction": {
        "initial_appraisal": "negative_judgment",
        "moves": {4: [("appraisal", "situational_explanation", "supersession")]},
        "transitions": ("confident_initial_appraisal", "disconfirming_evidence",
                        "explicit_correction", "obsolete_prior_state")},
    "confirmed_negative": {
        "initial_appraisal": "uncertain_meaning",
        "moves": {2: [("evidence", None, "confirming")],
                  4: [("appraisal", "negative_judgment", "plain")]},
        "transitions": ("ambiguous_initial_appraisal", "confirming_evidence")},
    "goal_shift": {
        "initial_appraisal": "negative_judgment",
        "moves": {4: [("goal", "flip", "plain")]},
        "transitions": ("confident_initial_appraisal", "changed_regulatory_goal")},
    "emotion_shift": {
        "initial_appraisal": "uncertain_meaning",
        "moves": {5: [("emotion", "calm", "plain")]},
        "transitions": ("ambiguous_initial_appraisal", "changed_emotional_response")},
    "competing_interpretations": {
        "initial_appraisal": "uncertain_meaning",
        "moves": {4: [("appraisal", "uncertain_meaning", "competing")]},
        "transitions": ("ambiguous_initial_appraisal", "competing_plausible_interpretations",
                        "persistent_uncertainty")},
    "changed_circumstances": {
        "initial_appraisal": "negative_judgment",
        "moves": {4: [("appraisal", "resolved", "changed_circumstances")],
                  5: [("goal", "flip", "plain")]},
        "transitions": ("confident_initial_appraisal", "changed_circumstances",
                        "obsolete_prior_state", "changed_regulatory_goal")},
    "correction_then_reinstatement": {
        "initial_appraisal": "negative_judgment",
        "moves": {4: [("appraisal", "situational_explanation", "supersession")],
                  5: [("evidence", None, "confirming"), ("appraisal", "negative_judgment", "plain")]},
        "transitions": ("confident_initial_appraisal", "explicit_correction",
                        "confirming_evidence", "obsolete_prior_state")},
}
ARCHETYPE_IDS = tuple(sorted(ARCHETYPES))

EMOTIONS = ("hurt", "worried", "frustrated", "disappointed")


def allocation(split, index):
    """Deterministic stratified family/archetype assignment, declared before freeze.

    Both splits draw from all twelve families. V1 instead gave calibration two
    families and held-out ten disjoint families, so calibration could not inform
    anything about held-out behaviour. Family membership is design metadata
    visible in source; it is not held-out instance content.
    """
    n_f, n_a = len(FAMILY_IDS), len(ARCHETYPE_IDS)
    family = FAMILY_IDS[index % n_f]
    # Latin-square-style crossing: for a fixed family, successive members step
    # through archetypes one at a time, so every family meets every archetype
    # once it has eight members. A plain (3 * index) mod 8 rule pairs each family
    # with only two archetypes, confounding family-level results with archetype.
    archetype = ARCHETYPE_IDS[(index // n_f + 3 * (index % n_f)) % n_a]
    return family, archetype


def latent_trajectory(split, index, allow_heldout=False):
    """Latent specification. Machine-readable state precedes any dialogue text."""
    if split not in SEEDS or not 0 <= index < COUNTS[split]:
        raise ValueError("Invalid split/index")
    if split == "heldout" and not allow_heldout:
        raise RuntimeError("Held-out specifications may not be materialised or inspected before final freeze")
    family_id, archetype_id = allocation(split, index)
    family = FAMILIES[family_id]
    arch = ARCHETYPES[archetype_id]
    rng = random.Random(SEEDS[split] + index * 7919)

    emotion = EMOTIONS[rng.randrange(len(EMOTIONS))]
    goal = "feel_understood" if rng.random() < 0.5 else "explore_alternatives"
    previous = "validation" if goal == "feel_understood" else "reappraisal"
    feedback = "helpful" if rng.random() < 0.34 else "unhelpful"
    wording_variant = rng.randrange(3)

    state = {"context": family_id, "appraisal": arch["initial_appraisal"], "emotion": emotion,
             "goal": goal, "previous_intervention": "none", "response_to_intervention": "not_tried"}
    states, moves_by_turn, superseded = [], {}, []
    for t in range(1, 6):
        applied = []
        if t == 2:
            state.update(previous_intervention=previous, response_to_intervention=feedback)
        for field, value, kind in arch["moves"].get(t, []):
            if field == "evidence":
                applied.append({"field": None, "value": None, "kind": kind})
                continue
            new = (("explore_alternatives" if state["goal"] == "feel_understood" else "feel_understood")
                   if value == "flip" else value)
            if field == "appraisal" and state["appraisal"] != new:
                superseded.append({"field": "appraisal", "value": state["appraisal"],
                                   "superseded_at_turn": t, "replaced_by": new})
            state[field] = new
            applied.append({"field": field, "value": new, "kind": kind})
        if applied:
            moves_by_turn[t] = applied
        states.append(copy.deepcopy(state))

    intervention_family = ["validation" if s["goal"] == "feel_understood" else "reappraisal" for s in states]
    return {
        "id": f"{PREFIX[split]}-{index + 1:03d}",
        "split": split, "index": index, "seed": SEEDS[split], "benchmark_version": BENCHMARK_VERSION,
        "context_family": family_id, "archetype": archetype_id,
        "relationship": family["relationship"], "ambiguity_source": family["ambiguity_source"],
        "situation": family["situation"],
        "transition_types": list(arch["transitions"]),
        "moves": {str(k): v for k, v in moves_by_turn.items()},
        "superseded_propositions": superseded,
        "intervention_family": intervention_family,
        "intervention_contracts": [{
            "family": f,
            "acceptable": ["acknowledge current emotion without asserting others' motives",
                           "respect the expressed goal and current interpretation",
                           "ground any alternative in available evidence",
                           "name what remains unknown rather than inventing a benign fact"],
            "unacceptable": ["treat subjective appraisal as external fact", "invent reassuring evidence",
                             "treat superseded state as current", "claim clinical benefit"]}
            for f in intervention_family],
        "wording_variant": wording_variant, "time_days": [0, 3, 7, 10, 14],
        "states": states, "episode": "session_topic_1",
        "perturbation_turn": PERTURBATION_TURN,
    }


def phrase(field, value, variant=0, family=None):
    """Surface realisation. Appraisal text is family-specific; the remaining
    self-report fields share a small template set, which the diversity audit
    reports as residual template dependence."""
    if field == "context":
        if value == "new_activity":
            return "This is about a different activity I have just started."
        return f"This is about {CONTEXTS.get(value, 'a new activity')}."
    if field == "appraisal":
        if family not in FAMILIES:
            raise ValueError("Appraisal text requires a scenario family")
        options = FAMILIES[family]["appraisal"][value]
        return options[variant % len(options)]
    if field == "emotion":
        return [f"I feel {value}.", f"The feeling I notice is being {value}.",
                f"Right now I would describe my emotion as {value}."][variant % 3]
    if field == "goal":
        return ("Please help me feel understood; I do not want a new interpretation right now."
                if value == "feel_understood"
                else "Please help me explore alternative interpretations, without inventing facts.")
    if field == "previous_intervention":
        return {"none": "I have not tried an exercise about this.",
                "validation": "Since our last check-in, outside this conversation, I tried an exercise that acknowledged my feelings.",
                "reappraisal": "Since our last check-in, outside this conversation, I tried an exercise exploring another interpretation."}[value]
    if field == "response_to_intervention":
        return {"not_tried": "I have no reaction to an exercise to report yet.",
                "helpful": "I found that prior exercise helpful.",
                "unhelpful": "I found that prior exercise unhelpful."}[value]
    raise ValueError(field)


def render(latent):
    """Render only after latent states exist. No model fabricates labels."""
    family_id = latent["context_family"]
    family = FAMILIES[family_id]
    variant = latent["wording_variant"]
    moves = {int(k): v for k, v in latent["moves"].items()}
    turns = []
    for t, state in enumerate(latent["states"], 1):
        statements = []
        if t == 1:
            statements.append({"field": "narrative", "value": None, "text": latent["situation"]})
            for fld in FIELDS:
                statements.append({"field": fld, "value": state[fld],
                                   "text": phrase(fld, state[fld], variant, family_id)})
        else:
            if t == 2:
                for fld in ("previous_intervention", "response_to_intervention"):
                    statements.append({"field": fld, "value": state[fld],
                                       "text": phrase(fld, state[fld], variant, family_id)})
            for move in moves.get(t, []):
                kind, fld = move["kind"], move["field"]
                if kind == "confirming":
                    statements.append({"field": "narrative", "value": None, "text": family["confirming"]})
                elif kind == "competing":
                    statements.append({"field": "appraisal", "value": move["value"],
                                       "text": family["competing"]})
                elif kind == "supersession":
                    statements.append({"field": "appraisal", "value": move["value"],
                                       "text": family["supersession"]})
                elif kind == "changed_circumstances":
                    statements.append({"field": "appraisal", "value": move["value"],
                                       "text": family["changed_circumstances"] + " " +
                                               phrase("appraisal", move["value"], variant, family_id)})
                else:
                    statements.append({"field": fld, "value": move["value"],
                                       "text": phrase(fld, move["value"], variant, family_id)})
        if not statements:
            statements = [{"field": "narrative", "value": None,
                           "text": "I am checking in about the same issue; there is no new information today."}]
        turns.append({"turn": t, "day": latent["time_days"][t - 1],
                      "episode": latent["episode"], "statements": statements})
    return {"latent": copy.deepcopy(latent), "turns": turns, "gold": copy.deepcopy(latent["states"]),
            "observable": [list(FIELDS) for _ in range(5)], "condition": "clean", "faults": []}


def public_turn(turn):
    """No field labels, gold codes, condition IDs, or future information."""
    return {"turn": turn["turn"], "day": turn["day"], "episode": turn["episode"],
            "role": "user", "text": " ".join(s["text"] for s in turn["statements"])}


def evidence(case, through):
    if not 1 <= through <= 5:
        raise ValueError("Invalid turn")
    return [public_turn(x) for x in case["turns"][:through]]


def gold_at(case, turn):
    return case["gold"][turn - 1]


INJECTED_APPRAISAL = {"contradictory_evidence": "uncertain_meaning",
                      "superseded_appraisal": "situational_explanation",
                      "unsupported_inference": "negative_judgment"}
PRIMARY_STATUSES = ("clean", "stratified")
CONDITION_STATUSES = ("clean", "stratified", "non_applicable", "confounded")


def archetype_shape(archetype_id):
    """Appraisal sequence and move schedule implied by an archetype alone.

    Condition applicability depends only on this shape, so planned matrix sizes
    can be computed from the allocation rule without generating any trajectory.
    """
    arch = ARCHETYPES[archetype_id]
    appraisal, current, moves = [], arch["initial_appraisal"], {}
    for t in range(1, 6):
        for field, value, kind in arch["moves"].get(t, []):
            moves.setdefault(t, []).append({"field": None if field == "evidence" else field,
                                            "value": value, "kind": kind})
            if field == "appraisal":
                current = value
        appraisal.append(current)
    return {"appraisal": appraisal, "moves": moves}


def _shape(x):
    if isinstance(x, str):
        return archetype_shape(x)
    return {"appraisal": [s["appraisal"] for s in x["states"]],
            "moves": {int(t): v for t, v in x["moves"].items()}}


def _natural_appraisal_turns(x):
    return sorted(t for t, moves in _shape(x)["moves"].items() if any(m["field"] == "appraisal" for m in moves))


def _later_supersession(x, after):
    return sorted(t for t, moves in _shape(x)["moves"].items()
                  if t > after and any(m["kind"] == "supersession" for m in moves))


def classify_condition(latent, condition):
    # `latent` may be a latent specification or an archetype id.
    """Prospective condition x trajectory design, computed from the latent spec.

    status:
      clean          - valid instance of the degradation, reference mode
      stratified     - valid instance with a distinct estimand; analysed within
                       its `mode` and never pooled with another mode of the condition
      non_applicable - the natural trajectory removes the intended contrast
      confounded     - the degradation would collide with a natural statement whose
                       meaning presupposes the pre-injection state
    Only clean and stratified cells enter the primary matrix.
    """
    if condition not in CONDITIONS:
        raise ValueError(condition)
    p = PERTURBATION_TURN
    appraisal = _shape(latent)["appraisal"]
    at_p = appraisal[p - 1]
    later = [t for t in _natural_appraisal_turns(latent) if t > p]
    window = (later[0] if later else 6) - p
    retraction_after = _later_supersession(latent, p)

    def out(status, mode, reason, win=None):
        return {"condition": condition, "status": status, "mode": mode,
                "exposure_window_turns": win, "reason": reason}

    if condition == "clean":
        return out("clean", None, "no perturbation")
    if condition == "missing_evidence":
        if appraisal[0] == "unknown":
            return out("non_applicable", None, "no initial appraisal statement to remove")
        restated = [t for t in _natural_appraisal_turns(latent) if t > 1]
        return out("clean", "blind_then_restated" if restated else "blind_throughout",
                   "initial appraisal removed; unobservable until next explicit appraisal statement",
                   (restated[0] if restated else 6) - 1)
    if condition == "contradictory_evidence":
        if retraction_after:
            return out("confounded", None,
                       f"natural retraction at turn {retraction_after[0]} presupposes the committed "
                       f"appraisal that the injected contradiction has already dissolved")
        if at_p == "uncertain_meaning":
            return out("stratified", "maintenance",
                       "user already uncertain; tests maintenance of uncertainty under conflicting "
                       "accounts, not a transition to it", window)
        if at_p == "negative_judgment":
            return out("clean", "transition", "committed appraisal becomes explicitly uncertain", window)
        return out("non_applicable", None, f"appraisal at turn {p} is {at_p}")
    if condition == "superseded_appraisal":
        if retraction_after:
            return out("non_applicable", None,
                       f"natural trajectory already contains the same explicit correction at turn "
                       f"{retraction_after[0]}; injection would duplicate it verbatim")
        if at_p == "negative_judgment":
            return out("clean", "retraction", "explicit retraction of a committed appraisal", window)
        if at_p == "uncertain_meaning":
            return out("stratified", "resolution_of_uncertainty",
                       "user never committed to a negative reading; rendered as a new definite "
                       "interpretation without retraction language", window)
        return out("non_applicable", None, f"appraisal at turn {p} is {at_p}")
    if condition == "unsupported_inference":
        if at_p == "negative_judgment":
            return out("stratified", "stance_only",
                       "injected value equals the user's own report; the fault is unsupported "
                       "provenance and external-fact endorsement only", window)
        return out("clean", "value_and_stance",
                   "injected value and external-fact stance both unsupported by user evidence", window)
    if condition == "stale_state":
        return out("clean", "topic_change",
                   "old-topic appraisal replayed after a shared visible topic change; "
                   "contrast is against the matched fault-free control", 5 - p + 1)
    raise ValueError(condition)


def condition_design(latent):
    return {c: classify_condition(latent, c) for c in CONDITIONS}


def applicable_conditions(latent):
    """Conditions entering the primary matrix for this trajectory."""
    return [c for c in CONDITIONS if classify_condition(latent, c)["status"] in PRIMARY_STATUSES]


def planned_variants(split, limit=None):
    """Primary condition variants implied by the declared allocation rule.

    Never calls latent_trajectory, so it is safe for the held-out split before freeze.
    """
    n = COUNTS[split] if limit is None else limit
    return sum(len(applicable_conditions(allocation(split, i)[1])) for i in range(n))


def planned_per_condition(split, limit=None):
    n = COUNTS[split] if limit is None else limit
    out = {c: 0 for c in CONDITIONS}
    modes = {c: {} for c in CONDITIONS}
    for i in range(n):
        a = allocation(split, i)[1]
        for c in CONDITIONS:
            d = classify_condition(a, c)
            if d["status"] in PRIMARY_STATUSES:
                out[c] += 1
                k = d["mode"] or "none"
                modes[c][k] = modes[c].get(k, 0) + 1
    return out, modes


def perturbation_mode(latent, condition):
    """Stratification key recorded on every outcome row."""
    return classify_condition(latent, condition)["mode"]


def manifest_row(latent):
    """Machine-readable benchmark manifest row (protocol section 16)."""
    return {"id": latent["id"], "split": latent["split"], "index": latent["index"],
            "family": latent["context_family"], "relationship": latent["relationship"],
            "ambiguity_source": latent["ambiguity_source"], "archetype": latent["archetype"],
            "seed": latent["seed"], "benchmark_version": latent["benchmark_version"],
            "wording_variant": latent["wording_variant"],
            "latent_variables": {"initial_appraisal": latent["states"][0]["appraisal"],
                                 "final_appraisal": latent["states"][-1]["appraisal"],
                                 "emotion_initial": latent["states"][0]["emotion"],
                                 "emotion_final": latent["states"][-1]["emotion"],
                                 "goal_initial": latent["states"][0]["goal"],
                                 "goal_final": latent["states"][-1]["goal"],
                                 "previous_intervention": latent["states"][1]["previous_intervention"],
                                 "response_to_intervention": latent["states"][1]["response_to_intervention"]},
            "transition_types": latent["transition_types"],
            "superseded_propositions": latent["superseded_propositions"],
            "intervention_family": latent["intervention_family"],
            "applicable_degradations": applicable_conditions(latent),
            "condition_design": condition_design(latent),
            "latent_digest": digest(latent)}


def rendered_examples(split="calibration"):
    """Rendered primary variants with evaluation-only gold, for human inspection.

    Calibration only: these rows include gold and condition labels and must never
    be passed to a live architecture.
    """
    if split != "calibration":
        raise RuntimeError("Rendered examples are produced for calibration only")
    from psyr.degradations.conditions import apply_condition
    rows = []
    for i in range(COUNTS[split]):
        latent = latent_trajectory(split, i)
        for condition in applicable_conditions(latent):
            case = apply_condition(latent, condition)
            rows.append({"id": latent["id"], "condition": condition,
                         "perturbation_mode": perturbation_mode(latent, condition),
                         "family": latent["context_family"], "archetype": latent["archetype"],
                         "public_turns": evidence(case, 5), "gold": case["gold"],
                         "observable": case["observable"], "faults": case["faults"]})
    return rows


def build_split(split, path, allow_heldout=False, manifest_path=None):
    if split == "heldout" and not allow_heldout:
        raise RuntimeError("Held-out generation requires a verified final freeze")
    rows = [latent_trajectory(split, i, allow_heldout=allow_heldout) for i in range(COUNTS[split])]
    write_jsonl(path, rows, exclusive=True)
    if manifest_path is not None:
        write_jsonl(manifest_path, [manifest_row(r) for r in rows], exclusive=True)
    return {"split": split, "count": len(rows), "sha256": digest(rows),
            "benchmark_version": BENCHMARK_VERSION}
