# exp-000-baseline

## Status

`planned`

## Goal

Measure the untouched Qwen3.5-4B starting model on CETVEL and preserve enough
evidence to compare every later Turkish fine-tuning experiment under the same
conditions.

## Hypothesis

This is a measurement experiment, not a training hypothesis. It establishes the
starting score, task-level variation, output behavior, and evaluation runtime.

## Parent experiment

None. This is the root experiment for this model and capability.

## What changed

Nothing. The model is evaluated without an adapter, merged weights, or
quantization.

## Starting model

- Repository: `Qwen/Qwen3.5-4B`
- Revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Tokenizer/processor: same repository and revision
- Input mode: text only

## Dataset

No training dataset is used. CETVEL is evaluation-only and must never be copied,
translated, paraphrased, or otherwise incorporated into training data.

## Training setup

None. Baseline experiments do not train the model.

## Evaluation

Configuration:
[`configs/evaluation/turkish-cetvel-v1.yaml`](../../../../configs/evaluation/turkish-cetvel-v1.yaml)

Before the full run:

- [ ] Create an isolated evaluation environment.
- [ ] Check out CETVEL and its harness submodule at the pinned commits.
- [ ] Install and record an exact Transformers v5 revision that supports Qwen3.5.
- [ ] Confirm the pinned CETVEL harness can load Qwen3.5 through its `hf` backend.
- [ ] Confirm the model's native chat template is applied exactly once.
- [ ] Confirm thinking mode behavior and freeze the chosen mode.
- [ ] Run one deterministic CETVEL task with `--limit 1`.
- [ ] Inspect the serialized prompt, raw output, parsed answer, and score.
- [ ] Record environment and hardware metadata.
- [ ] Freeze this protocol before running the full suite.

On a suitable Linux GPU host, create an isolated environment, install a
CUDA-compatible PyTorch build, and then run:

```bash
python3 -m venv /workspace/.venvs/cetvel
source /workspace/.venvs/cetvel/bin/activate
bash scripts/evaluation/setup_cetvel.sh
bash scripts/evaluation/run_cetvel_smoke.sh
```

The setup script pins the external repositories and Python packages. It assumes
a CUDA-compatible PyTorch build is already installed because the correct wheel
depends on the rented host's CUDA environment.

The default smoke task is `belebele_tr`. Override it only for a documented
diagnostic run:

```bash
CETVEL_SMOKE_TASK=gecturk_generation bash scripts/evaluation/run_cetvel_smoke.sh
```

The compatibility smoke test is mandatory because CETVEL pins
`lm-evaluation-harness` at an older commit while Qwen3.5 requires current model
support. A newer harness or a compatibility patch would be a material protocol
decision and must be documented before baseline execution.

Unsloth is not needed for the untouched baseline unless it becomes the chosen
inference backend. Training-specific Unsloth behavior must not silently change
the baseline evaluation path.

## Results

The full candidate baseline started at `2026-09-13T09:32:21Z`. It runs in the
background on the RTX 4090 and stores aggregate metrics, per-item samples,
request cache, and five-second GPU telemetry under
`results/full/20260913T093221Z`. It is not a completed result until the process
exits successfully and the output bundle has been validated.

### Smoke attempt 1

Environment preflight initially passed on the RunPod template, but model startup
stopped before weight download because Transformers 5.17 requires PyTorch 2.5
or newer and the template supplied PyTorch 2.4.1. This is a technical setup
failure, not an experimental result. The preflight and setup scripts were
updated to enforce and install a pinned PyTorch 2.6.0/CUDA 12.4 stack.

### Smoke attempt 2

The pinned PyTorch wheel installed, but import failed because the environment
had been created with `--system-site-packages`; pip reused the container image's
cuDNN metadata without making its library visible to the new Torch loader. No
model weights were downloaded. Setup now installs the matching cuDNN wheel into
the active environment explicitly, and clean environments must not inherit
system site packages.

### Smoke attempt 3

Core PyTorch and CUDA checks passed, but importing the evaluation stack loaded
Torchaudio 2.4.1 from the container image against PyTorch 2.6.0 and failed with
an undefined symbol. No model weights were downloaded. Torchaudio 2.6.0 is now
pinned with Torch 2.6.0 and Torchvision 0.21.0.

### Smoke attempt 4

The complete pinned package and CUDA stack passed preflight, and the exact model
revision began downloading. Hugging Face reconstruction stopped at roughly
8.7/9.3 GB because the persistent `/workspace` quota was exhausted. No model was
loaded and no benchmark item ran. Current usage includes approximately 9.9 GB
for the isolated environment, 3.3 GB of disposable pip cache, 3.8 GB of partial
Hugging Face cache, and 0.3 GB for the repository and CETVEL checkout. Expand
the volume before retrying so the model, benchmark datasets, and output bundle
have adequate headroom.

### Smoke attempt 5

After expanding persistent storage, both the `belebele_tr` likelihood path and
the `gecturk_generation` generation path completed. Inspection showed the native
template appended `<think>` and the GEC task stopped at its first generated
newline, producing only `Thinking Process:` for scoring. This is a protocol
incompatibility rather than a model-quality result. The pinned harness is now
augmented by the tracked
[`cetvel-harness-qwen35-nonthinking.patch`](../../../../patches/cetvel-harness-qwen35-nonthinking.patch),
which passes `enable_thinking=False` to the native Qwen3.5 chat template.

### Smoke attempt 6

The patched likelihood and generation paths both completed with the pinned
model and harness. In non-thinking mode Qwen3.5's native template intentionally
renders an empty `<think>...</think>` block; it does not emit a reasoning
preamble. The GEC sample instead produced a normal but verbose Turkish
explanation rather than only the corrected sentence, so exact match remained
zero. That is model behavior, not a parser or template failure, and the
one-item smoke score is not reported as benchmark quality. Aggregate files and
per-item records for the successful and diagnostic attempts are preserved in
[`results/smoke`](results/smoke/).

The final smoke preflight recorded Python 3.11.10, PyTorch 2.6.0+cu124,
Transformers 5.17.0, lm-eval 0.4.2, CUDA runtime 12.4, and an RTX 4090 with
23.52 GiB VRAM. The unpatched and patched outputs are retained together so the
protocol decision remains auditable.

### Smoke attempt 7

The first `tquad` mixed-request smoke stopped during dataset construction.
Datasets 5.0.1 no longer supports the dataset loading script used by
`mcemilg/tquad`, so no item was evaluated. Datasets 3.6.0 restored loading-script
execution but its removed `datasets.tasks` namespace remained incompatible with
the script. This revealed that the evaluation environment must pin Datasets
2.21.0 rather than accepting the newest transitive dependency allowed by the
old harness.

### Smoke attempt 8

With Datasets 2.21.0 and explicit remote-code trust, one `tquad` item completed
both its answer-generation and unanswerable-log-likelihood requests and ran all
legacy SQuAD-v2 aggregations. The deprecation warnings are expected for this
pinned stack. As with the other `--limit 1` checks, its scores are structural
test evidence and not baseline measurements.

## Regressions

Not applicable until the starting model has been measured on the selected
regression suite.

## Conclusion

Pending baseline execution.

## Next step

Complete the one-item compatibility smoke test, freeze the evaluation protocol,
then run the complete CETVEL baseline before creating `exp-001-lora`.
