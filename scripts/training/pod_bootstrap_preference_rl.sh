#!/usr/bin/env bash
# Pod-side bootstrap for the preference-rl experiments (DPO, GRPO on LFM3-1.7B): a venv with the library versions the Liquid
# cookbook notebooks were tested with, then the CPU self-check of the tool-call scorer. Fresh Vast RTX 4090 pod, run from the repo root.
set -uo pipefail
R=${PREFRL_ROOT:-/workspace/pref-rl}
STATUS=$R/bootstrap-status.txt
mkdir -p $R/logs
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$STATUS"; }
export HF_HOME=/workspace/.cache/huggingface UV_CACHE_DIR=/workspace/.cache/uv UV_HTTP_TIMEOUT=180 HF_HUB_DISABLE_XET=1
mkdir -p /workspace/.venvs
cd $R/repo || { log "NO_REPO"; exit 1; }
log "driver check"
python3 - <<'PY' || { log "DRIVER_TOO_OLD"; exit 1; }
import re, subprocess
s = subprocess.check_output(['nvidia-smi'], text=True)
m = re.search(r'CUDA(?: UMD)? Version:\s*(\d+)\.(\d+)', s)
assert m and tuple(map(int, m.groups())) >= (13, 0), 'pinned torch wheels need a CUDA 13 capable driver'
print(s.splitlines()[8] if len(s.splitlines()) > 8 else s)
PY
command -v uv >/dev/null || python3 -m pip install uv
UV=$(command -v uv || echo /root/.local/bin/uv)
$UV python install 3.12 >> $R/logs/setup.log 2>&1
[ -x /workspace/.venvs/pref-rl/bin/python ] || $UV venv --python 3.12 /workspace/.venvs/pref-rl >> $R/logs/setup.log 2>&1
PY=/workspace/.venvs/pref-rl/bin/python
log "install pinned libraries"
ok=0
for try in 1 2 3 4 5; do
  $UV pip install --python $PY "torch==2.14.1" "torchvision==0.29.1" "torchao==0.18.0" "trl==1.16.0" "transformers==5.20.2" "peft==0.21.2" \
    "accelerate==1.15.0" "datasets==5.1.0" "huggingface-hub==2.3.0" "tokenizers==0.23.3" "safetensors==0.8.0" pyarrow >> $R/logs/setup.log 2>&1 && { ok=1; break; }
  log "install attempt $try failed, retrying"; sleep 15
done
[ $ok = 1 ] || { log "PIP_FAILED"; exit 1; }
$UV pip freeze --python $PY > $R/logs/environment.txt
$PY - <<'PY' >> $R/logs/setup.log 2>&1 || { log "ENV_CHECK_FAILED"; exit 1; }
import torch, transformers, trl, peft
assert torch.cuda.is_available() and torch.cuda.is_bf16_supported(), 'no CUDA bf16'
print(torch.__version__, transformers.__version__, trl.__version__, peft.__version__, torch.cuda.get_device_name(), torch.cuda.mem_get_info())
PY
log "versions: $($PY -c 'import torch,transformers,trl,peft;print(torch.__version__,transformers.__version__,trl.__version__,peft.__version__)')"
log "scorer self-check (CPU)"
$PY scripts/evaluation/check_phone_tools_scoring.py --out $R/logs/scorer-check.json > $R/logs/scorer-check.log 2>&1 || { log "SCORER_CHECK_FAILED"; exit 1; }
log "BOOTSTRAP_DONE"
