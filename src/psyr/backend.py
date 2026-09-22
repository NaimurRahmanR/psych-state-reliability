"""Minimal chat-completions-compatible backend; no fabricated fallback."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from psyr.common import Journal, canonical, digest

class BackendUnavailable(RuntimeError):
    pass

class Backend:
    def __init__(self, config, journal_path, judge=False):
        self.config = config
        self.judge = judge
        self.model = config["judge_model" if judge else "model"]
        self.revision = config["judge_revision" if judge else "model_revision"]
        if not self.model or not self.revision:
            raise BackendUnavailable("Model identifier and pinned revision/snapshot must be configured")
        self.base = os.environ.get(config["judge_endpoint_env" if judge else "endpoint_env"], "").rstrip("/")
        self.key = os.environ.get(config["judge_api_key_env" if judge else "api_key_env"], "")
        parsed = urllib.parse.urlparse(self.base)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise BackendUnavailable("Configure a valid endpoint; credentials belong in the key environment variable")
        if parsed.scheme == "http" and parsed.hostname not in ("localhost","127.0.0.1","::1"):
            raise BackendUnavailable("Use HTTPS except for a local inference server")
        self.params = dict(config["judge_generation" if judge else "generation"])
        self.journal = Journal(journal_path)
        self.cache = {r["call_id"]:r for r in self.journal.records if r.get("kind") == "completion"}
        self.count = len(self.cache)
        fingerprints={r["fingerprint"] for r in self.cache.values() if r.get("status")=="ok" and r.get("fingerprint")}
        if len(fingerprints)>1:
            raise BackendUnavailable("Multiple server fingerprints in one raw run")
        self.fingerprint=next(iter(fingerprints),None)

    def complete(self, call_id, messages, seed):
        request = dict(model=self.model, messages=messages, seed=seed, **self.params)
        request_hash = digest({"request":request,"revision":self.revision})
        if call_id in self.cache:
            row = self.cache[call_id]
            if row["request_hash"] != request_hash:
                raise RuntimeError("Resume request differs from recorded call; start a new run")
            if row.get("error_type")=="ModelIdentityDrift":
                raise BackendUnavailable("This run recorded model identity drift and cannot be resumed")
            return row
        if self.count >= self.config["max_calls"]:
            raise RuntimeError("Predefined call limit reached; no silent incomplete result")
        headers = {"Content-Type":"application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        req = urllib.request.Request(self.base + "/chat/completions", data=canonical(request).encode(), headers=headers)
        result = {"kind":"completion", "call_id":call_id, "request_hash":request_hash,
                  "request":request, "requested_revision":self.revision, "status":"error", "text":None}
        try:
            with urllib.request.urlopen(req, timeout=self.config["request_timeout_seconds"]) as response:
                raw = response.read().decode("utf-8")
            result["raw_response"] = raw
            parsed = json.loads(raw)
            result.update(status="ok", text=parsed["choices"][0]["message"]["content"],
                returned_model=parsed.get("model"), fingerprint=parsed.get("system_fingerprint"), usage=parsed.get("usage"))
            if not isinstance(result["text"], str):
                raise ValueError("Nontext completion")
            # Non-thinking mode is required. A reasoning block is recorded, never stripped;
            # the raw text then normally fails strict JSON parsing and stays visible.
            result["think_block_detected"] = "<think>" in result["text"] or "</think>" in result["text"]
            returned_fingerprint=result.get("fingerprint")
            if result["returned_model"]!=self.model or (self.fingerprint and returned_fingerprint and self.fingerprint!=returned_fingerprint):
                result.update(status="error",text=None,error_type="ModelIdentityDrift")
            elif returned_fingerprint:
                self.fingerprint=returned_fingerprint
        except urllib.error.HTTPError as e:
            result.update(error_type="HTTPError", http_status=e.code)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError) as e:
            result.update(status="error", text=None, error_type=type(e).__name__)
        row = self.journal.append(result)
        self.cache[call_id] = row
        self.count += 1
        if row.get("error_type")=="ModelIdentityDrift":
            raise BackendUnavailable("Returned model identity/fingerprint changed; raw response preserved, run stopped")
        return row
