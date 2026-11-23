#!/usr/bin/env bash
# Local side: bring a fresh Vast RTX 4090 pod to a running SFT core campaign (exp-021, exp-019 seed 2, exp-022).
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_sft_core_campaign.sh
# Uploads scripts and eval data (about 35 MB), the three packs and the final-test prompts (checksum-verified, retried), then starts
# the pod-side bootstrap (environment, guard data, CPT parent) and the autostart watcher (verifies uploads, audits the pack, launches
# scripts/evaluation/run_lfm3_sft_core_campaign.sh). The pod address is never stored in Git. Run it from the repo root.
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/lfm3-evalv2
L=experiments/turkish-capability/lfm3-1.7b
C=$L/sft-core-v01
FINAL=${LFM3_FINAL_PROMPTS:?set LFM3_FINAL_PROMPTS to the final-test prompt render (prompts-render-final.jsonl)}
$S "mkdir -p $R/repo $R/sft-core/packs" || exit 1
echo "uploading scripts and eval data"
tar czf - --exclude=__pycache__ --exclude=$L/eval-v2/runs-local --exclude=$L/eval-v2/source-cache --exclude=$L/eval-v2/results scripts $L/eval-v2 \
  $L/eval-v2/source-cache/belebele-eng_Latn.jsonl $L/eval-v2/source-cache/belebele-tur_Latn.jsonl \
  $L/exp-000-baseline/config-planned.json $L/exp-000-baseline/data-local/turblimp-1600.jsonl $L/exp-000-baseline/turblimp-manifest-v01.json \
  $L/exp-014-completion-mask/config.json $L/exp-012-base-bilingual/config.yaml \
  | $S "cd $R/repo && tar xzf - && find scripts -name '*.sh' -exec sed -i 's/\r\$//' {} + && echo extracted" || exit 1
declare -A SRC=([pack-exp019]=$C/pack-local/lfm3-base-v1/train.jsonl [pack-exp021]=$C/pack-local/lfm3-exp021/train.jsonl [pack-exp022]=$C/pack-local/lfm3-exp022/train.jsonl)
upload() {  # local remote
  local want; want=$(sha256sum "$1" | cut -d' ' -f1)
  for try in 1 2 3 4 5 6; do
    cat "$1" | $S "cat > $2.part && mv $2.part $2"
    [ "$($S "sha256sum $2 | cut -d' ' -f1" 2>/dev/null)" = "$want" ] && { echo "uploaded $(basename $2)"; return 0; }
    echo "upload of $(basename $2) failed (try $try)"
  done
  return 1
}
for name in "${!SRC[@]}"; do upload "${SRC[$name]}" "$R/sft-core/packs/$name.jsonl" || exit 1; done
upload "$FINAL" "$R/sft-core/prompts-render-final.jsonl" || exit 1
H19=$(sha256sum "${SRC[pack-exp019]}" | cut -d' ' -f1); H21=$(sha256sum "${SRC[pack-exp021]}" | cut -d' ' -f1); H22=$(sha256sum "${SRC[pack-exp022]}" | cut -d' ' -f1)
$S "cat > $R/bootstrap.sh && chmod +x $R/bootstrap.sh" < scripts/training/pod_bootstrap_sft_core.sh
$S "cat > $R/autostart.sh" <<AUTOSTART
#!/usr/bin/env bash
set -uo pipefail
R=$R
log() { echo "\$(date -u +%FT%TZ) \$*" | tee -a \$R/autostart-status.txt; }
until grep -q -E "BOOTSTRAP_DONE|_FAILED" \$R/bootstrap-status.txt 2>/dev/null; do sleep 20; done
grep -q "_FAILED" \$R/bootstrap-status.txt && { log "AUTOSTART_ABORT bootstrap failed"; exit 1; }
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
cd \$R/repo
[ "\$(sha256sum \$R/sft-core/packs/pack-exp019.jsonl | cut -d' ' -f1)" = "$H19" ] && [ "\$(sha256sum \$R/sft-core/packs/pack-exp021.jsonl | cut -d' ' -f1)" = "$H21" ] \
  && [ "\$(sha256sum \$R/sft-core/packs/pack-exp022.jsonl | cut -d' ' -f1)" = "$H22" ] || { log "AUTOSTART_ABORT pack checksum mismatch"; exit 1; }
rm -rf \$R/sft-core/audit-exp021
/workspace/.venvs/lfm3-stage/bin/python scripts/training/run_lfm3_sft_core_train.py --data \$R/sft-core/packs/pack-exp021.jsonl --out \$R/sft-core/audit-exp021 \
  --parent \$R/models/cpt --audit-only > \$R/audit-exp021.log 2>&1 || { log "AUTOSTART_ABORT pack audit failed"; exit 1; }
log "pack audit passed"
setsid nohup bash scripts/evaluation/run_lfm3_sft_core_campaign.sh > \$R/campaign.log 2>&1 < /dev/null &
log "CAMPAIGN_LAUNCHED"
AUTOSTART
rm_old="rm -f $R/bootstrap-status.txt $R/autostart-status.txt"
$S "$rm_old; (setsid nohup bash $R/bootstrap.sh > $R/bootstrap.log 2>&1 < /dev/null &); (setsid nohup bash $R/autostart.sh > $R/autostart.log 2>&1 < /dev/null &); sleep 2; echo started"
