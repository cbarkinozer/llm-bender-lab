#!/usr/bin/env bash
# Pod-side driver, SFT core v01 phase E: train one model on the pack, merge, and run the evaluation suite in priority order.
#   run_lfm3_sft_core_model_session.sh NAME [PARENT]   PARENT = a directory name under models/ (for example cpt); empty = base
# Needs $ROOT/sft-core/train.jsonl (the pack) and the baseline runs of earlier experiments (base and arm B) on the pod.
# Idempotent: finished stages are skipped. Progress: $ROOT/sft-core/status-NAME.txt ; results: $ROOT/sft-core/NAME-results.tar.gz
set -uo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
NAME=$1; PARENT=${2:-}
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
OUT=$ROOT/sft-core
MODELS=$ROOT/models
RUNS=$ROOT/runs
DIAG=$ROOT/diag-runs
BEL=$ROOT/belebele-runs
WRI=$ROOT/writing-runs
GUARD=$ROOT/guard-runs
GDATA=$ROOT/guard-data
TURB=$ROOT/turblimp
MODEL=$MODELS/$NAME
STATUS=$OUT/status-$NAME.txt
LOGS=$OUT/logs-$NAME
mkdir -p "$LOGS"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$STATUS"; }
cd "$ROOT/repo"
export PYTHONPATH=$ROOT/vendor
ARM_B=$MODELS/selfdistill-b-cpt

# 1. train + merge
if [ ! -f "$OUT/train-$NAME/training-manifest.json" ]; then
  log "training $NAME (parent: ${PARENT:-base})"
  pargs=(); [ -n "$PARENT" ] && pargs=(--parent "$MODELS/$PARENT")
  "$PY" scripts/training/run_lfm3_sft_core_train.py --data "$OUT/train.jsonl" --out "$OUT/train-$NAME" "${pargs[@]}" \
      > "$LOGS/train.log" 2>&1 || { log "TRAIN_FAILED"; exit 1; }
fi
if [ ! -f "$MODEL/merge-receipt.json" ]; then
  log "merging"
  if [ -n "$PARENT" ]; then
    "$PY" scripts/evaluation/merge_lfm3_adapter_parent.py --parent "$MODELS/$PARENT" --adapter "$OUT/train-$NAME/adapter" \
        --output "$MODEL" > "$LOGS/merge.log" 2>&1 || { log "MERGE_FAILED"; exit 1; }
  else
    "$PY" scripts/evaluation/merge_lfm3_adapter.py --adapter "$OUT/train-$NAME/adapter" --output "$MODEL" \
        > "$LOGS/merge.log" 2>&1 || { log "MERGE_FAILED"; exit 1; }
  fi
fi

# 2. final test (100 GSM8K test items, EN and TR, thinking on, k=4): same sampler and checker as the base run
if [ ! -f "$OUT/verified-$NAME-final.summary.json" ]; then
  log "final test"
  "$PY" scripts/evaluation/generate_lfm3_sft_samples.py --prompts "$OUT/prompts-render-final.jsonl" --model "$MODEL" \
      --output "$OUT/samples-$NAME-final.jsonl" --k 4 >> "$LOGS/final.log" 2>&1
  "$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$OUT/prompts-render-final.jsonl" \
      --samples "$OUT/samples-$NAME-final.jsonl" --output "$OUT/verified-$NAME-final.jsonl" > "$LOGS/final-verify.log" 2>&1
fi

# 3. eval v2 (math EN/TR, symbolic, tool calls), thinking on, with paired comparisons against base and arm B
if [ ! -f "$RUNS/$NAME-think-on/summary.json" ]; then
  log "eval v2 thinking on"
  "$PY" scripts/evaluation/run_lfm3_eval_v2.py --name "$NAME-think-on" --thinking on --model "$MODEL" \
      --output-dir "$RUNS/$NAME-think-on" > "$LOGS/evalv2.log" 2>&1
  "$PY" scripts/evaluation/score_lfm3_eval_v2.py score --run-dir "$RUNS/$NAME-think-on" > "$LOGS/evalv2-score.log" 2>&1
fi
for ref in base-think-on selfdistill-b-cpt-think-on; do
  [ -f "$RUNS/$NAME-think-on/compare-vs-$ref.json" ] || "$PY" scripts/evaluation/score_lfm3_eval_v2.py compare \
      --base "$RUNS/$ref" --candidate "$RUNS/$NAME-think-on" --output "$RUNS/$NAME-think-on/compare-vs-$ref.json" \
      > "$LOGS/evalv2-compare-$ref.log" 2>&1
done

# 4. understanding diagnostic (six conditions, 4 seeds), thinking on
if [ ! -f "$DIAG/$NAME-think-on/summary.json" ]; then
  log "diagnostic thinking on"
  "$PY" scripts/evaluation/run_lfm3_understanding_diagnostic.py --name "$NAME-think-on" --thinking on --model "$MODEL" \
      --output-dir "$DIAG/$NAME-think-on" > "$LOGS/diag.log" 2>&1
  "$PY" scripts/evaluation/score_lfm3_understanding_diagnostic.py score --run-dir "$DIAG/$NAME-think-on" > "$LOGS/diag-score.log" 2>&1
