#!/usr/bin/env python3
"""Portable invariant suite with saved count and failure report."""
import io
import json
from pathlib import Path
import sys
import unittest
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"src"))
stream=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(root/"tests"))
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
report=stream.getvalue()
(root/"docs/test_results.txt").write_text(report,encoding="utf-8")
summary={"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),
         "successful":result.wasSuccessful(),"scope":"software invariants and temporary canned fixtures; no research model inference"}
(root/"docs/test_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
