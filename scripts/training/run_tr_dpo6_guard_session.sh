#!/usr/bin/env bash
# Pod side: rule 4 guards for exp-006. Re-merges the kept adapters into exp-021, then runs the exp-021 suite (math final test, eval v2 math and tool calls,
# Belebele, TurBLiMP, IFEval and HumanEval) on exp-021 itself and on every arm, in one session so the decoding is identical.
#   ARMS="dpo-s101 sft-s101 ..."  (adapters in /workspace/tr-dpo6/runs/<arm>/adapter)   STAGES="final evalv2 bel guard"
# Waits until the training session is finished (one GPU). Status: $EV/guard-status.txt; results: $EV/exp006-guard-results.tar.gz
set -uo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface UV_CACHE_DIR=/workspace/.cache/uv HF_HUB_DISABLE_XET=1
R6=/workspace/tr-dpo6
EV=/workspace/lfm3-evalv2
PY=/workspace/.venvs/lfm3-stage/bin/python
PREF=/workspace/.venvs/pref-rl/bin/python
ARMS=${ARMS:-"dpo-s101 sft-s101"}
STAGES=${STAGES:-"final evalv2 bel guard"}
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $EV/guard-status.txt; }
cd $EV/repo || exit 1
export PYTHONPATH=$EV/vendor
mkdir -p $EV/models $EV/sft-core $EV/vendor

while pgrep -f run_tr_dpo6_train_session.sh > /dev/null; do sleep 30; done
log "training session finished, guards start"

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

ln -sfn $R6/exp021 $EV/models/exp021
for arm in $ARMS; do
  [ -f $EV/models/$arm/merge-receipt.json ] && continue
  want=$($PREF -c "import json; print(json.load(open('$R6/runs/$arm/results.json')).get('merged_sha256') or '')" 2>/dev/null)
  [ -n "$want" ] || want=$(grep -o '"merged_sha256": *"[0-9a-f]*"' $R6/runs/$arm/*manifest*.json 2>/dev/null | head -1 | grep -o '[0-9a-f]\{64\}')
  log "merge $arm"
  $PREF scripts/training/merge_tr_dpo6_adapter.py --parent $R6/exp021 --adapter $R6/runs/$arm/adapter --out $EV/models/$arm \
      ${want:+--expect-sha256 $want} >> $EV/guard-merge.log 2>&1 || { log "MERGE_FAILED $arm"; exit 1; }
  log "merged $arm: $(grep -o '"matches_trainer": [a-z]*' $EV/models/$arm/merge-receipt.json)"
done
# overfit check: the same sampling as the held-out run, on 300 training prompts ($R6/prompts-trainsub.jsonl; 149 of them have pairs in the training set)
for arm in $ARMS; do
  [ -f $R6/eval-trainsub/$arm/answers.jsonl ] && continue
  log "sample training prompts $arm"
  PYTHONPATH=scripts/evaluation:$EV/vendor $PY scripts/training/sample_tr_dpo_candidates.py --prompts $R6/prompts-trainsub.jsonl       --output-dir $R6/eval-trainsub/$arm --model $EV/models/$arm --model-revision '' --temperatures 0.7,0.7,0.7,0.7 > $R6/logs/trainsub-$arm.log 2>&1     || { log "FAILED trainsub $arm"; exit 1; }
done
for arm in exp021 $ARMS; do
  for st in $STAGES; do
    STAGES="$st" bash scripts/evaluation/run_lfm3_sft_core_model_session.sh "$arm" > /dev/null 2>&1
    log "STAGE_DONE $st $arm"
  done
done
(cd $EV && tar czf exp006-guard-results.tar.gz $(for a in exp021 $ARMS; do for d in sft-core/verified-$a-final.jsonl sft-core/verified-$a-final.summary.json models/$a/merge-receipt.json runs/$a-think-on belebele-runs/$a turblimp/$a guard-runs/$a guard-runs/$a-rest; do [ -e $d ] && echo $d; done; done) guard-status.txt guard-merge.log ../tr-dpo6/eval-trainsub 2>/dev/null \
  && sha256sum exp006-guard-results.tar.gz > exp006-guard-results.sha256)
log "GUARDS_DONE ($ARMS; $STAGES)"
