from psyr.common import ROOT, canonical
from psyr.benchmark.dataset import VOCAB

def prompt(name):
    return (ROOT / "configs" / "prompts" / (name + ".txt")).read_text(encoding="utf-8")

def extraction_messages(evidence):
    return [{"role":"system","content":prompt("extract")},
            {"role":"user","content":canonical({"vocabulary":VOCAB,"evidence":evidence})}]

def decision_messages(architecture, evidence, state=None, records=None, fault_notes=None, forced_defer=False):
    # B/C have identical instruction template; only predeclared memory mechanisms differ.
    payload = {"vocabulary":VOCAB,"evidence":evidence, "force_clarification":forced_defer}
    if architecture == "A":
        payload["prior_assistant_notes"] = fault_notes or []
    else:
        payload["state"] = state or {}
        payload["reliability_records"] = records or []
    return [{"role":"system","content":prompt("decide")}, {"role":"user","content":canonical(payload)}]

def response_messages(evidence, decision):
    return [{"role":"system","content":prompt("respond")},
            {"role":"user","content":canonical({"evidence":evidence,"decision":decision})}]

def judge_messages(evidence, response, gold):
    # Judge gets observable gold only; never architecture, condition or model identity.
    return [{"role":"system","content":prompt("judge")},
            {"role":"user","content":canonical({"evidence":evidence,"response":response,"observable_reference":gold})}]
