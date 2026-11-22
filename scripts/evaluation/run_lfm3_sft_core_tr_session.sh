#!/usr/bin/env bash
# Pod-side driver, SFT core v01 phase C: base-model samples on the owner's Turkish prompts (math train) and on the
# 100-item final test in both languages (the base-model baseline for the final test), then verify and pack.
# Inputs (uploaded, rendered locally from the worksheets): $OUT/prompts-render-tr.jsonl, $OUT/prompts-render-final.jsonl.
# Idempotent and resumable. Progress: $OUT/status-tr.txt ; results: $OUT/tr-results.tar.gz
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
OUT=$ROOT/sft-core
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$OUT/status-tr.txt"; }
cd "$ROOT/repo"

cat "$OUT/prompts-render-tr.jsonl" "$OUT/prompts-render-final.jsonl" > "$OUT/prompts-render-phaseC.jsonl"
log "sampling base on $(wc -l < "$OUT/prompts-render-phaseC.jsonl") Turkish/final-test prompts (k=4)"
"$PY" scripts/evaluation/generate_lfm3_sft_samples.py --prompts "$OUT/prompts-render-phaseC.jsonl" \
      --output "$OUT/samples-base-tr.jsonl" --k 4 >> "$OUT/sampling-base-tr.log" 2>&1
log "verifying"
"$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$OUT/prompts-render-phaseC.jsonl" \
      --samples "$OUT/samples-base-tr.jsonl" --output "$OUT/verified-base-tr.jsonl" | tee "$OUT/verify-base-tr.log"
(cd "$OUT" && tar czf tr-results.tar.gz verified-base-tr.jsonl verified-base-tr.summary.json samples-base-tr.meta.json status-tr.txt \
   && sha256sum tr-results.tar.gz > tr-results.sha256 \
   && tar czf tr-samples.tar.gz samples-base-tr.jsonl prompts-render-phaseC.jsonl && sha256sum tr-samples.tar.gz >> tr-results.sha256)
log "SFT_CORE_TR_DONE"
