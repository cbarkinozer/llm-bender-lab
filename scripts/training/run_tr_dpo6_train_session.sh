#!/usr/bin/env bash
# Pod side: exp-006 training runs, each followed by sampling the merged model on the evaluation prompts and deleting the merged weights.
# Needs the pref-rl venv (pod_bootstrap_preference_rl.sh), the lfm3-stage venv (vLLM) and $ROOT/pairs-trainer.jsonl, $ROOT/prompts-eval.jsonl.
# Status: $ROOT/train-status.txt. Every run writes a new directory under $ROOT/runs and $ROOT/eval/<name>; existing ones are skipped.
#   STAGES (default: overfit sweep): overfit | sweep | one:NAME:KIND:BETA:EPOCHS:SEED   (KIND = dpo | sft; sft = same trainer with DPO weight 0)
#   sweep = sft-e1 sft-e2 and dpo beta {0.1, 0.05, 0.3} x {1, 2} epochs, seed 42, per-lane metrics off
#   EVAL_TEMPS: sampling temperatures of the evaluation prompts (default 0.7,0.7,0.7,0.7 = four samples at T 0.7)
set -uo pipefail
ROOT=/workspace/tr-dpo6
PY=/workspace/.venvs/pref-rl/bin/python
SPY=/workspace/.venvs/lfm3-stage/bin/python
EXP021_COMMIT=6e4f0b7658b115a28da971f82ff4009f63bed612
PAIRS=$ROOT/pairs-trainer.jsonl
EVAL_TEMPS=${EVAL_TEMPS:-0.7,0.7,0.7,0.7}
STAGES=${STAGES:-"overfit sweep"}
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1 PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
cd $ROOT/repo || exit 1
mkdir -p $ROOT/runs $ROOT/logs $ROOT/eval
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $ROOT/train-status.txt; }

if [ ! -f $ROOT/exp021/model.safetensors ]; then
  log "downloading exp-021 weights"
  $PY - <<PYEOF || { log "DOWNLOAD_FAILED"; exit 1; }
from huggingface_hub import snapshot_download
snapshot_download('cbarkinozer/LFM3-1.7B-Turkish-SFT', revision='$EXP021_COMMIT', local_dir='$ROOT/exp021',
                  allow_patterns=['*.json', '*.py', '*.jinja', 'model.safetensors'])
PYEOF
fi

one() {  # name kind beta epochs seed
  local name=$1 kind=$2 beta=$3 epochs=$4 seed=$5
  if [ -e $ROOT/runs/$name ]; then log "SKIP $name (already exists)"; return 0; fi
  local dpo_weight=1.0; [ "$kind" = sft ] && dpo_weight=0
  log "TRAIN $name kind=$kind beta=$beta epochs=$epochs seed=$seed"
  $PY scripts/training/run_tr_dpo_train.py --pairs $PAIRS --arm sft --sft-dir $ROOT/exp021 --out $ROOT/runs/$name \
      --beta $beta --epochs $epochs --seed $seed --dpo-weight $dpo_weight --no-lane-metrics > $ROOT/logs/$name.log 2>&1 \
    || { log "FAILED train $name (see logs/$name.log), stopped"; exit 1; }
  log "SAMPLE $name"
  ( source /workspace/lfm3-stage-env.sh; export PYTHONPATH=scripts/evaluation
    $SPY scripts/training/sample_tr_dpo_candidates.py --prompts $ROOT/prompts-eval.jsonl --output-dir $ROOT/eval/$name \
      --model $ROOT/runs/$name/merged --model-revision '' --temperatures $EVAL_TEMPS > $ROOT/logs/$name-sample.log 2>&1 ) \
    || { log "FAILED sample $name (see logs/$name-sample.log), stopped"; exit 1; }
  rm -rf $ROOT/runs/$name/merged $ROOT/runs/$name/trainer
  log "DONE $name"
}

for stage in $STAGES; do
  case $stage in
    overfit)
      if [ ! -e $ROOT/runs/overfit ]; then
        log "START overfit (32 pairs, 10 epochs, LR 1e-4)"
        $PY scripts/training/run_tr_dpo_train.py --pairs $PAIRS --arm sft --sft-dir $ROOT/exp021 --out $ROOT/runs/overfit --limit-train 32 --epochs 10 --lr 1e-4 --no-merge --no-lane-metrics > $ROOT/logs/overfit.log 2>&1 \
          || { log "FAILED overfit (see logs/overfit.log), stopped"; exit 1; }
      fi
      $PY -c "import json,sys; d=json.load(open('$ROOT/runs/overfit/results.json'))['learning_check']; print(d['passed'], d['values'][-3:]); sys.exit(0 if d['passed'] is True else 1)" >> $ROOT/train-status.txt 2>&1 \
        && log "LEARNING CHECK PASSED" || { log "LEARNING CHECK FAILED, stopped"; exit 1; } ;;
    sweep)
      one dpo-b0.1-e1 dpo 0.1 1 42
      one sft-e1 sft 0.1 1 42
      one dpo-b0.05-e1 dpo 0.05 1 42
      one dpo-b0.3-e1 dpo 0.3 1 42
      one sft-e2 sft 0.1 2 42
      one dpo-b0.1-e2 dpo 0.1 2 42
      one dpo-b0.05-e2 dpo 0.05 2 42
      one dpo-b0.3-e2 dpo 0.3 2 42 ;;
    one:*)
      IFS=: read -r _ n k b e s <<< "$stage"
      one "$n" "$k" "$b" "$e" "$s" ;;
    package)
      (cd $ROOT && tar czf tr-dpo6-train-results.tar.gz --exclude=merged --exclude=trainer runs eval logs train-status.txt && sha256sum tr-dpo6-train-results.tar.gz > tr-dpo6-train-results.sha256 && log "PACKAGED $(du -h tr-dpo6-train-results.tar.gz | cut -f1)") ;;
    *) log "unknown stage $stage" ;;
  esac
done
log "TRAIN6_DONE ($STAGES)"
