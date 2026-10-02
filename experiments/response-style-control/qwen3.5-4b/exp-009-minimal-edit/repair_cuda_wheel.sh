#!/usr/bin/env bash
set -euo pipefail
unset UV_NO_CACHE
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
mkdir -p /workspace/wheels
wheel=/workspace/wheels/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl
curl -L --fail --retry 2 --output "$wheel" 'https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0+cu12torch2.7cxx11abiTRUE-cp311-cp311-linux_x86_64.whl?download=1'
sha256sum "$wheel"
uv pip install --python /workspace/.venvs/exp009-train/bin/python --no-deps "$wheel"
/workspace/.venvs/exp009-train/bin/python - <<'PY'
import unsloth
import torch, transformers, triton
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
print('Validated imports:', torch.__version__, transformers.__version__, triton.__version__)
PY
uv pip freeze --python /workspace/.venvs/exp009-train/bin/python > /workspace/exp009-training-freeze.txt
