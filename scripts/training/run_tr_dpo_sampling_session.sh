#!/usr/bin/env bash
# Pod side: sample the model answers for the Turkish DPO data (preference-rl exp-003). Idempotent; status in $ROOT/status.txt.
# Needs the lfm3-stage venv (scripts/training/setup_lfm3_stage_diagnostic.sh) and /workspace/lfm3-stage-env.sh.
# Lanes: (1) Turkish writing prompts, 4 answers each from exp-021 and from the original model; (2) skill prompts with automatic checkers,
# 4 answers each from exp-021, verified here (code is executed: disposable pod only).
set -euo pipefail
source /workspace/lfm3-stage-env.sh
PY=/workspace/.venvs/lfm3-stage/bin/python
ROOT=/workspace/tr-dpo
DATA=experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality/data
PROMPTS=$DATA/prompts-tr-dpo.jsonl
SKILLS=$DATA/prompts-skills-dpo.jsonl
EXP021_COMMIT=6e4f0b7658b115a28da971f82ff4009f63bed612
export PYTHONPATH=scripts/evaluation
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ROOT/status.txt"; }
mkdir -p "$ROOT"

# 1. Turkish writing lane
if [ ! -f "$ROOT/smoke/answers.jsonl" ]; then
  log "smoke: 8 prompts"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$PROMPTS" --output-dir "$ROOT/smoke" --limit 8 > "$ROOT/smoke.log" 2>&1
  "$PY" - <<PYEOF
import json
rows = [json.loads(l) for l in open('$ROOT/smoke/answers.jsonl', encoding='utf-8')]
assert len(rows) == 32, len(rows)
ended = sum(r['finish_reason'] == 'eos' for r in rows)
print('smoke answers', len(rows), 'ended with eos', ended)
assert ended >= 16, 'most answers should end normally'
assert all(r['raw_output'].strip() for r in rows)
PYEOF
fi
if [ ! -f "$ROOT/full/answers.jsonl" ]; then
  log "full: all Turkish prompts, exp-021"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$PROMPTS" --output-dir "$ROOT/full" > "$ROOT/full.log" 2>&1
fi
if [ ! -f "$ROOT/full-base/answers.jsonl" ]; then
  log "full-base: original LFM3-1.7B on the same prompts"
  "$PY" scripts/training/sample_tr_dpo_candidates.py --prompts "$PROMPTS" --output-dir "$ROOT/full-base" \
    --model LiquidAI/LFM3-1.7B --model-revision 0dc4268b561499c648c7ba7c9466bf3d8d01517a > "$ROOT/full-base.log" 2>&1
fi

# 2. skill-preserving lane
if [ ! -f "$ROOT/exp021/model.safetensors" ]; then
  log "downloading exp-021 weights"
  "$PY" - <<PYEOF
from huggingface_hub import snapshot_download
snapshot_download('cbarkinozer/LFM3-1.7B-Turkish-SFT', revision='$EXP021_COMMIT', local_dir='$ROOT/exp021',
                  allow_patterns=['*.json', '*.py', '*.jinja', 'model.safetensors'])
PYEOF
fi
if [ ! -f "$ROOT/skills-smoke/verified.jsonl" ]; then
  log "skills smoke: 8 prompts, k=2"
  mkdir -p "$ROOT/skills-smoke"
  head -n 8 "$SKILLS" > "$ROOT/skills-smoke/prompts.jsonl"
  "$PY" scripts/evaluation/generate_lfm3_sft_samples.py --prompts "$ROOT/skills-smoke/prompts.jsonl" --model "$ROOT/exp021" \
      --output "$ROOT/skills-smoke/samples.jsonl" --k 2 > "$ROOT/skills-smoke.log" 2>&1
  "$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$ROOT/skills-smoke/prompts.jsonl" --samples "$ROOT/skills-smoke/samples.jsonl" \
      --output "$ROOT/skills-smoke/verified.jsonl" --allow-exec >> "$ROOT/skills-smoke.log" 2>&1
fi
if [ ! -f "$ROOT/skills/verified.jsonl" ]; then
  log "skills: all prompts, k=4"
  mkdir -p "$ROOT/skills"
  "$PY" scripts/evaluation/generate_lfm3_sft_samples.py --prompts "$SKILLS" --model "$ROOT/exp021" --output "$ROOT/skills/samples.jsonl" \
      --k 4 > "$ROOT/skills.log" 2>&1
  "$PY" scripts/evaluation/verify_lfm3_sft_samples.py --prompts "$SKILLS" --samples "$ROOT/skills/samples.jsonl" \
      --output "$ROOT/skills/verified.jsonl" --allow-exec >> "$ROOT/skills.log" 2>&1
fi

(cd "$ROOT" && tar czf tr-dpo-samples.tar.gz full full-base skills skills-smoke smoke status.txt \
   && sha256sum tr-dpo-samples.tar.gz > tr-dpo-samples.sha256)
log "SAMPLING_DONE"
