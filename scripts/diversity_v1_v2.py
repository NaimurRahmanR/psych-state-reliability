#!/usr/bin/env python3
"""Recompute identical surface-diversity metrics for V1 and V2 calibration sets.

Usage: python scripts/diversity_v1_v2.py /path/to/psych-state-reliability-research-package.zip
The V1 generator is loaded from the authoritative V1 ZIP; the same metric code
(psyr.benchmark.diversity.surface_metrics) is applied to both versions.
"""
import hashlib, importlib.util, json, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from psyr.common import ROOT, write_json
from psyr.benchmark import dataset as v2
from psyr.benchmark.diversity import surface_metrics

zpath = Path(sys.argv[1])
member = "psych-state-reliability/src/psyr/benchmark/dataset.py"
with tempfile.TemporaryDirectory() as d, zipfile.ZipFile(zpath) as z:
    src = z.read(member)
    f = Path(d) / "v1_dataset.py"; f.write_bytes(src)
    spec = importlib.util.spec_from_file_location("v1_dataset", f)
    v1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)  # imports only psyr.common digest/write_jsonl
    v1_lat = [v1.latent_trajectory("calibration", i) for i in range(20)]
    result = {"v1_source": {"zip_sha256": hashlib.sha256(zpath.read_bytes()).hexdigest(), "member": member,
                            "member_sha256": hashlib.sha256(src).hexdigest()},
              "v1": surface_metrics(v1_lat, v1.render),
              "v2": surface_metrics([v2.latent_trajectory("calibration", i) for i in range(20)], v2.render)}
write_json(ROOT / "results/processed/diversity_v1_vs_v2.json", result)
print(json.dumps(result, indent=2))
