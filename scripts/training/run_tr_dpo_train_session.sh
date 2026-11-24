#!/usr/bin/env bash
# Pod side: preference-rl exp-003 training stages, one after the other (needs the pref-rl venv from pod_bootstrap_preference_rl.sh and the
# exp-021 weights in $ROOT/exp021 from run_tr_dpo_sampling_session.sh). Every stage writes a new directory under $ROOT/runs; status in $ROOT/train-status.txt.
#   overfit     playbook tiny-overfit check: 32 pairs, 10 epochs, LR 1e-4, arm sft, no merge; rewards/accuracies must reach .9
#   dpo-on-sft     DPO over exp-021 on the pairs file, the notebook's recipe
#   dpo-on-base    the same pairs over the original LFM3-1.7B
#   variant     a documented variant of a run (VARIANT_NAME, VARIANT_ARGS), for example more epochs
#   package     tar + sha256 of the adapters and manifests (the merged weights stay on the pod for the evaluation stages)
set -uo pipefail
ROOT=/workspace/tr-dpo
PY=/workspace/.venvs/pref-rl/bin/python
PAIRS=$ROOT/pairs-dpo.jsonl
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1 PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
STAGES=${STAGES:-"overfit dpo-on-sft dpo-on-base"}
cd $ROOT/repo || exit 1
mkdir -p $ROOT/runs $ROOT/logs
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $ROOT/train-status.txt; }
run() {  # name, command...
  local name=$1; shift
  if [ -e $ROOT/runs/$name ]; then log "SKIP $name (already exists)"; return 0; fi
  log "START $name"
  "$@" > $ROOT/logs/$name.log 2>&1 && log "DONE $name" || { log "FAILED $name (see logs/$name.log), stopped"; exit 1; }
}
T="$PY scripts/training/run_tr_dpo_train.py --pairs $PAIRS"
for stage in $STAGES; do
  case $stage in
    overfit)
      run tr-dpo-overfit $T --arm sft --sft-dir $ROOT/exp021 --out $ROOT/runs/tr-dpo-overfit --limit-train 32 --epochs 10 --lr 1e-4 --no-merge
      $PY -c "import json,sys; d=json.load(open('$ROOT/runs/tr-dpo-overfit/results.json'))['learning_check']; print(d['passed'], d['values'][-3:]); sys.exit(0 if d['passed'] is True else 1)" >> $ROOT/train-status.txt 2>&1 \
        && log "LEARNING CHECK PASSED" || { log "LEARNING CHECK FAILED, stopped (diagnose before the real runs)"; exit 1; } ;;
    dpo-on-sft)
      run dpo-on-sft $T --arm sft --sft-dir $ROOT/exp021 --out $ROOT/runs/dpo-on-sft ;;
    dpo-on-base)
      run dpo-on-base $T --arm base --out $ROOT/runs/dpo-on-base ;;
    variant)  # VARIANT_NAME and VARIANT_ARGS from the environment, for example VARIANT_NAME=dpo-on-sft-e3 VARIANT_ARGS="--arm sft --sft-dir $ROOT/exp021 --epochs 3"
      run $VARIANT_NAME $T --out $ROOT/runs/$VARIANT_NAME $VARIANT_ARGS ;;
    package)
      (cd $ROOT && tar czf tr-dpo-train-results.tar.gz --exclude=merged --exclude=trainer runs logs train-status.txt && sha256sum tr-dpo-train-results.tar.gz > tr-dpo-train-results.sha256 && log "PACKAGED $(du -h tr-dpo-train-results.tar.gz | cut -f1)") ;;
    *) log "unknown stage $stage" ;;
  esac
done
log "TRAIN_DONE ($STAGES)"
