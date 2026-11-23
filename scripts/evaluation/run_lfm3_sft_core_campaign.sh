#!/usr/bin/env bash
# Pod-side campaign driver, stage by stage: all three models go through each stage before the next stage starts, so the models
# can be compared early and a clearly worse one can be dropped (touch $ROOT/skip-<name>; checked before every stage).
#   exp021   exp-019 pack without Atlas + 57 reviewed Atlas rows + 80 correspondence rows (the candidate)
#   exp019s2 the exp-019 pack again with another seed (run-to-run spread)
#   exp022   exp-019 pack without its Atlas rows (ablation: do the flawed Atlas rows help or hurt?)
# Needs $ROOT/sft-core/packs/{pack-exp019,pack-exp021,pack-exp022}.jsonl, models/cpt, and the bootstrap done. Idempotent per stage.
# Progress: $ROOT/campaign-status.txt ("STAGE_DONE <stage> <name>", "CAMPAIGN_DONE <name>"). Results per model: $ROOT/sft-core/<name>-results.tar.gz.
set -uo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
ROOT=/workspace/lfm3-evalv2
OUT=$ROOT/sft-core
PY=/workspace/.venvs/lfm3-stage/bin/python
STATUS=$ROOT/campaign-status.txt
cd "$ROOT/repo"
export PYTHONPATH=$ROOT/vendor
mkdir -p "$ROOT/writing-runs-think-on"
SPECS=("exp021:pack-exp021:3407" "exp019s2:pack-exp019:4242" "exp022:pack-exp022:3407")
echo "$(date -u +%FT%TZ) CAMPAIGN_START stage-major" | tee -a "$STATUS"
for stage in train final evalv2 diag bel guard writing writing_on pack; do
  for spec in "${SPECS[@]}"; do
    IFS=: read -r name pack seed <<< "$spec"
    if [ -f "$ROOT/skip-$name" ]; then echo "$(date -u +%FT%TZ) SKIPPED $stage $name" | tee -a "$STATUS"; continue; fi
    if [ "$stage" = writing_on ]; then
      if [ ! -f "$ROOT/writing-runs-think-on/$name/run-manifest.json" ]; then
        "$PY" scripts/evaluation/run_lfm3_writing_probe.py --name "$name-think-on" --output-dir "$ROOT/writing-runs-think-on/$name" \
            --thinking on --model "$ROOT/models/$name" > "$ROOT/writing-runs-think-on/run-$name.log" 2>&1
      fi
      (cd "$ROOT" && tar czf "writing-think-on-$name.tar.gz" "writing-runs-think-on/$name" && sha256sum "writing-think-on-$name.tar.gz" > "writing-think-on-$name.sha256")
    else
      STAGES="$stage" PACK="$OUT/packs/$pack.jsonl" SEED="$seed" bash scripts/evaluation/run_lfm3_sft_core_model_session.sh "$name" cpt
    fi
    echo "$(date -u +%FT%TZ) STAGE_DONE $stage $name" | tee -a "$STATUS"
  done
done
for spec in "${SPECS[@]}"; do IFS=: read -r name _ _ <<< "$spec"; [ -f "$ROOT/skip-$name" ] || echo "$(date -u +%FT%TZ) CAMPAIGN_DONE $name" | tee -a "$STATUS"; done
echo "$(date -u +%FT%TZ) CAMPAIGN_ALL_DONE" | tee -a "$STATUS"
