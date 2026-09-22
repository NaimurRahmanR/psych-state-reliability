# GPU execution plan (documented, NOT executed)

Status: **no stage below has been started.** REAL QWEN CALLS: 0. The authoring environment could not obtain the weights (`huggingface.co`, `hf-mirror.com`, `cas-bridge.xethub.hf.co`, `modelscope.cn` → HTTP 403 `host_not_allowed`) and had 1 CPU, 3 GB RAM and no GPU.

Stages must run in this order. Each has an exit gate; failing a gate stops the plan at that stage. Every stage writes to its own directory and never overwrites an earlier one.

| # | Stage | Exit gate |
|---|---|---|
| 1 | Benchmark V2 independently approved | Written approval of the families, archetypes, condition design and diversity audit, or a list of required changes (which restart this plan at stage 1) |
| 2 | GPU environment | Recorded hardware, driver, CUDA, Python, vLLM and Transformers versions |
| 3 | Exact Qwen revision pinned | Commit SHA recorded in `configs/experiment.json` and weight-file hashes recorded |
| 4 | Non-thinking mode verified | Rendered prompt and raw completions show no reasoning block |
| 5 | Smoke test | End-to-end run on calibration trajectory CAL-001 succeeds |
| 6 | Real 20-trajectory calibration | Complete calibration matrix with every raw output preserved |
| 7 | Calibration-only corrections | Each change documented with its calibration evidence; recalibrated in a new run directory |
| 8 | Evaluator mode decision and validation | `evaluator_mode` set: either a pinned evaluator passes the prospective gate, or `manual_audit_only` is recorded |
| 9 | Final scientific freeze | `finalize` succeeds |
| 10 | Freeze hashes | `protocol/freeze_manifest.json` recorded and copied out of the working tree |
| 11 | Held-out materialisation | Exactly once; hashes recorded |
| 12 | Held-out execution | Primary matrix and matched controls |
| 13 | Repair/replay | Counterfactual probes for B/C state-error exposures |
| 14 | Statistical analysis | Frozen plan only |
| 15 | Blinded human-audit packet | Packet generated before aggregate held-out results are inspected |
| 16 | Independent verification | Reviewer recomputes headline numbers from raw journals |

## 1. Benchmark approval

The reviewer receives this package. Nothing in stages 2–16 begins until approval. A requested benchmark change is made, re-tested and re-audited, and approval is sought again.

## 2. Environment

Minimum practical hardware for Qwen3-8B in bf16 is a single GPU with about 24 GB memory (weights ≈ 16 GB plus KV cache); 40–80 GB gives headroom for the 1,800-token response limit and longer histories. Quantisation is **not** planned: it would change the model under test. If it becomes necessary, that is a model change requiring a documented decision before calibration.

```bash
git clone <review-approved package>  &&  cd psych-state-reliability
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e .
python scripts/check.py                    # must report the documented test count, 0 failures
python scripts/psyr.py doctor              # writes docs/environment.json
pip install vllm==<pin> transformers==<pin>
nvidia-smi > results/raw/env/nvidia_smi.txt
pip freeze > results/raw/env/pip_freeze.txt
```

## 3. Pin the revision

```bash
python - <<'EOF'
from huggingface_hub import HfApi
info = HfApi().model_info("Qwen/Qwen3-8B")
print(info.sha)
EOF
huggingface-cli download Qwen/Qwen3-8B --revision <SHA> --local-dir weights/Qwen3-8B
sha256sum weights/Qwen3-8B/*.safetensors weights/Qwen3-8B/tokenizer* > results/raw/env/weights.sha256
```

Set `model_revision` to that SHA in `configs/experiment.json`. The model must be `Qwen/Qwen3-8B`, never `Qwen/Qwen3-8B-Base`. Check the model card at that revision for the recommended non-thinking sampling values and record whether they match the calibration starting point below. Weights are never committed to the package.

## 4. Serve and verify non-thinking mode

```bash
vllm serve weights/Qwen3-8B --served-model-name Qwen/Qwen3-8B --revision <SHA> \
  --dtype bfloat16 --seed 263901 --max-model-len <recorded> \
  --default-chat-template-kwargs '{"enable_thinking": false}' --port 8000
export PSYR_API_BASE=http://localhost:8000/v1
```

Every request also carries `chat_template_kwargs: {"enable_thinking": false}` from `configs/experiment.json`. Do not enable a vLLM reasoning parser: it would move reasoning text out of `content` and hide it from the raw journal.

