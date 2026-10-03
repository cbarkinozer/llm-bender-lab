#!/usr/bin/env bash
set -euo pipefail
unset UV_NO_CACHE
export HF_HOME=/workspace/.cache/huggingface
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/.local/share/uv/python
mkdir -p /workspace/.venvs /workspace/.cache/wandb /workspace/wheels
uv python install 3.11.16
uv venv --python 3.11.16 /workspace/.venvs/exp010-train
uv pip install --python /workspace/.venvs/exp010-train/bin/python torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
# Exact previous freeze, no dependency re-resolution or optional torchao/xformers.
uv pip install --python /workspace/.venvs/exp010-train/bin/python --no-deps -r "$(dirname "$0")/requirements-exp009.txt"
wheel=/workspace/wheels/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl
curl -L --fail --retry 2 --output "$wheel" 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl?download=1'
echo '6d04c5b9c675dd68aa4ece694d3c5d1d79b25326757bae567aeb2edfe1dd5cc2  /workspace/wheels/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl' | sha256sum --check
uv pip install --python /workspace/.venvs/exp010-train/bin/python --no-deps "$wheel"
/workspace/.venvs/exp010-train/bin/python - <<'PY'
import unsloth
import torch, transformers, triton
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
print('Validated imports:',torch.__version__,transformers.__version__,triton.__version__)
PY
uv pip freeze --python /workspace/.venvs/exp010-train/bin/python > /workspace/exp010-training-freeze.txt
