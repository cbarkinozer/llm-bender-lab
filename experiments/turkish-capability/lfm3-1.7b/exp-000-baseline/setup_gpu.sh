#!/usr/bin/env bash
set -euo pipefail
# Run from repository root on Linux with Python 3.12. No Docker required.
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
python3.12 -m venv /workspace/.venvs/lfm3
PY=/workspace/.venvs/lfm3/bin/python
"$PY" -m pip install -r experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/requirements-gpu.txt
"$PY" -m pip check
"$PY" -c 'import torch,transformers,trl,peft,datasets; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); print(torch.__version__,transformers.__version__,torch.cuda.get_device_name())'
nvidia-smi
