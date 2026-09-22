"""Canned protocol fixture backend for tests only; never research outputs."""
import json
from psyr.common import Journal, canonical

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

