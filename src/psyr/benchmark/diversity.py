"""Quantitative benchmark diversity measurement.

Every number this module reports is computed from the generated calibration
trajectories. It deliberately reports lexical statistics *and* structural reuse
statistics, because vocabulary diversity alone does not establish conceptual
diversity, and V1's central weakness was conceptual rather than lexical.

The held-out allocation is described from the declared allocation rule only.
No held-out trajectory is materialised here.
"""
from __future__ import annotations
import re
from collections import Counter

from psyr.benchmark.dataset import (ARCHETYPE_IDS, ARCHETYPES, CONDITIONS, COUNTS, FIELDS,
                                    allocation, applicable_conditions, classify_condition,
                                    evidence, latent_trajectory, perturbation_mode, render)
from psyr.benchmark.families import FAMILIES, FAMILY_IDS

STOP = set("""a an the and or but if of to in on at for with from by as is am are was were be been being
it its this that these those i me my mine we our you your he she they them his her their not no do does did
have has had will would can could should there here what which who whom when where how so than then too very
about into over under again more most other some such only own same s t just now""".split())

# Statement fields whose surface text is drawn from the shared template set rather
# than authored per family. Used to quantify residual template dependence honestly.
SHARED_TEMPLATE_FIELDS = {"emotion", "goal", "previous_intervention", "response_to_intervention", "context"}


def content_tokens(text):
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP and len(w) > 2]


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 0.0


def trajectories(split="calibration"):
    return [latent_trajectory(split, i) for i in range(COUNTS[split])]


def distributions(latents):
    """Distributions over the latent design variables, not over surface words."""
    d = {
        "family": Counter(l["context_family"] for l in latents),
        "relationship": Counter(l["relationship"] for l in latents),
        "ambiguity_source": Counter(l["ambiguity_source"] for l in latents),
        "archetype": Counter(l["archetype"] for l in latents),
        "initial_appraisal": Counter(l["states"][0]["appraisal"] for l in latents),
        "final_appraisal": Counter(l["states"][-1]["appraisal"] for l in latents),
        "initial_emotion": Counter(l["states"][0]["emotion"] for l in latents),
        "final_emotion": Counter(l["states"][-1]["emotion"] for l in latents),
        "initial_goal": Counter(l["states"][0]["goal"] for l in latents),
        "final_goal": Counter(l["states"][-1]["goal"] for l in latents),
        "intervention_family_turn1": Counter(l["intervention_family"][0] for l in latents),
        "intervention_family_turn5": Counter(l["intervention_family"][-1] for l in latents),
        "transition_type": Counter(t for l in latents for t in l["transition_types"]),
        "wording_variant": Counter(l["wording_variant"] for l in latents),
    }
    return {k: dict(sorted(v.items())) for k, v in d.items()}


def degradation_applicability(latents):
    """Prospective condition design over the trajectories, by status and mode."""
    status = {c: Counter() for c in CONDITIONS}
    modes = {c: Counter() for c in CONDITIONS}
    by_archetype = {}
    for l in latents:
        for c in CONDITIONS:
            d = classify_condition(l, c)
            status[c][d["status"]] += 1
            if d["status"] in ("clean", "stratified"):
                modes[c][d["mode"] or "none"] += 1
            by_archetype.setdefault(l["archetype"], {})[c] = f"{d['status']}:{d['mode']}"
    primary = sum(len(applicable_conditions(l)) for l in latents)
    return {"trajectories": len(latents),
            "status_per_condition": {c: dict(sorted(v.items())) for c, v in status.items()},
            "primary_modes_per_condition": {c: dict(sorted(v.items())) for c, v in modes.items()},
            "archetype_x_condition": dict(sorted(by_archetype.items())),
            "primary_condition_variants": primary,
            "naive_condition_variants": len(latents) * len(CONDITIONS)}


def planned_primary_matrix(split="heldout"):
    """Planned primary counts from the allocation rule; no trajectory is generated."""
    from psyr.benchmark.dataset import planned_variants, planned_per_condition
    variants = planned_variants(split)
    per, modes = planned_per_condition(split)
    return {"split": split, "base_trajectories": COUNTS[split], "condition_variants": variants,
            "per_condition": per, "per_condition_mode": modes,
            "architecture_condition_trajectories": variants * 3,
            "primary_decision_points": variants * 3 * 5,
            "matched_control_trajectories": (per["unsupported_inference"] + per["stale_state"]) * 3,
            "naive_design_trajectories": COUNTS[split] * len(CONDITIONS) * 3}


def _public_text(case):
    return " ".join(" ".join(s["text"] for s in t["statements"]) for t in case["turns"])


