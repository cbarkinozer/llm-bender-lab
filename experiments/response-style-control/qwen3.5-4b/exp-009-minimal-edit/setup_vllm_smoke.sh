#!/usr/bin/env bash
set -euo pipefail
unset UV_NO_CACHE
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/.local/share/uv/python
uv venv --python 3.11 /workspace/.venvs/exp009-vllm
uv pip install --python /workspace/.venvs/exp009-vllm/bin/python vllm==0.20.1 transformers==4.57.6
uv pip freeze --python /workspace/.venvs/exp009-vllm/bin/python > /workspace/exp009-vllm-freeze.txt
