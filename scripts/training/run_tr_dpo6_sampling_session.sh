#!/usr/bin/env bash
# Pod side: sample exp-021 on the exp-006 prompts (preference-rl exp-006). Idempotent; status in $ROOT/status6.txt.
#   train + dev prompts: 8 answers each (4 at temperature 0.7, 4 at 1.0) for the code-checked pairs and the dev sweep
#   held-out prompts:    4 answers each at temperature 0.7 from the parent only (the parent's side of the final comparison)
# Needs the lfm3-stage venv (vLLM) and /workspace/lfm3-stage-env.sh, like the exp-004 sampling.
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/tr-dpo6
PROMPTS=experiments/preference-rl/lfm3-1.7b/exp-006-dpo-code-checked-turkish/data/prompts-dpo6.jsonl
TEMPS_TRAIN=${TEMPS_TRAIN:-0.7,0.7,0.7,0.7,1.0,1.0,1.0,1.0}
TEMPS_HELDOUT=${TEMPS_HELDOUT:-0.7,0.7,0.7,0.7}
export PYTHONPATH=scripts/evaluation
mkdir -p "$ROOT"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ROOT/status6.txt"; }
"$PY" - "$PROMPTS" "$ROOT" <<'PYEOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
for name, keep in (('prompts-train-dev', {'train', 'dev'}), ('prompts-heldout', {'heldout'})):
    sel = [r for r in rows if r['split'] in keep]
    open(f'{sys.argv[2]}/{name}.jsonl', 'w', encoding='utf-8', newline='\n').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in sel))
    print(name, len(sel))
PYEOF
if [ ! -f "$ROOT/train-dev/answers.jsonl" ]; then
  log "smoke6: 16 prompts"
  rm -rf "$ROOT/smoke6"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$ROOT/prompts-train-dev.jsonl" --output-dir "$ROOT/smoke6" --limit 16 --temperatures "$TEMPS_TRAIN" > "$ROOT/smoke6.log" 2>&1
  "$PY" -c "
import json
rows = [json.loads(l) for l in open('$ROOT/smoke6/answers.jsonl', encoding='utf-8')]
n = 16 * len('$TEMPS_TRAIN'.split(','))
assert len(rows) == n, (len(rows), n)
ended = sum(r['finish_reason'] == 'eos' for r in rows)
print('smoke answers', len(rows), 'ended with eos', ended)
assert ended >= n // 2
"
  log "train-dev: 5,300 prompts, 8 samples each, temperatures $TEMPS_TRAIN"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$ROOT/prompts-train-dev.jsonl" --output-dir "$ROOT/train-dev" --temperatures "$TEMPS_TRAIN" > "$ROOT/train-dev.log" 2>&1
fi
if [ ! -f "$ROOT/heldout-parent/answers.jsonl" ]; then
  log "heldout-parent: 700 prompts, 4 samples each, temperatures $TEMPS_HELDOUT"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$ROOT/prompts-heldout.jsonl" --output-dir "$ROOT/heldout-parent" --temperatures "$TEMPS_HELDOUT" > "$ROOT/heldout-parent.log" 2>&1
fi
(cd "$ROOT" && tar czf tr-dpo6-samples.tar.gz train-dev heldout-parent prompts-train-dev.jsonl prompts-heldout.jsonl status6.txt && sha256sum tr-dpo6-samples.tar.gz > tr-dpo6-samples.sha256)
log "SAMPLING6_DONE"
