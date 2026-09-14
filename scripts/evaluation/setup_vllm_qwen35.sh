#!/usr/bin/env bash
set -euo pipefail

# Keep the fast serving stack independent from the pinned Transformers/CETVEL
# environment. Qwen3.5 requires a current vLLM build rather than an old stable
# release, and installation may select a newer compatible Torch stack.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
venv_dir="${VLLM_QWEN35_VENV:-/workspace/.venvs/vllm-qwen35}"
log_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/vllm-setup"
mkdir -p "${log_dir}"
exec > >(tee "${log_dir}/setup-$(date -u +%Y%m%dT%H%M%SZ).log") 2>&1

# Only /workspace persists across container restarts and has real room;
# the container's own root overlay is small (~20GB) and already filled up
# once this session from caches defaulting there. vLLM's install (torch +
# CUDA libs) and any later model download are both multi-GB.
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-/workspace/.cache/pip}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"

python3 -m venv "${venv_dir}"
source "${venv_dir}/bin/activate"
python -m pip install --upgrade pip uv

# Official Qwen3.5 guidance requires a current vLLM build. uv resolves the
# compatible Torch backend inside this isolated environment.
uv pip install vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly

# This vLLM nightly resolves a torch build (2.13+cu129) alongside a
# vllm._C_stable_libtorch extension linked against the CUDA 13 stable ABI,
# which needs libcudart.so.13 from the nvidia-cu13 wheel. That wheel lands in
# site-packages but isn't on the dynamic linker path by default (unlike the
# cu12 runtime package, which is), so `import vllm` fails with
# "ImportError: libcudart.so.13: cannot open shared object file" unless its
# lib dir is added explicitly. Persist this for every later invocation of
# this venv (activation alone doesn't set LD_LIBRARY_PATH).
cu13_lib_dir="${venv_dir}/lib/python3.11/site-packages/nvidia/cu13/lib"
if [ -d "${cu13_lib_dir}" ]; then
  printf 'export LD_LIBRARY_PATH="%s:${LD_LIBRARY_PATH:-}"\n' "${cu13_lib_dir}" >> "${venv_dir}/bin/activate"
fi
export LD_LIBRARY_PATH="${cu13_lib_dir}:${LD_LIBRARY_PATH:-}"

python - <<'PY'
import json
import platform
import subprocess
import sys
import torch
import vllm

print(json.dumps({
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "vllm": vllm.__version__,
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "pip_freeze": subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines(),
}, indent=2))
PY
