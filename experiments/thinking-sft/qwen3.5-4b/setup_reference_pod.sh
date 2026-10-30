#!/usr/bin/env bash
set -euo pipefail
# Explicit persistent paths. No secrets or training data are required.
export HF_HOME=/workspace/.cache/huggingface
export PIP_CACHE_DIR=/workspace/.cache/pip
export UV_CACHE_DIR=/workspace/.cache/uv
mkdir -p /workspace/occam2-reference /workspace/.venvs "$HF_HOME" "$PIP_CACHE_DIR" "$UV_CACHE_DIR"
venv_path=/workspace/.venvs/occam2-reference
if [[ ! -x "$venv_path/bin/python" ]]; then
  uv venv --seed --python /venv/main/bin/python "$venv_path"
fi
uv pip install --python "$venv_path/bin/python" \
  'torch==2.14.1' 'transformers==5.20.2' 'peft==0.21.2' \
  'accelerate==1.15.0' 'safetensors==0.8.0' pillow
"$venv_path/bin/python" -m pip freeze > /workspace/occam2-reference/requirements.lock.txt
nvidia-smi > /workspace/occam2-reference/nvidia-smi.txt
"$venv_path/bin/python" - <<'PY'
import json,torch,importlib.metadata as m
from pathlib import Path
from transformers import Qwen3_5ForConditionalGeneration,AutoTokenizer
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
report=dict(gpu=torch.cuda.get_device_name(),cuda=torch.version.cuda,
            versions={k:m.version(k) for k in ['torch','transformers','peft','accelerate','safetensors']})
Path('/workspace/occam2-reference/environment.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
PY
