#!/usr/bin/env bash
# Pod-side follow-up for exp-018: the 271 IFEval prompts outside the 270-prompt subset, thinking off, base and arm B,
# then a merged comparison on the full 541 prompts (pre-registered resolution of an AMBIGUOUS IFEval cell).
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
RUNS=$ROOT/guard-runs
DATA=$ROOT/guard-data
export PYTHONPATH=$ROOT/vendor
SCRIPT=scripts/evaluation/lfm3_guard_eval.py
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ROOT/guard-status.txt"; }

"$PY" $SCRIPT prepare --data-dir "$DATA" | tee "$RUNS/prepare-rest.log"
for entry in base: selfdistill-b-cpt:$ROOT/models/selfdistill-b-cpt; do
  name=${entry%%:*}; model=${entry#*:}
  if [ -f "$RUNS/$name-rest/summary.json" ]; then log "$name-rest: scored, skipped"; continue; fi
  margs=(); [ -n "$model" ] && margs=(--model "$model")
  log "$name-rest: generating"
  "$PY" $SCRIPT run --name "$name-rest" --output-dir "$RUNS/$name-rest" --data-dir "$DATA" "${margs[@]}" \
    --tasks ifeval --modes off --ifeval-file ifeval-rest.jsonl > "$RUNS/run-$name-rest.log" 2>&1
  "$PY" $SCRIPT score --run-dir "$RUNS/$name-rest" --vendor "$ROOT/vendor" --data-dir "$DATA" --allow-exec \
    --ifeval-file ifeval-rest.jsonl | tee "$RUNS/score-$name-rest.log"
done
"$PY" $SCRIPT compare --base "$RUNS/base" --base "$RUNS/base-rest" --candidate "$RUNS/selfdistill-b-cpt" \
  --candidate "$RUNS/selfdistill-b-cpt-rest" --out-name compare-full-ifeval.json | tee "$RUNS/compare-full-ifeval.log"
(cd "$ROOT" && tar czf guard-results-rest.tar.gz guard-runs/base-rest guard-runs/selfdistill-b-cpt-rest guard-runs/selfdistill-b-cpt/compare-full-ifeval.json \
   guard-runs/compare-full-ifeval.log guard-runs/score-*-rest.log guard-status.txt && sha256sum guard-results-rest.tar.gz > guard-results-rest.sha256)
log "GUARD_REST_DONE"
