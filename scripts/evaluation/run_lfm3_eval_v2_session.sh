#!/usr/bin/env bash
# Pod-side driver for the eval v2 baselines. Run from the synced repo root.
#   run_lfm3_eval_v2_session.sh merge       # build the three merged models (cpt, exp014, exp015)
#   run_lfm3_eval_v2_session.sh smoke       # 5 pairs per family, base model, thinking off and on
#   run_lfm3_eval_v2_session.sh baselines   # full set, 4 models x 2 thinking modes, seed 3407
# Steps are idempotent: finished runs and merges are skipped, never overwritten.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
RUNS=$ROOT/runs
MODELS=$ROOT/models
EXP=experiments/turkish-capability/lfm3-1.7b
CPT_REV=6f213ec25a944dab2fbdeb6d337deb0e0442e638
CPT_HISTORICAL_SHA=f4562118c3196462d73649198d856450714ae67081cd6af7df851f59dccf5e46
mkdir -p "$RUNS" "$MODELS" "$RUNS/merge-receipts" "$RUNS/logs"

merge() {  # name adapter [extra args]
  local name=$1 adapter=$2; shift 2
  if [ -f "$MODELS/$name/merge-receipt.json" ]; then echo "merge $name: exists, skipped"; return; fi
  "$PY" scripts/evaluation/merge_lfm3_adapter.py --adapter "$adapter" --output "$MODELS/$name" "$@" \
    2>&1 | tee "$RUNS/logs/merge-$name.log"
  cp "$MODELS/$name/merge-receipt.json" "$RUNS/merge-receipts/$name.json"
}

evaluate() {  # run-name model-dir-or-empty thinking [extra runner args]
  local name=$1 model=$2 mode=$3; shift 3
  if [ -f "$RUNS/$name/summary.json" ]; then echo "run $name: scored, skipped"; return; fi
  local model_args=()
  [ -n "$model" ] && model_args=(--model "$model")
  "$PY" scripts/evaluation/run_lfm3_eval_v2.py --name "$name" --thinking "$mode" "${model_args[@]}" \
    --output-dir "$RUNS/$name" "$@" 2>&1 | tee "$RUNS/logs/run-$name.log"
  "$PY" scripts/evaluation/score_lfm3_eval_v2.py score --run-dir "$RUNS/$name" > "$RUNS/logs/score-$name.log"
  echo "scored $name"
}

case "${1:-}" in
  merge)
    merge cpt cbarkinozer/LFM3-1.7B-Turkish-CPT --adapter-revision "$CPT_REV" --expected-sha256 "$CPT_HISTORICAL_SHA"
    merge exp014 "$EXP/exp-014-completion-mask/results-local/sft/adapter"
    merge exp015 "$EXP/exp-015-cookbook-recipe/results-local/sft/adapter"
    ;;
  smoke)
    evaluate smoke-base-off "" off --limit-pairs 5
    evaluate smoke-base-on "" on --limit-pairs 5
    echo "--- smoke tool-call format and symbolic check (stop here and read before running baselines) ---"
    "$PY" - <<'PY'
import json
for name in ('smoke-base-off', 'smoke-base-on'):
    s = json.load(open(f'/workspace/lfm3-evalv2/runs/{name}/summary.json'))
    for seed, body in s['seeds'].items():
        for key, v in body['summary'].items():
            print(name, key, 'acc', v['accuracy'], 'n', v['n'], 'eos', v['eos_rate'], 'hit_max', v['hit_max_rate'],
                  v.get('errors', ''), v.get('thinking_closure_rate', ''))
PY
    ;;
  baselines)
    for mode in off on; do
      evaluate "base-think-$mode" "" "$mode"
      for m in ${BASELINE_MODELS:-cpt exp014 exp015}; do
        evaluate "$m-think-$mode" "$MODELS/$m" "$mode"
      done
    done
    ;;
  *) echo "usage: $0 merge|smoke|baselines"; exit 2 ;;
esac