def lexical(latents, render_fn=render):
    """Lexical statistics over the rendered clean dialogue."""
    per_traj, all_tokens = [], []
    for l in latents:
        text = _public_text(render_fn(l))
        toks = content_tokens(text)
        per_traj.append(toks)
        all_tokens += toks
    pairs = [jaccard(per_traj[i], per_traj[j])
             for i in range(len(per_traj)) for j in range(i + 1, len(per_traj))]
    within, between = [], []
    for i in range(len(latents)):
        for j in range(i + 1, len(latents)):
            same = latents[i]["context_family"] == latents[j]["context_family"]
            (within if same else between).append(jaccard(per_traj[i], per_traj[j]))
    return {"total_content_tokens": len(all_tokens),
            "distinct_content_tokens": len(set(all_tokens)),
            "type_token_ratio": round(len(set(all_tokens)) / len(all_tokens), 4) if all_tokens else None,
            "mean_pairwise_jaccard": round(sum(pairs) / len(pairs), 4) if pairs else None,
            "max_pairwise_jaccard": round(max(pairs), 4) if pairs else None,
            "mean_jaccard_same_family": round(sum(within) / len(within), 4) if within else None,
            "mean_jaccard_different_family": round(sum(between) / len(between), 4) if between else None}


def structural(latents, render_fn=render):
    """Structural/template reuse, measured at the statement level.

    `shared_template_char_fraction` is the share of rendered characters produced by
    the shared template set rather than family-authored text. This is the honest
    counterweight to the lexical numbers.
    """
    situations = Counter(l["situation"] for l in latents)
    frames, shared_chars, total_chars, distinct_statements = Counter(), 0, 0, set()
    family_of_statement = {}
    for l in latents:
        case = render_fn(l)
        for turn in case["turns"]:
            for s in turn["statements"]:
                family_of_statement.setdefault(s["text"], set()).add(l["context_family"])
    cross_chars = 0
    for l in latents:
        case = render_fn(l)
        for turn in case["turns"]:
            for s in turn["statements"]:
                if len(family_of_statement[s["text"]]) >= 2:
                    cross_chars += len(s["text"])
            frames[tuple(s["field"] for s in turn["statements"])] += 1
            for s in turn["statements"]:
                total_chars += len(s["text"])
                distinct_statements.add(s["text"])
                if s["field"] in SHARED_TEMPLATE_FIELDS or (
                        s["field"] == "narrative" and "no new information" in s["text"]):
                    shared_chars += len(s["text"])
    total_statements = sum(len(t["statements"]) for l in latents for t in render_fn(l)["turns"])
    return {"distinct_situations": len(situations),
            "max_trajectories_sharing_one_situation": max(situations.values()),
            "distinct_turn_field_frames": len(frames),
            "most_common_turn_frame_share": round(frames.most_common(1)[0][1] / sum(frames.values()), 4),
            "total_statements": total_statements,
            "distinct_statement_strings": len(distinct_statements),
            "distinct_statement_ratio": round(len(distinct_statements) / total_statements, 4),
            "shared_template_char_fraction": round(shared_chars / total_chars, 4),
            "cross_family_reused_char_fraction": round(cross_chars / total_chars, 4),
            "family_authored_char_fraction": round(1 - shared_chars / total_chars, 4)}


def heldout_allocation_plan():
    """Declared allocation rule only. No held-out trajectory is generated."""
    fam, arch, cross = Counter(), Counter(), {}
    for i in range(COUNTS["heldout"]):
        f, a = allocation("heldout", i)
        fam[f] += 1
        arch[a] += 1
        cross.setdefault(f, set()).add(a)
    archetypes_per_family = {f: len(v) for f, v in cross.items()}
    return {"planned_count": COUNTS["heldout"],
            "materialised": 0,
            "rule": "family = FAMILY_IDS[i % 12]; archetype = ARCHETYPE_IDS[(i // 12 + 3 * (i % 12)) % 8]",
            "archetypes_per_family": dict(sorted(archetypes_per_family.items())),
            "planned_per_family": dict(sorted(fam.items())),
            "planned_per_archetype": dict(sorted(arch.items()))}


def surface_metrics(latents, render_fn=render):
    """Version-independent surface metrics, used for the V1 vs V2 comparison."""
    return {"trajectories": len(latents),
            "scenario_families_used": len({l["context_family"] for l in latents}),
            "lexical": lexical(latents, render_fn), "structural": structural(latents, render_fn)}


def audit(split="calibration"):
    latents = trajectories(split)
    return {"split": split, "count": len(latents),
            "scenario_families": len(FAMILY_IDS), "archetypes": len(ARCHETYPE_IDS),
            "distributions": distributions(latents),
            "degradations": degradation_applicability(latents),
            "lexical": lexical(latents),
            "structural": structural(latents),
            "heldout_allocation_plan": heldout_allocation_plan(),
            "planned_primary_matrix": {"calibration": planned_primary_matrix("calibration"),
                                       "heldout": planned_primary_matrix("heldout")}}
