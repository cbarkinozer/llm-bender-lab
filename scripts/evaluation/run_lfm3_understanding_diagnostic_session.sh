#!/usr/bin/env bash
# Pod-side driver for the understanding diagnostic. Run from the synced repo root.
#   run_lfm3_understanding_diagnostic_session.sh smoke   # 6 pairs, 2 seeds, base, thinking off
#   run_lfm3_understanding_diagnostic_session.sh full    # RUN_LIST (model:mode), 4 seeds, six conditions
# Idempotent: scored runs are skipped, never overwritten. RUN_LIST default: base, arm B, arm A.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
RUNS=$ROOT/diag-runs
MODELS_DIR=$ROOT/models
mkdir -p "$RUNS/logs"

diagnose() {  # run-name model-dir-or-empty thinking [extra runner args]
  local name=$1 model=$2 mode=$3; shift 3
  if [ -f "$RUNS/$name/summary.json" ]; then echo "run $name: scored, skipped"; return; fi
  local model_args=()
  [ -n "$model" ] && model_args=(--model "$model")
  "$PY" scripts/evaluation/run_lfm3_understanding_diagnostic.py --name "$name" --thinking "$mode" \
    "${model_args[@]}" --output-dir "$RUNS/$name" "$@" 2>&1 | tee "$RUNS/logs/run-$name.log"
  "$PY" scripts/evaluation/score_lfm3_understanding_diagnostic.py score --run-dir "$RUNS/$name" \
    | tee "$RUNS/logs/score-$name.log"
}

case "${1:-}" in
  smoke) diagnose smoke-base-off "" off --limit-pairs 6 --seeds 3407,3408 ;;
  full)
    # Primary comparisons first; arm A (secondary) last. Override with RUN_LIST="model:mode ...".
    for entry in ${RUN_LIST:-base:off selfdistill-b-cpt:off base:on selfdistill-b-cpt:on selfdistill-a:off selfdistill-a:on}; do
      m=${entry%%:*}; mode=${entry##*:}
      if [ "$m" = base ]; then dir=""; else dir="$MODELS_DIR/$m"; fi
      diagnose "$m-think-$mode" "$dir" "$mode"
    done
    ;;
  *) echo "usage: $0 smoke|full"; exit 2 ;;
esac
