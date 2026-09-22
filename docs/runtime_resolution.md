# Runtime resolution and frozen configuration status strings

Some source-frozen configuration files retain status text written before the final freeze, for example `freeze_status: NOT_FROZEN` or wording that says the model revision still needs to be resolved. Those files are deliberately preserved byte-for-byte because they are part of the source digest and freeze manifest.

The execution-time facts were resolved later and are recorded separately in:

- `protocol/freeze_manifest.json`
- `release/final_runtime.json`
- `results/provenance/final_analysis_manifest.json`

The authoritative empirical runtime is Qwen/Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, vLLM 0.29.0, Transformers 5.17.0, PyTorch 2.13.0+cu130, CUDA 13.0, BF16, non-thinking mode, with server fingerprint `vllm-0.29.0-33dd102b`.

This separation avoids a post-hoc edit to the frozen scientific source while still making the final runtime unambiguous.
