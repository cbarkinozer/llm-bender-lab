#!/usr/bin/env bash
# Pod side: sample 8 answers per prompt from exp-021 for the on-policy Turkish DPO pairs (preference-rl exp-004). Idempotent; status in $ROOT/status4.txt.
# Needs the lfm3-stage venv (vLLM) and /workspace/lfm3-stage-env.sh, like the exp-003 sampling.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/tr-dpo
PROMPTS=experiments/preference-rl/lfm3-1.7b/exp-004-dpo-onpolicy-turkish/data/prompts-tr-dpo4.jsonl
TEMPS=${TEMPS:-0.1,0.4,0.7,0.7,0.7,0.7,0.9,0.9}
export PYTHONPATH=scripts/evaluation
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ROOT/status4.txt"; }
if [ ! -f "$ROOT/full4/answers.jsonl" ]; then
  log "smoke4: 16 prompts"
  rm -rf "$ROOT/smoke4"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$PROMPTS" --output-dir "$ROOT/smoke4" --limit 16 --temperatures "$TEMPS" > "$ROOT/smoke4.log" 2>&1
  "$PY" -c "
import json
rows = [json.loads(l) for l in open('$ROOT/smoke4/answers.jsonl', encoding='utf-8')]
n = 16 * len('$TEMPS'.split(','))
assert len(rows) == n, (len(rows), n)
ended = sum(r['finish_reason'] == 'eos' for r in rows)
print('smoke answers', len(rows), 'ended with eos', ended)
assert ended >= n // 2
"
  log "full4: all prompts, 8 samples each, temperatures $TEMPS"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$PROMPTS" --output-dir "$ROOT/full4" --temperatures "$TEMPS" > "$ROOT/full4.log" 2>&1
fi
(cd "$ROOT" && tar czf tr-dpo4-samples.tar.gz full4 smoke4 status4.txt && sha256sum tr-dpo4-samples.tar.gz > tr-dpo4-samples.sha256)
log "SAMPLING4_DONE"
