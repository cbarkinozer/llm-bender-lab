#!/usr/bin/env bash
set -euo pipefail
unset UV_NO_CACHE
export HF_HOME=/workspace/.cache/huggingface
export PIP_CACHE_DIR=/workspace/.cache/pip
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/.local/share/uv/python
mkdir -p /workspace/.venvs /workspace/.cache/wandb
uv python install 3.11
uv venv --python 3.11 /workspace/.venvs/exp009-train
uv pip install --python /workspace/.venvs/exp009-train/bin/python torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python /workspace/.venvs/exp009-train/bin/python torch==2.7.1 torchvision==0.22.1 triton==3.3.1 transformers==5.5.0 trl==0.24.0 accelerate==1.10.1 datasets==5.0.1 flash-linear-attention==0.5.2 fla-core==0.5.2 einops==0.8.2 peft bitsandbytes wandb pyyaml sentencepiece protobuf tyro hf_transfer
uv pip install --python /workspace/.venvs/exp009-train/bin/python --no-deps unsloth==2026.9.6 unsloth_zoo==2026.9.5
uv pip install --python /workspace/.venvs/exp009-train/bin/python --no-deps 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl'
/workspace/.venvs/exp009-train/bin/python - <<'PY'
import unsloth
import torch, transformers, triton
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
print('Validated imports:', torch.__version__, transformers.__version__, triton.__version__)
PY
uv pip freeze --python /workspace/.venvs/exp009-train/bin/python > /workspace/exp009-training-freeze.txt
