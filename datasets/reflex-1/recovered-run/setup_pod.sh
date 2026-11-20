#!/usr/bin/env bash
set -euo pipefail
cd /workspace/reflex-decision
export HF_HOME=/workspace/reflex-decision/cache/huggingface
export PIP_CACHE_DIR=/workspace/reflex-decision/cache/pip
export UV_CACHE_DIR=/workspace/reflex-decision/cache/uv
uv venv --seed --python 3.11 .venv
uv pip install --python .venv/bin/python torch==2.8.0 torchvision torchaudio==2.8.0 triton==3.4.0 bitsandbytes xformers==0.0.32.post2 unsloth unsloth_zoo transformers==5.2.0 trl==0.22.2 wandb datasets huggingface_hub
uv pip install --python .venv/bin/python --no-deps git+https://github.com/unslothai/unsloth.git@a70b2a8 git+https://github.com/unslothai/unsloth-zoo.git@ea7c1b2d9eb5daf0bc6036bf68032795868f2d74
.venv/bin/python -m pip freeze > environment-freeze.txt
.venv/bin/python -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__, torch.cuda.get_device_name(0)); import unsloth; from unsloth import FastDecisionModel, DecisionTrainer; import transformers, trl, wandb; print("Training imports passed")'