Verification, recorded in `results/raw/env/thinking_check.md`:

1. Render the chat template for one extraction message with `enable_thinking=False` via `tokenizer.apply_chat_template(..., enable_thinking=False)` and store the rendered prompt.
2. Send 10 calibration extraction requests; confirm `think_block_detected` is false for all.
3. Confirm the server echoes `model == "Qwen/Qwen3-8B"`; the backend stops on identity drift.

Any `think_block_detected: true` blocks stage 5.

## 5. Smoke test

Run one calibration base in a throwaway directory:

```bash
python scripts/psyr.py run --split calibration --limit 1 --run-dir results/raw/smoke-v2
```

Inspect raw journals for parse success, correct evidence prefixes, identical B/C extraction candidates and plausible latency. The smoke directory is retained but is not calibration evidence.

## 6. Calibration (20 trajectories only)

Calibration starting configuration, identical for A, B and C:

| Parameter | Value | Status |
|---|---|---|
| model | Qwen/Qwen3-8B | fixed |
| revision | pinned SHA | set at stage 3 |
| thinking | disabled (`enable_thinking=false`) | fixed |
| temperature | 0.7 | starting point |
| top_p | 0.8 | starting point |
| top_k | 20 | starting point |
| min_p | 0 | starting point |
| max_tokens | 1800 | starting point |
| seed | 263901 (per-call derived seeds) | fixed |

```bash
# Before an evaluator is selected, calibration generation runs without the judge.
python scripts/psyr.py run --split calibration --no-judge --run-dir results/raw/calibration-v2-r1
python scripts/psyr.py analyze --run-dir results/raw/calibration-v2-r1 --out-dir results/tables/calibration-v2-r1
```

`--no-judge` is refused for held-out. A judgeless run can never satisfy the freeze gate, so the run submitted at stage 9 must be a complete calibration run *with* the validated evaluator (stage 8).

Planned size: 110 primary variants → 330 architecture–condition trajectories (1,650 decision points), plus 120 matched-control trajectories. Record per architecture: extraction/parse success, malformed outputs, unsupported inference, stale state, contradiction handling, supersession, intervention selection, clarify/defer, response generation, `think_block_detected`, and infrastructure versus model failures. Write `results/calibration/calibration_report.md`.

Stochastic sampling check: re-run a fixed subset (e.g. five bases, all conditions) with the same seeds. If the server honours seeds, outputs should repeat; if they do not, quantify how often the parsed decision changes. Sampling may be changed before freeze **only** on these grounds: parse or schema failure above the 5% calibration limit, or decision instability that makes paired comparison uninterpretable. A/B/C performance is never a reason. Any change applies identically to A, B and C and triggers a new calibration run.

## 7. Calibration-only corrections

Allowed: prompts, schemas, parser, clearly broken thresholds, output contracts, evaluator instructions, implementation defects. Each change is recorded in `results/calibration/changes.md` with the calibration evidence and rerun in a new directory (`calibration-v2-r2`, …). Held-out data do not exist yet and must not be generated. Deterministic syntactic parser repair, if introduced, must be specified here, applied to calibration, and frozen.

## 8. Evaluator mode decision and validation

The evaluator mode must be decided here and is recorded in the freeze (stage 9), so it is fixed before held-out materialisation. Rules and the full gate are in `protocol/protocol_v2_amendment.md` §9.

**Option A, `validated_automated`.** 
Select an evaluator model that is **separately configured and not Qwen3-8B**, pin its revision, and set `judge_model`/`judge_revision`. It sees only evidence, the response and observable gold, never architecture or condition.

```bash
python scripts/psyr.py judge-traps --split calibration --run-dir results/raw/calibration-judge-traps-v2
```

Report sensitivity per trap kind, specificity on `clean` and `uncertainty_ack`, missing-judgment rate and within-judge disagreement. Freeze with `--trap-dir` pointing at that run. The gate requires, per failure kind, ≥7/8 detected and, per negative control, ≥7/8 correctly passed (invalid items count as errors); ≤5% invalid trap items; ≤20% of items with disagreeing samples; ≥95% of calibration responses with three valid samples; an evaluator different from the primary model. At most two candidate evaluators may be tried; thresholds may not change after any candidate is scored. The final calibration run submitted to the freeze must include this evaluator's judgments.

