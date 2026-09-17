# exp-003 — Unsloth SFT run

This is the first training run for the response-style-control experiment.
It trains a LoRA adapter only; the base model is never overwritten.

## Fixed experiment inputs

- Base model: `unsloth/Qwen3.5-4B`
- Training data: `../exp-001-sft-dataset/reviewed-v3/accepted-reviewed.csv`
  (2,442 human-accepted and exact-deduplicated records)
- Held-out evaluation: `../exp-002-communication-policy-benchmark/test.csv`
  (100 prompts; never loaded by the trainer)
- Mode: non-thinking chat template, so the adapter learns direct final answers
  rather than emitting reasoning content.

## Proposed first-run configuration

| Setting | Value | Rationale |
| --- | ---: | --- |
| Precision | bf16 LoRA | Qwen3.5 guidance recommends this over QLoRA |
| LoRA rank / alpha | 16 / 16 | Conservative adapter capacity for a small policy dataset |
| Max sequence length | 1,024 | Safely covers the reviewed data (max 810 characters) with less compute waste |
| Per-device batch | 1 | Stable VRAM envelope |
| Gradient accumulation | 8 | Effective batch size 8 |
| Epochs | 2 | First-run, low-overfit baseline |
| Learning rate | 1e-4 | Conservative LoRA policy adaptation |
| Seed | 3407 | Reproducibility; deterministic kernels are requested where supported |
| Tracking | Weights & Biases | Records loss, learning rate, hardware/run configuration, and system telemetry |

The run records the resolved command/configuration, package versions,
GPU telemetry, source-data SHA-256, training metrics, and saved adapter under
the chosen `--output-dir`.

## Required preflight and run order

`config.yaml` is the complete source configuration. It pins the model and
tokenizer revision, dataset and benchmark hashes, SFT recipe, generation
protocol, checkpoint policy, and tracking project. CLI overrides are allowed
only when they are deliberately recorded as a new run configuration.

Before any GPU run, commit this experiment and its data/benchmark artifacts so
the working tree is clean. The trainer refuses a dirty worktree by default.

Run the following gates in order. Keep each output directory: the full run
requires the smoke and tiny-overfit directories as evidence.

## Run on the RunPod machine

Copy the repository there, create/activate the existing CETVEL Python
environment or a fresh Python 3.11 environment, then install current
Qwen3.5-compatible packages. Unsloth's current installer is preferred:

```bash
curl -fsSL https://unsloth.ai/install.sh | sh
pip install --upgrade --no-cache-dir datasets trl accelerate wandb
wandb login
```

Verify that `transformers >= 5`, then perform the no-GPU data gate:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/train.py --mode dry-run
```

Inspect actual rendered messages, token lengths, EOS boundaries, and
assistant-only labels. This writes auditable samples and label-mask counts;
review them before continuing:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/train.py \
  --mode representation-check \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/representation-check
```

Then run pipeline smoke and tiny-overfit tests:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/train.py \
  --mode smoke \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/smoke

python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/train.py \
  --mode tiny-overfit \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/tiny-overfit
```

Only after finite/decreasing loss, W&B logging, checkpoint save, adapter
reload, and a short generation check have passed, start the full run:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/train.py \
  --mode full \
  --smoke-run experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/smoke \
  --tiny-overfit-run experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/tiny-overfit \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/full-v1
```

Do not use `--allow-benchmark-overlap` in a real run. That flag exists only
to diagnose a deliberately expected overlap failure.

## Evaluation protocol

Before the first GPU training run, generate and preserve the base-model raw
outputs. After the full run, generate the candidate outputs exactly once. Both
commands use the pinned model/benchmark revisions and the non-thinking greedy
protocol from `config.yaml`:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/evaluate.py \
  --role base \
  --output experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/eval-base.jsonl

python experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/evaluate.py \
  --role candidate \
  --adapter experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/full-v1/lora-adapter \
  --output experiments/response-style-control/qwen3.5-4b/exp-003-unsloth-sft/results/eval-candidate.jsonl
```

Randomize the two JSONL output columns into anonymous A/B labels, then score
them according to `exp-002-communication-policy-benchmark/scoring-rubric.md`.
Keep the raw JSONL files and their adjacent manifests; do not replace them.

## What this run does not claim

- Training loss is not a communication-policy score.
- It does not create a validation split from synthetic source templates.
- It does not prove improvement until the base and adapter are generated with
  the same non-thinking inference protocol on the blind 100-prompt benchmark.
- A seed improves repeatability, but CUDA/Triton operations can still retain
  small nondeterministic effects; the recorded environment makes them auditable.
- The held-out test is a final paired comparison, not a hyperparameter or
  checkpoint-selection tool. A future recipe iteration must add development
  prompts and reserve a fresh final holdout.
