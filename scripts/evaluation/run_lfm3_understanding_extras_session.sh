#!/usr/bin/env bash
# Pod-side driver: Belebele (EN/TR) and the Turkish writing probe for base, CPT, arm A, arm B (thinking off).
# Waits for the primary diagnostic runs (arm B, thinking on) to finish, stops the secondary arm A diagnostic runs that would
# follow, smoke-tests both extras on the base model (5 items; aborts on failure), runs them for all four models, then
# resumes the arm A diagnostic runs. Idempotent: finished runs are skipped.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
DIAG=$ROOT/diag-runs
BEL=$ROOT/belebele-runs
WRI=$ROOT/writing-runs
MODELS_DIR=$ROOT/models
LOGS=$ROOT/extras-logs
mkdir -p "$BEL" "$WRI" "$LOGS"
cd "$ROOT/repo"

until [ -f "$DIAG/selfdistill-b-cpt-think-on/summary.json" ]; do sleep 20; done
pkill -f run_lfm3_understanding_diagnostic_session.sh || true
pkill -f run_lfm3_understanding_diagnostic.py || true
sleep 15
for d in "$DIAG"/*; do
  if [ -d "$d" ] && [ "$(basename "$d")" != logs ] && [ ! -f "$d/summary.json" ]; then rm -rf "$d"; fi
done

run_belebele() {  # name outdir [model-args...]
  local name=$1 out=$2; shift 2
  "$PY" scripts/evaluation/lfm3_belebele_eval.py run --name "$name" --output-dir "$out" "$@" 2>&1 | tail -n 40 > "$LOGS/belebele-$name.log"
  "$PY" scripts/evaluation/lfm3_belebele_eval.py score --run-dir "$out" | tee "$LOGS/belebele-score-$name.log"
}
run_writing() {  # name outdir [model-args...]
  local name=$1 out=$2; shift 2
  "$PY" scripts/evaluation/run_lfm3_writing_probe.py --name "$name" --output-dir "$out" "$@" 2>&1 | tail -n 40 > "$LOGS/writing-$name.log"
  test -f "$out/run-manifest.json"
}

rm -rf "$ROOT/belebele-smoke" "$ROOT/writing-smoke"
run_belebele smoke "$ROOT/belebele-smoke" --limit 5
run_writing smoke "$ROOT/writing-smoke"

for m in base cpt selfdistill-a selfdistill-b-cpt; do
  args=(); [ "$m" != base ] && args=(--model "$MODELS_DIR/$m")
  [ -f "$BEL/$m/summary.json" ] || run_belebele "$m" "$BEL/$m" "${args[@]}"
  [ -f "$WRI/$m/run-manifest.json" ] || run_writing "$m" "$WRI/$m" "${args[@]}"
done

RUN_LIST="selfdistill-a:off selfdistill-a:on" bash scripts/evaluation/run_lfm3_understanding_diagnostic_session.sh full
echo EXTRAS_DONE
