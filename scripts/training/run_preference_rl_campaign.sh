#!/usr/bin/env bash
# Pod side: run stages of the preference-rl experiments one after the other. Every stage writes to its own new directory under
# $R/runs (a run directory is never overwritten) and logs to $R/logs. Choose stages with STAGES (default: baseline dpo-overfit dpo grpo-smoke).
#   baseline    exp-000: DPO and GRPO test sets scored on the untouched model, no training
#   dpo-overfit playbook tiny-overfit check: 32 pairs, 10 epochs, LR 1e-4; the manifest's learning_check must pass (reward accuracy >= .9)
#   dpo         exp-001: DPO on grounded QA (eval, train, eval)
#   grpo-overfit tiny RL overfit: the same 4 requests for 12 steps, LR 5e-5; the mean reward must rise (learning_check)
#   grpo-smoke  exp-002 pipeline check: 5 GRPO steps on the real model (speed and memory, no evaluation)
#   grpo        exp-002: the full GRPO run (150 steps, eval, train, eval); start it only after reading the smoke test's speed
#   package     tar + sha256 of runs/ for download
set -uo pipefail
R=${PREFRL_ROOT:-/workspace/pref-rl}
PY=/workspace/.venvs/pref-rl/bin/python
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1 PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
STAGES=${STAGES:-"baseline dpo-overfit dpo grpo-smoke"}
cd $R/repo || exit 1
mkdir -p $R/runs $R/logs
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $R/campaign-status.txt; }
run() {  # name, command...
  local name=$1; shift
  if [ -e $R/runs/$name ]; then log "SKIP $name (already exists)"; return 0; fi
  log "START $name"
  "$@" > $R/logs/$name.log 2>&1 && log "DONE $name" || { log "FAILED $name (see logs/$name.log), campaign stopped"; exit 1; }
}
require_learning() {  # run name: the tiny-overfit check recorded in its manifest must have passed, otherwise stop before the real run
  $PY -c "import json,sys; d=json.load(open('$R/runs/$1/results.json'))['learning_check']; print(d); sys.exit(0 if d['passed'] is True else 1)" >> $R/campaign-status.txt 2>&1     && log "LEARNING CHECK PASSED $1" || { log "LEARNING CHECK FAILED $1, campaign stopped (diagnose before any full run)"; exit 1; }
}
for stage in $STAGES; do
  case $stage in
    baseline)
      run exp-000-dpo-grounded-qa $PY scripts/training/run_pref_dpo_grounded_qa.py --out $R/runs/exp-000-dpo-grounded-qa --eval-only
      run exp-000-grpo-phone-tools $PY scripts/training/run_pref_grpo_phone_tools.py --out $R/runs/exp-000-grpo-phone-tools --eval-only ;;
    dpo-overfit)
      run exp-001-dpo-overfit $PY scripts/training/run_pref_dpo_grounded_qa.py --out $R/runs/exp-001-dpo-overfit --limit-train 32 --epochs 10 --lr 1e-4 --n 16
      require_learning exp-001-dpo-overfit ;;
    grpo-overfit)
      run exp-002-grpo-overfit $PY scripts/training/run_pref_grpo_phone_tools.py --out $R/runs/exp-002-grpo-overfit --limit-train 4 --max-steps 12 --lr 5e-5 --n 8
      require_learning exp-002-grpo-overfit ;;
    dpo)
      run exp-001-dpo-grounded-qa $PY scripts/training/run_pref_dpo_grounded_qa.py --out $R/runs/exp-001-dpo-grounded-qa ;;
    grpo-smoke)
      run exp-002-grpo-smoke $PY scripts/training/run_pref_grpo_phone_tools.py --out $R/runs/exp-002-grpo-smoke --n 16 --max-steps 5 --limit-train 160 ;;
    grpo)
      run exp-002-grpo-phone-tools $PY scripts/training/run_pref_grpo_phone_tools.py --out $R/runs/exp-002-grpo-phone-tools ;;
    package)
      (cd $R && tar czf pref-rl-results.tar.gz runs logs bootstrap-status.txt campaign-status.txt && sha256sum pref-rl-results.tar.gz > pref-rl-results.tar.gz.sha256 && log "PACKAGED $(du -h pref-rl-results.tar.gz | cut -f1)") ;;
    *) log "unknown stage $stage" ;;
  esac
done
log "CAMPAIGN_DONE ($STAGES)"
