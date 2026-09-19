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
