#!/usr/bin/env bash
# Pod side: evaluate the exp-003 DPO models with the same suite as exp-021 (scripts/evaluation/run_lfm3_sft_core_model_session.sh), plus the
# held-out Turkish prompts. Stage-major: every arm goes through a stage before the next stage starts, so the arms can be compared early.
#   ARMS="dpo-on-sft dpo-on-base"   (merged models in /workspace/tr-dpo/runs/<arm>/merged)
#   STAGES="heldout guard bel final evalv2 diag writing pack"   (the suite's own stage names, plus heldout = 78 never-trained Turkish prompts)
#   heldout5 = exp-005's 200 held-out data-carrying prompts, two answers each (temperature 0.1 = the judged answer, 0.7 = sensitivity check)
#   exp-021 itself is an arm for the heldout stages only: ln -s /workspace/tr-dpo/exp021 /workspace/tr-dpo/runs/exp021/merged
# Needs the lfm3-stage venv (vLLM), the uploaded repo files in $EV/repo and $EV/sft-core/prompts-render-final.jsonl. Status: $EV/eval-status.txt
set -uo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface UV_CACHE_DIR=/workspace/.cache/uv HF_HUB_DISABLE_XET=1
EV=/workspace/lfm3-evalv2
TR=/workspace/tr-dpo
PY=/workspace/.venvs/lfm3-stage/bin/python
ARMS=${ARMS:-"dpo-on-sft dpo-on-base"}
STAGES=${STAGES:-"heldout guard bel final evalv2 diag writing pack"}
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $EV/eval-status.txt; }
cd $EV/repo || exit 1
export PYTHONPATH=$EV/vendor
mkdir -p $EV/models $EV/sft-core $EV/vendor

if [ ! -f $EV/env-ready ]; then
  log "guard packages"
  UV=$(command -v uv || echo /root/.local/bin/uv)
  $UV pip install --python $PY "nltk==3.8.1" absl-py langdetect immutabledict pyarrow > $EV/setup-eval.log 2>&1 || { log "PIP_FAILED"; exit 1; }
  $PY -c "import nltk; print(nltk.download('punkt', download_dir='/workspace/nltk_data'))" >> $EV/setup-eval.log 2>&1
  grep -q "export NLTK_DATA" /workspace/lfm3-stage-env.sh || echo "export NLTK_DATA=/workspace/nltk_data" >> /workspace/lfm3-stage-env.sh
  source /workspace/lfm3-stage-env.sh
  $PY scripts/evaluation/lfm3_guard_eval.py prepare --data-dir $EV/guard-data > $EV/guard-prepare.log 2>&1 || { log "GUARD_PREPARE_FAILED"; exit 1; }
  touch $EV/env-ready
fi

for arm in $ARMS; do
  src=$TR/runs/$arm/merged
  [ -f $src/model.safetensors ] || { log "NO_MODEL $arm"; exit 1; }
  ln -sfn $src $EV/models/$arm
done
for stage in $STAGES; do
  for arm in $ARMS; do
    name=$arm
    if [ "$stage" = heldout ]; then
      out=$TR/heldout/$arm
      if [ ! -f $out/answers.jsonl ]; then
        $PY - <<PYEOF
import json
ids = set(json.load(open('$EV/holdout-ids.json')))
rows = [json.loads(l) for l in open('$EV/repo/experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality/data/prompts-tr-dpo.jsonl', encoding='utf-8')]
keep = [r for r in rows if r['id'] in ids]
assert len(keep) == len(ids), (len(keep), len(ids))
open('$TR/prompts-heldout.jsonl', 'w', encoding='utf-8', newline='\n').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in keep))
PYEOF
        mkdir -p $TR/heldout
        $PY scripts/training/sample_tr_dpo_candidates.py --prompts $TR/prompts-heldout.jsonl --output-dir $out --model $EV/models/$name --model-revision '' > $TR/heldout/$arm.log 2>&1
      fi
    elif [ "$stage" = heldout5 ]; then
      out=$TR/heldout5/$arm
      if [ ! -f $out/answers.jsonl ]; then
        mkdir -p $TR/heldout5
        $PY scripts/training/sample_tr_dpo_candidates.py --prompts $EV/repo/experiments/preference-rl/lfm3-1.7b/exp-005-dpo-repaired-turkish/results-local/heldout-prompts.jsonl \
            --output-dir $out --model $EV/models/$name --model-revision '' --temperatures 0.1,0.7 > $TR/heldout5/$arm.log 2>&1
      fi
    else
      STAGES="$stage" bash scripts/evaluation/run_lfm3_sft_core_model_session.sh "$name"
    fi
    log "STAGE_DONE $stage $name"
  done
done
if [[ " $STAGES " == *" pack "* ]]; then  # the suite packs its own results per model (sft-core/<name>-results.tar.gz); the held-out answers go in one more tarball
  (cd $TR && tar czf tr-dpo-heldout.tar.gz heldout heldout5 prompts-heldout.jsonl 2>/dev/null; sha256sum tr-dpo-heldout.tar.gz > tr-dpo-heldout.sha256)
fi
log "EVAL_DONE ($ARMS; $STAGES)"
