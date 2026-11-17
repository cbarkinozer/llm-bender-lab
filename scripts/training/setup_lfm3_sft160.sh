#!/usr/bin/env bash
# Reproduce the validated pilot80 stack in persistent, separate environments.
set -euo pipefail
export HF_HOME=/workspace/.cache/huggingface
export UV_CACHE_DIR=/workspace/.cache/uv
export PIP_CACHE_DIR=/workspace/.cache/pip
export WANDB_DIR=/workspace/.cache/wandb
export UV_HTTP_TIMEOUT=180
mkdir -p /workspace/setup-logs /workspace/.venvs
python3 - <<'PY'
import re,subprocess
text=subprocess.check_output(['nvidia-smi'],text=True)
match=re.search(r'CUDA Version:\s*(\d+)\.(\d+)',text)
assert match and tuple(map(int,match.groups())) >= (13,0), 'Validated Torch/vLLM wheels require CUDA13-capable driver. Stop before install and choose a tested compatible stack.'
print(text)
PY
if ! command -v uv >/dev/null; then python3 -m pip install uv; fi
uv python install 3.12
if [ ! -x /workspace/.venvs/lfm3-sft/bin/python ]; then
  uv venv --python 3.12 /workspace/.venvs/lfm3-sft
fi
uv pip install --python /workspace/.venvs/lfm3-sft/bin/python -r experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/requirements-gpu.txt jinja2==3.1.6
/workspace/.venvs/lfm3-sft/bin/python - <<'PY'
import torch, transformers, trl, peft, datasets, wandb
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
print(torch.__version__,torch.version.cuda,transformers.__version__,torch.cuda.get_device_name())
PY
if [ ! -x /workspace/.venvs/lfm3-vllm/bin/python ]; then
  uv venv --python 3.12 /workspace/.venvs/lfm3-vllm
fi
uv pip install --python /workspace/.venvs/lfm3-vllm/bin/python \
  'https://wheels.vllm.ai/7cc0a8a2b1ef6888b44973933c8a208e91122229/vllm-0.34.0rc1.dev251%2Bg7cc0a8a2b-cp38-abi3-manylinux_2_28_x86_64.whl' \
  torch==2.14.0 transformers==5.20.2 tokenizers==0.23.3 jinja2==3.1.6 sacrebleu==2.5.1 rouge-score==0.1.2
# Some CUDA13 wheels need their bundled runtime directory on the linker path.
CUDA_LIBS=$(/workspace/.venvs/lfm3-vllm/bin/python - <<'PY'
from pathlib import Path
import site
paths=[]
for root in site.getsitepackages():
    paths.extend(str(p) for p in (Path(root)/'nvidia').glob('*/lib') if p.is_dir())
print(':'.join(paths))
PY
)
export LD_LIBRARY_PATH="${CUDA_LIBS}:${LD_LIBRARY_PATH:-}"
printf '%s\n' "export LD_LIBRARY_PATH=\"${CUDA_LIBS}:\${LD_LIBRARY_PATH:-}\"" > /workspace/lfm3-sft160-cuda-env.sh
/workspace/.venvs/lfm3-vllm/bin/python - <<'PY'
import torch,vllm,transformers
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
print(torch.__version__,torch.version.cuda,vllm.__version__,transformers.__version__)
PY
uv pip freeze --python /workspace/.venvs/lfm3-sft/bin/python > /workspace/setup-logs/sft160-train-freeze.txt
uv pip freeze --python /workspace/.venvs/lfm3-vllm/bin/python > /workspace/setup-logs/sft160-vllm-freeze.txt
printf '%s\n' 'Environment imports passed. Actual model-load/generation and training gates still required.'
