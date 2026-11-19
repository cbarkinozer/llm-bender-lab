#!/usr/bin/env bash
# Run only on the next owner-provided GPU, after archive SHA verification/extraction.
set -euo pipefail
export HF_HOME=/workspace/.cache/huggingface UV_CACHE_DIR=/workspace/.cache/uv UV_HTTP_TIMEOUT=180 HF_HUB_DISABLE_XET=1
mkdir -p /workspace/.venvs /workspace/stage-setup-logs
python3 - <<'PY'
import re,subprocess
s=subprocess.check_output(['nvidia-smi'],text=True)
m=re.search(r'CUDA(?: UMD)? Version:\s*(\d+)\.(\d+)',s)
assert m and tuple(map(int,m.groups()))>=(13,0),'Pinned wheels need CUDA13-capable driver'
print(s)
PY
if ! command -v uv >/dev/null; then python3 -m pip install uv; fi
uv python install 3.12
if [ ! -x /workspace/.venvs/lfm3-stage/bin/python ]; then uv venv --python 3.12 /workspace/.venvs/lfm3-stage; fi
P=/workspace/.venvs/lfm3-stage/bin/python
uv pip install --python "$P" 'https://wheels.vllm.ai/7cc0a8a2b1ef6888b44973933c8a208e91122229/vllm-0.34.0rc1.dev251%2Bg7cc0a8a2b-cp38-abi3-manylinux_2_28_x86_64.whl' torch==2.14.0 transformers==5.20.2 tokenizers==0.23.3 huggingface-hub==2.4.0 peft==0.21.2 accelerate==1.15.0 jinja2==3.1.6 httpx==0.28.1
CUDA_LIBS=$($P - <<'PY'
from pathlib import Path
import site
print(':'.join(str(p) for root in site.getsitepackages() for p in (Path(root)/'nvidia').glob('*/lib') if p.is_dir()))
PY
)
export LD_LIBRARY_PATH="${CUDA_LIBS}:${LD_LIBRARY_PATH:-}"
printf '%s\n' "export HF_HOME=/workspace/.cache/huggingface" "export HF_HUB_DISABLE_XET=1" "export LD_LIBRARY_PATH=\"${CUDA_LIBS}:\${LD_LIBRARY_PATH:-}\"" > /workspace/lfm3-stage-env.sh
$P - <<'PY'
import sys,torch,vllm,transformers
assert sys.version_info[:2]==(3,12)
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
assert vllm.__version__=='0.34.0rc1.dev251+g7cc0a8a2b'
print(sys.version,torch.__version__,transformers.__version__,vllm.__version__)
PY
uv pip freeze --python "$P" > /workspace/stage-setup-logs/environment.txt
echo SETUP_PASSED
