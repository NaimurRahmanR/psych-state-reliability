from __future__ import annotations
from collections import Counter
from psyr.benchmark.dataset import FIELDS

def ratio(n, d):
    return n / d if d else None

def state_errors(view, gold, observable):
    errors = []
    for field, item in view.items():
        if item["value"] == "unknown" or item["stance"] == "hypothesis":
            continue
        reason = None
        if field not in observable:
            reason = "unsupported"
        elif item["value"] != gold[field]:
            reason = "incorrect_or_obsolete"
        elif field == "appraisal" and item["stance"] == "external_fact":
            reason = "appraisal_endorsement"
        if reason:
            errors.append({"field":field,"value":item["value"],"reason":reason})
    return errors

def state_counts(view, gold, observable):
    asserted = {f:v for f,v in view.items() if v["value"] != "unknown" and v["stance"] != "hypothesis"}
    correct = sum(f in observable and v["value"] == gold[f] and not(f == "appraisal" and v["stance"] == "external_fact") for f,v in asserted.items())
    return {"state_correct":correct,"state_asserted":len(asserted),"state_required":len(observable),
            "state_errors":len(state_errors(view,gold,observable))}

def decision_violations(decision, gold, observable, turn):
    if decision is None:
        return {"parser"}
    bad = set()
    if any(i > turn for i in decision["basis"]):
        bad.add("provenance")
    for e in state_errors(decision["targets"], gold, observable):
        bad.add(e["field"])
    if decision["action"] == "proceed":
        expected = "validation" if gold["goal"] == "feel_understood" else "reappraisal"
        if decision["family"] != expected:
            bad.add("goal")
        needed = {"context","emotion","goal"}
        if decision["family"] == "reappraisal":
            needed.add("appraisal")
        for field in needed:
            if field not in decision["targets"] or decision["targets"][field]["value"] == "unknown":
                bad.add(field)
    return bad

def sepr_counts(cases):
    """Every item is one erroneous state-slot exposure, not an entire trajectory."""
    counts = Counter(x["attribution"] for x in cases)
    n = len(cases)
    propagated = counts["propagated"]
    ambiguous = counts["ambiguous"]
    return {"error_exposures":n,"propagated":propagated,"ambiguous":ambiguous,
            "sepr":ratio(propagated,n),"sepr_upper_bound":ratio(propagated+ambiguous,n)}

def coverage_counts(rows):
    n = len(rows)
    proceed = sum(r.get("proceeded",False) for r in rows)
    good = sum(r.get("proceeded",False) and r.get("decision_error") is False and r.get("fidelity_failure") is False for r in rows)
    decided = sum(r.get("proceeded",False) and r.get("decision_error") is False for r in rows)
    return {"eligible":n,"proceeded":proceed,"coverage":ratio(proceed,n),
            # Deterministic: proceeded with no typed decision error. Always available.
            "decision_reliable_proceeded":decided,"decision_reliable_coverage":ratio(decided,n),
            "reliable_proceeded":good,"reliable_coverage":ratio(good,n),
            "fidelity_unknown":sum(r.get("fidelity_failure") is None for r in rows)}

def aggregate_judgments(judgments):
    """Three repeated completions; majority only when all are valid."""
    if len(judgments) != 3 or any(j is None for j in judgments):
        return {"fidelity_failure":None,"judge_disagreement":None,"judge_valid":sum(j is not None for j in judgments)}
    vals = [j["overall_failure"] for j in judgments]
    result = {"fidelity_failure":sum(vals)>=2,"judge_disagreement":len(set(vals))>1,"judge_valid":3}
    for key in ("endorsement","fabrication","stale_target","strategy_switch","generic_advice"):
        result[key] = sum(j[key] for j in judgments)>=2
    for key in ("validation","reappraisal"):
        scores = [j[key] for j in judgments if j[key] is not None]
        result[key] = sorted(scores)[len(scores)//2] if len(scores) == 3 else None
    return result

def attribution(original, replay, repaired, field):
    if original is None or replay is None or repaired is None or replay != original:
        return "ambiguous"
    return "propagated" if field in original and field not in repaired else "not_demonstrated"

def classification_audit(labels, predictions):
    if len(labels) != len(predictions):
        raise ValueError("Mismatched labels")
    pairs = [(a,b) for a,b in zip(labels,predictions) if b is not None and a is not None]
    tp=sum(a and b for a,b in pairs); tn=sum(not a and not b for a,b in pairs)
    fp=sum(not a and b for a,b in pairs); fn=sum(a and not b for a,b in pairs)
    n=len(pairs); agreement=ratio(tp+tn,n)
    pe=((tp+fn)*(tp+fp)+(tn+fp)*(tn+fn))/(n*n) if n else None
    return {"n":n,"missing":len(labels)-n,"tp":tp,"tn":tn,"fp":fp,"fn":fn,
            "sensitivity":ratio(tp,tp+fn),"specificity":ratio(tn,tn+fp),"agreement":agreement,
            "cohen_kappa":(agreement-pe)/(1-pe) if n and pe!=1 else None}
