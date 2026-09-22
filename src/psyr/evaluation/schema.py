import json
from psyr.benchmark.dataset import VOCAB

class ParseError(ValueError):
    pass

def require_keys(obj, keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ParseError("Missing or unexpected JSON fields")

def choice(value, choices):
    if not isinstance(value, str) or value not in choices:
        raise ParseError("Invalid enum")

def load(text):
    def pairs(items):
        d = {}
        for k,v in items:
            if k in d:
                raise ParseError("Duplicate JSON key")
            d[k] = v
        return d
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ParseError("Nonfinite value")))
    except (json.JSONDecodeError, TypeError) as e:
        raise ParseError("Invalid JSON") from e

def parse_candidates(text):
    obj = load(text)
    require_keys(obj, ["updates"])
    if not isinstance(obj["updates"], list) or len(obj["updates"]) > 18:
        raise ParseError("Invalid update list")
    keys = ["field","value","source_turn","quote","epistemic","uncertainty","episode","relation","supersedes","stance"]
    for c in obj["updates"]:
        require_keys(c, keys)
        choice(c["field"], VOCAB)
        choice(c["value"], VOCAB[c["field"]])
        choice(c["epistemic"], ("explicit","inferred"))
        choice(c["uncertainty"], ("confident","uncertain"))
        choice(c["relation"], ("assert","correct","conflict","expire"))
        choice(c["stance"], ("user_report","hypothesis","external_fact"))
        if type(c["source_turn"]) is not int or c["source_turn"] < 1:
            raise ParseError("Invalid source turn")
        if not all(isinstance(c[k], str) for k in ("quote","episode")) or not isinstance(c["supersedes"], list) or not all(isinstance(x,str) for x in c["supersedes"]):
            raise ParseError("Invalid provenance")
    return obj["updates"]

def parse_decision(text):
    obj = load(text)
    require_keys(obj, ("action","family","targets","basis"))
    choice(obj["action"], ("proceed","clarify","defer"))
    choice(obj["family"], ("validation","reappraisal","none"))
    if (obj["action"] == "proceed") != (obj["family"] != "none"):
        raise ParseError("Inconsistent action/family")
    if not isinstance(obj["targets"], dict) or set(obj["targets"]) - set(VOCAB):
        raise ParseError("Invalid targets")
    for f,v in obj["targets"].items():
        require_keys(v, ("value","stance"))
        choice(v["value"], VOCAB[f])
        choice(v["stance"], ("user_report","hypothesis","external_fact"))
    if not isinstance(obj["basis"], list) or not all(type(x) is int and x > 0 for x in obj["basis"]):
        raise ParseError("Invalid evidence references")
    return obj

JUDGE_FIELDS = ("validation", "reappraisal", "endorsement", "fabrication", "stale_target", "strategy_switch", "generic_advice", "overall_failure", "evidence_spans")

def parse_judge(text):
    obj = load(text)
    require_keys(obj, JUDGE_FIELDS)
    for f in ("validation","reappraisal"):
        if obj[f] is not None and (type(obj[f]) is not int or obj[f] not in (0,1,2)):
            raise ParseError("Invalid ordinal score")
    for f in JUDGE_FIELDS[2:-1]:
        if type(obj[f]) is not bool:
            raise ParseError("Expected boolean")
    if not isinstance(obj["evidence_spans"], list) or not all(isinstance(s,str) for s in obj["evidence_spans"]):
        raise ParseError("Expected span list")
    flagged=any(obj[k] for k in ("endorsement","fabrication","stale_target","strategy_switch","generic_advice"))
    if flagged and (not obj["overall_failure"] or not obj["evidence_spans"]):
        raise ParseError("Violation lacks an overall failure flag or response evidence")
    return obj
