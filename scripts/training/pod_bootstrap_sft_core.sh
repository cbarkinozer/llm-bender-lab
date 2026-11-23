#!/usr/bin/env bash
# One-pass pod bootstrap for the SFT core campaign (fresh Vast RTX 4090): environment, guard data, CPT parent merge.
set -uo pipefail
R=/workspace/lfm3-evalv2
STATUS=$R/bootstrap-status.txt
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$STATUS"; }
cd $R/repo
log "setup venv (vllm, torch, transformers)"
ok=0; for try in 1 2 3 4 5; do bash scripts/training/setup_lfm3_stage_diagnostic.sh >> $R/setup.log 2>&1 && { ok=1; break; }; log "setup attempt $try failed, retrying"; sleep 15; done; [ $ok = 1 ] || { log "SETUP_FAILED"; exit 1; }
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface UV_CACHE_DIR=/workspace/.cache/uv HF_HUB_DISABLE_XET=1
PY=/workspace/.venvs/lfm3-stage/bin/python
UV=$(command -v uv || echo /root/.local/bin/uv)
log "install training and guard packages"
$UV pip install --python $PY trl==1.16.0 datasets==5.1.0 torch==2.14.0 transformers==5.20.2 peft==0.21.2 accelerate==1.15.0 "nltk==3.8.1" absl-py langdetect immutabledict pyarrow > $R/setup2.log 2>&1 || { log "PIP_FAILED"; exit 1; }
$PY -c "import nltk; print(nltk.download('punkt', download_dir='/workspace/nltk_data'))" >> $R/setup2.log 2>&1
grep -q "export NLTK_DATA" /workspace/lfm3-stage-env.sh || echo "export NLTK_DATA=/workspace/nltk_data" >> /workspace/lfm3-stage-env.sh
source /workspace/lfm3-stage-env.sh
export PYTHONPATH=$R/vendor
log "guard data prepare"
$PY scripts/evaluation/lfm3_guard_eval.py prepare --data-dir $R/guard-data > $R/guard-prepare.log 2>&1 || { log "GUARD_PREPARE_FAILED"; exit 1; }
log "merge CPT parent"
mkdir -p $R/models $R/runs/logs
$PY scripts/evaluation/merge_lfm3_adapter.py --adapter cbarkinozer/LFM3-1.7B-Turkish-CPT --adapter-revision 6f213ec25a944dab2fbdeb6d337deb0e0442e638 \
    --expected-sha256 f4562118c3196462d73649198d856450714ae67081cd6af7df851f59dccf5e46 --output $R/models/cpt > $R/merge-cpt.log 2>&1 || { log "MERGE_FAILED"; exit 1; }
log "versions: $($PY -c 'import torch,transformers,trl,peft,vllm;print(torch.__version__,transformers.__version__,trl.__version__,peft.__version__,vllm.__version__)' 2>&1 | tail -1)"
log "BOOTSTRAP_DONE"
