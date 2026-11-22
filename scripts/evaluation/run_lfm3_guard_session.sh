#!/usr/bin/env bash
# Pod-side driver for exp-018 (English guard): base and arm B, both thinking modes, score, compare, pack.
# Idempotent: finished runs are skipped. Run from the synced repo root; progress in $ROOT/guard-status.txt.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
RUNS=$ROOT/guard-runs
DATA=$ROOT/guard-data
VENDOR=$ROOT/vendor
export PYTHONPATH=$VENDOR
SCRIPT=scripts/evaluation/lfm3_guard_eval.py
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ROOT/guard-status.txt"; }

for entry in base: selfdistill-b-cpt:$ROOT/models/selfdistill-b-cpt; do
  name=${entry%%:*}; model=${entry#*:}
  if [ -f "$RUNS/$name/summary.json" ]; then log "$name: scored, skipped"; continue; fi
  margs=(); [ -n "$model" ] && margs=(--model "$model")
  log "$name: generating"
  "$PY" $SCRIPT run --name "$name" --output-dir "$RUNS/$name" --data-dir "$DATA" "${margs[@]}" > "$RUNS/run-$name.log" 2>&1
  log "$name: scoring"
  "$PY" $SCRIPT score --run-dir "$RUNS/$name" --vendor "$VENDOR" --data-dir "$DATA" --allow-exec | tee "$RUNS/score-$name.log"
done
"$PY" $SCRIPT compare --base "$RUNS/base" --candidate "$RUNS/selfdistill-b-cpt" | tee "$RUNS/compare.log"
(cd "$ROOT" && tar czf guard-results.tar.gz guard-runs/base guard-runs/selfdistill-b-cpt guard-runs/compare.log guard-runs/score-*.log guard-data/sources.json guard-status.txt \
   && sha256sum guard-results.tar.gz > guard-results.sha256)
log "GUARD_DONE"
