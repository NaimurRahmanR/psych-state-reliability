from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "configs" / "experiment.json").exists():
    raise ImportError(
        "psyr must run from a repository checkout: install with `pip install -e .` from the "
        "repository root (a non-editable install cannot locate configs/, prompts or data/).")

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, obj, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")

def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def write_jsonl(path, rows, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as f:
        for row in rows:
            f.write(canonical(row) + "\n")

def stable_seed(*parts):
    return int(digest(parts)[:8], 16) % (2**31 - 1)

class Journal:
    """Traceable append-only journal. Never rewrites records; validates on resume."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records = read_jsonl(path) if self.path.exists() else []
        previous = "0" * 64
        for n, row in enumerate(self.records):
            payload = {k: v for k, v in row.items() if k != "record_hash"}
            if row.get("seq") != n or row.get("previous_hash") != previous or digest(payload) != row.get("record_hash"):
                raise ValueError("Journal integrity failure")
            previous = row["record_hash"]
        self.previous = previous

    def append(self, payload):
        if any(k in payload for k in ("seq", "previous_hash", "record_hash")):
            raise ValueError("Reserved journal keys")
        row = dict(payload, seq=len(self.records), previous_hash=self.previous)
        row["record_hash"] = digest(row)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.records.append(row)
        self.previous = row["record_hash"]
        return row