fi

# 5. Belebele (EN/TR), TurBLiMP
if [ ! -f "$BEL/$NAME/summary.json" ]; then
  log "belebele"
  "$PY" scripts/evaluation/lfm3_belebele_eval.py run --name "$NAME" --output-dir "$BEL/$NAME" --model "$MODEL" > "$LOGS/belebele.log" 2>&1
  "$PY" scripts/evaluation/lfm3_belebele_eval.py score --run-dir "$BEL/$NAME" > "$LOGS/belebele-score.log" 2>&1
fi
for ref in base selfdistill-b-cpt; do
  "$PY" scripts/evaluation/lfm3_belebele_eval.py compare --a "$BEL/$ref" --b "$BEL/$NAME" > "$LOGS/belebele-compare-$ref.log" 2>&1
done
if [ ! -d "$TURB/$NAME" ]; then
  log "turblimp"
  "$PY" scripts/evaluation/evaluate_lfm3_turblimp.py --experiment-dir experiments/turkish-capability/lfm3-1.7b/exp-000-baseline \
      --output-dir "$TURB/$NAME" --merged-model "$MODEL" > "$LOGS/turblimp.log" 2>&1
fi

# 6. English guard: IFEval 270 + HumanEval in both modes, then the other 271 IFEval prompts (thinking off), compare with base
if [ ! -f "$GUARD/$NAME/summary.json" ]; then
  log "guard"
  "$PY" scripts/evaluation/lfm3_guard_eval.py run --name "$NAME" --output-dir "$GUARD/$NAME" --data-dir "$GDATA" --model "$MODEL" \
      > "$GUARD/run-$NAME.log" 2>&1
  "$PY" scripts/evaluation/lfm3_guard_eval.py score --run-dir "$GUARD/$NAME" --vendor "$ROOT/vendor" --data-dir "$GDATA" \
      --allow-exec > "$GUARD/score-$NAME.log" 2>&1
fi
if [ ! -f "$GUARD/$NAME-rest/summary.json" ]; then
  "$PY" scripts/evaluation/lfm3_guard_eval.py run --name "$NAME-rest" --output-dir "$GUARD/$NAME-rest" --data-dir "$GDATA" \
      --model "$MODEL" --tasks ifeval --modes off --ifeval-file ifeval-rest.jsonl > "$GUARD/run-$NAME-rest.log" 2>&1
  "$PY" scripts/evaluation/lfm3_guard_eval.py score --run-dir "$GUARD/$NAME-rest" --vendor "$ROOT/vendor" --data-dir "$GDATA" \
      --allow-exec --ifeval-file ifeval-rest.jsonl > "$GUARD/score-$NAME-rest.log" 2>&1
fi
"$PY" scripts/evaluation/lfm3_guard_eval.py compare --base "$GUARD/base" --candidate "$GUARD/$NAME" \
    --out-name compare-vs-base.json > "$LOGS/guard-compare.log" 2>&1
"$PY" scripts/evaluation/lfm3_guard_eval.py compare --base "$GUARD/base" --base "$GUARD/base-rest" --candidate "$GUARD/$NAME" \
    --candidate "$GUARD/$NAME-rest" --out-name compare-full-ifeval.json > "$LOGS/guard-compare-full.log" 2>&1

# 7. Turkish writing probe (40 prompts, thinking off) and pack of the results
if [ ! -f "$WRI/$NAME/run-manifest.json" ]; then
  log "writing probe"
  "$PY" scripts/evaluation/run_lfm3_writing_probe.py --name "$NAME" --output-dir "$WRI/$NAME" --model "$MODEL" > "$LOGS/writing.log" 2>&1
fi
log "packing"
(cd "$ROOT" && tar czf "sft-core/$NAME-results.tar.gz" "sft-core/train-$NAME/training-manifest.json" "sft-core/train-$NAME/audit.json" \
   "sft-core/verified-$NAME-final.jsonl" "sft-core/verified-$NAME-final.summary.json" "models/$NAME/merge-receipt.json" \
   "runs/$NAME-think-on" "diag-runs/$NAME-think-on" "belebele-runs/$NAME" "turblimp/$NAME" "writing-runs/$NAME" \
   "guard-runs/$NAME" "guard-runs/$NAME-rest" "sft-core/logs-$NAME" "sft-core/status-$NAME.txt" 2>/dev/null; \
   sha256sum "sft-core/$NAME-results.tar.gz" > "sft-core/$NAME-results.sha256"; \
   tar czf "sft-core/$NAME-adapter.tar.gz" "sft-core/train-$NAME/adapter" && sha256sum "sft-core/$NAME-adapter.tar.gz" >> "sft-core/$NAME-results.sha256")
log "SFT_CORE_MODEL_DONE $NAME"