**Option B, `manual_audit_only`.** Leave `judge_model`/`judge_revision` empty and set `evaluator_mode` to `manual_audit_only`. No judge is constructed; `judge-traps` is refused; SEPR and all deterministic metrics run unchanged; semantic fidelity is reported `UNAVAILABLE_NOT_VALIDATED`; the blinded packet is the only fidelity pathway and must be rated by real people. H4's automated arm is then not tested.

## 9–10. Final freeze

`finalize` refuses while `evaluator_mode` is unset. In `validated_automated` mode it runs the evaluator gate; in `manual_audit_only` mode it requires that no judge is configured. Either way the parser/API gate (≤5%) and V2 matrix completeness still apply.

```bash
python scripts/psyr.py freeze --run-dir results/raw/calibration-v2-rN [--trap-dir results/raw/calibration-judge-traps-v2]
sha256sum protocol/freeze_manifest.json > ../freeze_manifest.sha256   # store outside the tree
```

`finalize` refuses unless: model and judge revisions are set; the calibration matrix is complete against the V2 design (1,650 primary and 600 matched-control turns); calibration parser/API failures ≤ 5%; each primary response has three valid judgments; source and config hashes match. Record in `protocol/FREEZE.md`: timestamp, hypotheses, architectures, benchmark version and hash, degradation rules, primary endpoint, secondary metrics, model and revision, tokenizer, backend and version, generation configuration, thinking mode, prompt hashes, parser, thresholds, evaluator, seeds, statistical plan, failure criteria.

## 11. Held-out materialisation (exactly once)

```bash
python scripts/psyr.py dataset --split heldout
sha256sum data/heldout/latent.jsonl data/heldout/manifest.jsonl
```

## 12–13. Held-out execution and repair/replay

```bash
python scripts/psyr.py run --split heldout --run-dir results/raw/heldout-v2
python scripts/psyr.py judge-traps --split heldout --run-dir results/raw/heldout-judge-traps-v2
```

Planned: 550 primary variants → **1,650** architecture–condition trajectories / **8,250** decision points; **600** matched-control trajectories. Repair/replay probes run inside `run` for every B/C erroneous state slot. Report actual counts from journals; never report planned counts as executed.

Failures stay in denominators. A call is attempted once; there is no retry unless a retry policy was frozen. Infrastructure failures (HTTP, timeout) and model failures (malformed output, think block) are recorded separately. Model identity drift stops the run. A genuine implementation defect stops the affected analysis and is documented; it is not silently patched.

Ablations, if the frozen trigger is met, reuse the primary extraction journal (see README).

## 14. Analysis

```bash
python scripts/psyr.py analyze --run-dir results/raw/heldout-v2 --out-dir results/tables/heldout-v2
python scripts/psyr.py figures --run-dir results/tables/heldout-v2 --out-dir results/figures/heldout-v2
```

Primary: H3 pooled C − B SEPR with paired bootstrap interval; `ALL_REFERENCE` sensitivity; per-condition and per-mode results; 12-family cluster sensitivity; coverage jointly with reliability; McNemar exploratory only. Report every condition, including unfavourable ones.

## 15. Blinded audit packet

Generated before aggregate held-out results are opened:

```bash
python scripts/psyr.py audit-packet --run-dir results/raw/heldout-v2 --out-dir results/audit_private/heldout-v2
```

Only a real person rates it. If no one does, report **HUMAN AUDIT NOT EXECUTED**.

## 16. Independent verification

A reviewer who did not run the experiment recomputes headline numbers from raw journals, checks figures against processed data, and confirms: every raw output is a real Qwen call; the revision matches the freeze; `enable_thinking=false` in every request; identical configuration across A/B/C; no latent truth in C inputs; calibration before freeze; held-out materialisation after freeze; no post-freeze change.

## After held-out materialisation, none of these may change

Model, model revision, thinking mode, prompts, parser, thresholds, benchmark, degradation definitions and applicability rules, primary metric, evaluator, statistical plan. Difficult scenarios are not removed. Inconvenient failures are not rerun.

## Resource estimate

Held-out primary calls, before repair/replay: about 2,750 shared extractions (550 variants × 5 turns), 8,250 decisions, 8,250 responses, and up to 24,750 judge calls (3 per response); controls add roughly a further third. Repair/replay adds two calls per B/C erroneous slot and cannot be estimated before calibration. Throughput and cost must be measured in calibration; no estimate is given here.
