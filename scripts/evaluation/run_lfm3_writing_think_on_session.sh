#!/usr/bin/env bash
# Pod-side: Turkish writing probe with thinking ON (the owner's assumed mode) for base, exp-016 arm B and exp-019.
# Waits until the exp-020 driver has finished (the GPU is busy until then). Output: $ROOT/writing-runs-think-on/<model>.
set -uo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
OUT=$ROOT/writing-runs-think-on
mkdir -p "$OUT"
cd "$ROOT/repo"
until grep -q "SFT_CORE_MODEL_DONE exp020" "$ROOT/sft-core/status-exp020.txt" 2>/dev/null; do sleep 30; done
for entry in base: selfdistill-b-cpt:$ROOT/models/selfdistill-b-cpt exp019:$ROOT/models/exp019; do
  name=${entry%%:*}; model=${entry#*:}
  [ -f "$OUT/$name/run-manifest.json" ] && continue
  margs=(); [ -n "$model" ] && margs=(--model "$model")
  "$PY" scripts/evaluation/run_lfm3_writing_probe.py --name "$name-think-on" --output-dir "$OUT/$name" --thinking on "${margs[@]}" \
      > "$OUT/run-$name.log" 2>&1
done
(cd "$ROOT" && tar czf writing-think-on.tar.gz writing-runs-think-on/base writing-runs-think-on/selfdistill-b-cpt writing-runs-think-on/exp019 && sha256sum writing-think-on.tar.gz > writing-think-on.sha256)
echo "$(date -u +%FT%TZ) WRITING_THINK_ON_DONE" | tee -a "$OUT/status.txt"
