#!/usr/bin/env bash
# Pod-side driver, SFT core v01 phase B: rendered prompts -> code oracle -> base-model samples -> verify -> pack.
# Prompts: English rows (math, code, tool, en_general) and the native Turkish rows (tr_general, k=8 for best-of-N polish).
# Idempotent and resumable (the sampler skips finished ids). Run from the synced repo root.
# Progress: $ROOT/sft-core/status.txt ; results: $ROOT/sft-core/en-results.tar.gz
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/lfm3-evalv2
OUT=$ROOT/sft-core
mkdir -p "$OUT"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$OUT/status.txt"; }

CORE=experiments/turkish-capability/lfm3-1.7b/sft-core-v01/prompts-en.jsonl
PROMPTS=$OUT/prompts-render-en.jsonl
"$PY" scripts/datasets/lfm3_sft_core.py render --lang en --split train --output "$PROMPTS"
"$PY" scripts/datasets/lfm3_sft_core.py render --lang tr --split train --output "$OUT/prompts-render-trgen.jsonl"
cat "$OUT/prompts-render-trgen.jsonl" >> "$PROMPTS"

if [ ! -f "$OUT/oracle-code-verified.summary.json" ]; then
  log "code oracle"
  "$PY" scripts/evaluation/oracle_lfm3_sft_core_code.py --core "$CORE" --output "$OUT/oracle-code-samples.jsonl"
  "$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$PROMPTS" --samples "$OUT/oracle-code-samples.jsonl" \
        --output "$OUT/oracle-code-verified.jsonl" --allow-exec | tee "$OUT/oracle-code.log"
fi

log "sampling base (k=4; tr_general k=8)"
"$PY" scripts/evaluation/generate_lfm3_sft_samples.py --prompts "$PROMPTS" --output "$OUT/samples-base-en.jsonl" --k 4 \
      --k-for tr_general=8 >> "$OUT/sampling-base-en.log" 2>&1
log "verifying"
"$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$PROMPTS" --samples "$OUT/samples-base-en.jsonl" \
      --output "$OUT/verified-base-en.jsonl" --allow-exec | tee "$OUT/verify-base-en.log"
(cd "$OUT" && tar czf en-results.tar.gz verified-base-en.jsonl verified-base-en.summary.json oracle-code-verified.jsonl \
   oracle-code-verified.summary.json samples-base-en.meta.json status.txt \
   && sha256sum en-results.tar.gz > en-results.sha256 \
   && tar czf en-samples.tar.gz samples-base-en.jsonl prompts-render-en.jsonl && sha256sum en-samples.tar.gz >> en-results.sha256)
log "SFT_CORE_EN_DONE"
