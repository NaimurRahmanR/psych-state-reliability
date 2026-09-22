#!/usr/bin/env python3
"""Run the original 149 pre-empirical tests against a temporary frozen-source view.

The original suite deliberately asserts that no held-out data or final freeze exists.
Those two assertions are obsolete in the empirical release, so the suite is executed
against a temporary view containing the exact frozen source plus the original offline
diversity artifact, but excluding post-freeze held-out/freeze artifacts. This preserves
the historical test contract without modifying frozen files.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY = ["src", "configs", "protocol", "tests", "scripts", "data/calibration"]
FILES = ["pyproject.toml", "requirements.txt", "requirements-analysis.txt", ".python-version"]

with tempfile.TemporaryDirectory(prefix="psyr-frozen-tests-") as td:
    tmp = Path(td)
    for item in COPY:
        src = ROOT / item
        dst = tmp / item
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
    for item in FILES:
        shutil.copy2(ROOT / item, tmp / item)

    # Recreate the expected pre-freeze heldout sentinel only.
    (tmp / "data/heldout").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data/heldout/README.md", tmp / "data/heldout/README.md")

    # Final freeze is a post-test artifact and is explicitly excluded by the original test contract.
    for p in [tmp / "protocol/freeze_manifest.json", tmp / "protocol/design_lock.json"]:
        if p.exists():
            p.unlink()

    # Offline diversity artifact expected by the original suite.
    (tmp / "results/processed").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "results/processed/benchmark_diversity.json", tmp / "results/processed/benchmark_diversity.json")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp / "src")
    cp = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=tmp, env=env)
    raise SystemExit(cp.returncode)
