#!/usr/bin/env bash
set -euo pipefail
export HF_HOME=/workspace/.cache/huggingface
export UV_CACHE_DIR=/workspace/.cache/uv
export PIP_CACHE_DIR=/workspace/.cache/pip
export HF_HUB_DISABLE_TELEMETRY=1
mkdir -p /workspace/cetvel-500-support
exec > >(tee /workspace/cetvel-500-support/setup-vllm.log) 2>&1
date -u
nvidia-smi -q > /workspace/cetvel-500-support/nvidia-smi-before.txt
if [[ ! -x /workspace/.venvs/cetvel-vllm/bin/python ]]; then
  uv venv --python 3.12 /workspace/.venvs/cetvel-vllm
fi
uv pip install --python /workspace/.venvs/cetvel-vllm/bin/python \
  'vllm==0.30.0' 'torch==2.13.0' 'transformers==5.18.0' \
  'sacrebleu==2.5.1' 'rouge-score==0.1.2' 'peft==0.21.2'
uv pip freeze --python /workspace/.venvs/cetvel-vllm/bin/python > /workspace/cetvel-500-support/pip-freeze.txt
site_dir=$(/workspace/.venvs/cetvel-vllm/bin/python -c 'import site; print(site.getsitepackages()[0])')
export LD_LIBRARY_PATH="${site_dir}/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}"
/workspace/.venvs/cetvel-vllm/bin/python -c 'import torch,vllm,transformers; print(torch.__version__,torch.version.cuda,vllm.__version__,transformers.__version__); assert torch.cuda.is_available(); assert torch.version.cuda == "13.0"; assert vllm.__version__ == "0.30.0"; assert transformers.__version__ == "5.18.0"'
/workspace/.venvs/cetvel-vllm/bin/python -c "from huggingface_hub import snapshot_download; print(snapshot_download('unsloth/Qwen3.5-4B',revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'))"
date -u
touch /workspace/cetvel-500-support/setup-completed
