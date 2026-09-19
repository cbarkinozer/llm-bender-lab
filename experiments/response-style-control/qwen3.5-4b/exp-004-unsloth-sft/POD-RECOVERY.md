# Pod recovery notes for exp-003

This experiment was completed on an RTX 4090 (24 GB) using the fast environment
below. The original Torch 2.4/Triton 3.0 environment made Unsloth fall back to
the slow PyTorch implementation; do not reuse it for the reportable run.

## Recreate the validated environment

```bash
python3 -m venv /workspace/.venvs/qwen-fast
source /workspace/.venvs/qwen-fast/bin/activate
python -m pip install --upgrade pip
pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu128
pip install 'transformers==5.5.0' 'trl==0.24.0' 'accelerate==1.10.1' \
  'datasets==5.0.1' 'wandb' 'peft' 'bitsandbytes'
pip install 'unsloth==2026.9.6' 'unsloth_zoo==2026.9.5' \
  'flash-linear-attention==0.5.2' 'fla-core==0.5.2' 'einops==0.8.2'
pip install 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl'
python -c "import torch,triton; import fla; print(torch.__version__, torch.version.cuda, triton.__version__)"
```

Expected output includes Torch `2.7.1+cu128`, CUDA `12.8`, Triton `3.3.1`, and
an importable `fla` package. The direct `causal-conv1d` wheel is intentional:
building it from source attempted to install an incompatible newer Torch/CUDA
toolchain.

## Fresh-pod check (2026-09-19)

The new RTX 4090 pod started from the base image with Torch `2.4.1+cu124`
and Triton `3.0.0`, with no Unsloth stack installed. Installing the current
`unsloth==2026.9.6` with normal dependency resolution upgraded Torch to
`2.12.1+cu130`; that is not the reportable setup for this experiment.
Re-pin Torch, Triton, and torchvision after installing Unsloth:

```bash
pip install --force-reinstall --no-deps 'torch==2.7.1' 'triton==3.3.1' \
  --index-url https://download.pytorch.org/whl/cu128
pip install --force-reinstall --no-deps 'torchvision==0.22.1' \
  --index-url https://download.pytorch.org/whl/cu128
```

The resolver-installed `torchao` and `xformers` wheels target the newer Torch
stack and make `transformers` fail at import (`ScalingType` is missing in
Torch 2.7). They are optional for this run and were removed:

```bash
pip uninstall -y torchao xformers
```

Imports were then verified on the RTX 4090: Torch `2.7.1+cu128`, CUDA runtime
`12.8`, Triton `3.3.1`, Transformers `5.5.0`, FLA `0.5.2`, and Unsloth
`2026.9.6`. The supplied causal-conv1d wheel imports but reports that its C++
extension is skipped for Torch <2.11; this must be recorded in the run
manifest and not silently described as fully accelerated.

## W&B

```bash
export WANDB_MODE=online
export WANDB_API_KEY='replace-with-your-key'
/workspace/.venvs/qwen-fast/bin/wandb login "$WANDB_API_KEY"
```

Never commit the key. The project is
`llm-bender-lab-response-style-control`.

## Experiment commands

Run from `/workspace/llm-bender-lab` with the exact config and immutable model
revision in `config.yaml`. Validate representation, smoke, and tiny-overfit
before starting `--mode full`; use separate output directories for any rerun.
The reportable final adapter is saved under `results/full-fast/lora-adapter`.

The final benchmark must use `evaluate.py` twice (`--role base` and
`--role candidate --adapter ...`) with the same frozen `test.csv`. Build the
blind paired review file with `scripts/evaluation/build_blind_review.py`; import
only `results/blind-review/argilla-review.csv` into Argilla. Keep
`blind-mapping-sealed.json` private until human scoring is frozen.

## Local artifacts already saved

`exp-003-repro-bundle.tar.gz` contains the final adapter, all run manifests and
logs, raw base/candidate outputs, blind review files, reproducibility snapshots,
and the W&B run data. Its verified SHA-256 is recorded beside the archive in
the handoff notes.
## Benchmark inference incident (2026-09-19)

The first candidate benchmark attempt appeared stalled before writing its first
JSONL row. The process was not deadlocked: Qwen3.5's first generation triggered
slow kernel/backend initialization, and the Transformers/Unsloth fallback showed
near-zero sampled GPU utilization while the CPU remained busy. A single
16-token diagnostic response eventually completed; a subsequent three-item
run also completed and flushed each row successfully.

The original evaluator had no progress output and did not flush after each row,
which made this look like a hang and risked losing progress. It was patched to
support `--limit` and `--max-new-tokens`, print `generating` / `completed`
markers, and flush JSONL after every item. The full candidate benchmark was
then launched in the background with unbuffered logging and line-count checks.

This is an inference-backend performance limitation, not a training failure:
the SFT smoke, tiny-overfit, and full training runs completed successfully.

## Argilla review protocol

The Argilla dataset `exp-004-v2-blind-benchmark` intentionally uses a compact
review form. For each prompt, the reviewer only selects `A`, `B`, or `Equal`
for the better response. An optional note is available for a consequential
error or an explanation, but the reviewer does not fill separate true/false
fields for every policy dimension. Length checks and pattern diagnostics remain
in the offline CSV/manifest and are not part of the manual burden.
