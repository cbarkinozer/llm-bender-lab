# RTX 4090 demo preparation

Prepared locally, not GPU-tested. This is a 50-row task-to-tests experiment;
planning/decision records are supporting development probes, not mixed training.
Recipe and hashes: `demo-preflight-v01/recipe.json` and `manifest.json`.

Starting point: exp015/016 BF16 LoRA, rank/alpha16, dropout0, seven projection
modules, LR1e-4, batch1/accumulation8, AdamW8bit, cosine, warmup2, seed3407.
Use fresh Qwen/Qwen3.5-4B revision851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a,
not the previous domain adapter. Changed: thinking enabled, max length3072,
three epochs over50 examples, no packing/truncation. Approximately21 optimizer
updates; actual steps/exposure are recorded rather than assumed.

Native training representation: 91,858 input and17,266 supervised tokens/epoch;
three epochs target275,574 input and51,798 supervised tokens. All50 arrays match
the saved native-label audit exactly. The actual GPU trainer re-encodes all rows,
then compares actual training microbatch labels to saved arrays before each step.

## Evaluation decision

Repository-held-out transfer demo, not a balanced-domain benchmark. Accept the
three documented taught-principle overlaps for this purpose. No split rows moved.
Use five task-to-tests development requests as the primary comparison and four
other development requests as supporting probes. No holdout generation yet.
Preselect final epoch; inspect development results before a separate final holdout
run. Require paired blinded review using the existing baseline rubric for semantic
quality; static format/AST checks alone are not an adequate quality measure.
No execution of generated code on the host. Runtime correctness/fault-detection
claims require protected execution and inspection, not just successful generation.

Base and candidate both use vLLM BF16, greedy generation, seed3407, repetition
penalty1, max2048 new tokens, max8192 context, native thinking-enabled template,
explicit stops at native im_end248046 or endoftext248044. Preserve token IDs and
finish/stop reasons. Length-capped outputs are incomplete, not successful tests.
Smoke adapter reload uses the same nine development requests; it is diagnostic,
not a new independent evaluation. Do not tune the recipe from smoke outputs.
vLLM compatibility with this model's LoRA must pass on the pod; do not silently
switch engines if it fails. Actual installed versions and GPU environment are
recorded. Backend installation/runtime compatibility is still a GPU gate.

## Before renting

No pod is needed to inspect these files. No model weights were downloaded.
Use one RTX4090 24GB, sufficient persistent disk (allow60GB for two environments,
weights/caches/results), and consult environment-setup-gotchas.md. Reuse a known
working persistent environment if available. Historical validated training setup:
`experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/setup_training.sh`.
It pins Torch2.7.1, Transformers5.5.0, Unsloth2026.9.6 and matching kernels.
Do not install vLLM into that training environment. A separate vLLM environment is
required; validate model/adapter support before committing to the training run.
The existing `scripts/evaluation/setup_vllm_qwen35.sh` is an unpinned historical
installer, not a reproducible current lockfile: inspect/reuse an existing working
environment or pin the resolved installation before measured generation.

## Staged commands (Linux, clean checkout, activated relevant environment)

Export HF_HOME, pip/uv caches and output directories under /workspace. Unset
USE_TORCH if inherited from tokenizer-only local preparation. Inference and
training commands run as separate processes, so GPU allocations are released.
Use a new output root for retries; the runner refuses to overwrite evidence.

```bash
export HF_HOME=/workspace/.cache/huggingface
export PIP_CACHE_DIR=/workspace/.cache/pip
export UV_CACHE_DIR=/workspace/.cache/uv
unset USE_TORCH
runner=scripts/evaluation/run_tdd_demo_gpu.py
out=/workspace/tdd-demo-v01
# vLLM environment
python "$runner" --mode baseline --output "$out/base"
# Unsloth training environment
python "$runner" --mode smoke --output "$out/smoke"
python "$runner" --mode tiny --output "$out/tiny"
# vLLM environment: inspect successful reload and stop reasons
python "$runner" --mode candidate --adapter "$out/smoke/adapter" --output "$out/reload"
# Unsloth environment: fails if preceding evidence is absent/inconsistent
python "$runner" --mode full --output "$out/sft" --baseline "$out/base" --smoke "$out/smoke" --tiny "$out/tiny" --reload "$out/reload"
# vLLM environment
python "$runner" --mode candidate --adapter "$out/sft/adapter" --output "$out/candidate"
```

Then preserve raw outputs/config/environment/exposure and adapter locally before
pod termination; compare five development tasks blindly against baseline and
review supporting probes separately. Use manual/AI-assisted rubric review as the
owner previously chose; label it accordingly. Do not claim measured utility from
training loss. Holdout and protected execution can follow as separate stages.

## Timing estimate, not measured on this corpus

Historical exp015 F RTX4090:320 microbatches,37,334 input/19,131 supervised tokens
in106.8984seconds (`gpu-results-v1/F/sft-v1/result.json` and exposure.jsonl).
Linear input-token extrapolation:789seconds (~13.2min) for this three-epoch run.
Different lengths, checkpointing, kernels, attention costs and loss-token counts
make this approximate; allow10–20min for training alone, revise after smoke.

Budget roughly25–45min on a warm compatible pod for model loads, base/reload/
candidate generation, smoke/tiny and training, excluding detailed human review.
Cold setup/downloads can bring total to45–75min or longer on slow networks.
These are planning allowances, not measured throughput promises. A15–20min
end-to-end deadline is not reliable. Recommend tomorrow if that is tonight's
hard limit. Do not rent until the owner accepts the estimate and supplies access.
