from __future__ import annotations
import copy
from psyr.common import digest
from psyr.benchmark.dataset import FIELDS

MECHANISMS = ("provenance", "temporal", "epistemic", "contradiction", "defer")

class NaiveState:
    """Competent last-write baseline: accepts explicit corrections; no reliability gating."""
    def __init__(self):
        self.current = {}

    def update(self, candidates, evidence):
        for c in candidates:
            if c["relation"] == "expire":
                self.current.pop(c["field"], None)
            else:
                self.current[c["field"]] = {"value":c["value"], "stance":c["stance"]}

    def view(self):
        return copy.deepcopy(self.current)

class ReliableState:
    def __init__(self, disabled=(), max_age_days=14):
        if set(disabled) - set(MECHANISMS):
            raise ValueError("Unknown ablation")
        self.enabled = set(MECHANISMS) - set(disabled)
        self.max_age_days = max_age_days
        self.records = []
        self.events = []

    def update(self, candidates, evidence):
        latest = evidence[-1]
        sources = {t["turn"]:t for t in evidence}
        if "temporal" in self.enabled:
            for old in self.records:
                if old["status"] in ("active", "competing") and old["field"] != "goal":
                    source = sources.get(old["source_turn"])
                    if old["episode"] != latest["episode"] or (source and latest["day"] - source["day"] > self.max_age_days):
                        old["status"] = "stale"
                        self.events.append({"event":"expired", "id":old["id"], "turn":latest["turn"]})
        for candidate in candidates:
            c = copy.deepcopy(candidate)
            c["id"] = digest(candidate)[:16]
            if any(r["id"] == c["id"] for r in self.records):
                continue
            c.update(status="active", observed_at=latest["turn"], contradiction=False, superseded_by=None)
            source = sources.get(c["source_turn"])
            if "provenance" in self.enabled and (source is None or not c["quote"] or c["quote"] not in source["text"]):
                c["status"] = "rejected_provenance"
            if "temporal" in self.enabled and c["field"] != "goal" and (c["episode"] != latest["episode"] or (source and latest["day"] - source["day"] > self.max_age_days)):
                c["status"] = "stale"
            if "epistemic" in self.enabled and (c["epistemic"] == "inferred" or c["uncertainty"] == "uncertain" or (c["field"] == "appraisal" and c["stance"] == "external_fact")):
                if c["status"] == "active":
                    c["status"] = "uncertain"
            old = [x for x in self.records if x["field"] == c["field"] and x["status"] in ("active", "competing")]
            if c["status"] == "active":
                if c["relation"] == "conflict" and "contradiction" in self.enabled and c["value"] != "uncertain_meaning":
                    for x in old:
                        x.update(status="competing", contradiction=True)
                    c.update(status="competing", contradiction=True)
                else:
                    for x in old:
                        x.update(status="superseded", superseded_by=c["id"])
                    if c["relation"] == "expire":
                        c["status"] = "expired"
            self.records.append(c)

    def view(self):
        result = {}
        for c in self.records:
            if c["status"] == "active":
                result[c["field"]] = {k:copy.deepcopy(c[k]) for k in ("value","stance","source_turn","quote","epistemic","uncertainty","episode","status","id","contradiction")}
        return result

    def metadata(self):
        return copy.deepcopy(self.records)

    def should_defer(self):
        if "defer" not in self.enabled:
            return False
        view = self.view()
        needed = {"context", "emotion", "goal"}
        if view.get("goal", {}).get("value") == "explore_alternatives":
            needed.add("appraisal")
        return not needed.issubset(view) or any(view[f]["value"] == "unknown" for f in needed)

def repair_slot(view, field, gold_value, observable):
    """Evaluation-only intervention. Never writes into a live architecture."""
    result = copy.deepcopy(view)
    if not observable or gold_value == "unknown":
        result.pop(field, None)
    else:
        if field not in result:
            raise ValueError("Repair requires an erroneous represented slot")
        result[field]["value"] = gold_value
        result[field]["stance"] = "user_report"
    return result
