#!/usr/bin/env bash
# Local side: evaluate the exp-003 DPO models on the pod that trained them. Run from the repo root; the pod address is never stored in Git.
#   LFM3_FINAL_PROMPTS=path/to/prompts-render-final.jsonl LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo_eval.sh up [STAGES]
#   ... status
#   ... fetch DIR     the held-out answers and the per-arm result tarballs, sha256 checked
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
EV=/workspace/lfm3-evalv2
TR=/workspace/tr-dpo
L=experiments/turkish-capability/lfm3-1.7b
H=experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality
ARMS=${ARMS:-"dpo-on-sft dpo-on-base"}
cmd=${1:-}; shift || true
case $cmd in
  up)
    stages=${1:-"heldout guard bel final evalv2 diag writing pack"}
    FINAL=${LFM3_FINAL_PROMPTS:?set LFM3_FINAL_PROMPTS to the final-test prompt render (prompts-render-final.jsonl)}
    $S "mkdir -p $EV/repo $EV/sft-core $TR/logs" || exit 1
    echo "uploading scripts and eval data"
    tar czf - --exclude=__pycache__ --exclude=$L/eval-v2/runs-local --exclude=$L/eval-v2/source-cache --exclude=$L/eval-v2/results scripts $L/eval-v2 \
      $L/eval-v2/source-cache/belebele-eng_Latn.jsonl $L/eval-v2/source-cache/belebele-tur_Latn.jsonl \
      $L/exp-000-baseline/config-planned.json $L/exp-000-baseline/data-local/turblimp-1600.jsonl $L/exp-000-baseline/turblimp-manifest-v01.json \
      $L/exp-014-completion-mask/config.json $L/exp-012-base-bilingual/config.yaml $H/data/prompts-tr-dpo.jsonl \
      | $S "cd $EV/repo && tar xzf - && find scripts -name '*.sh' -exec sed -i 's/\r\$//' {} + && echo extracted" || exit 1
    want=$(sha256sum "$FINAL" | cut -d' ' -f1)
    cat "$FINAL" | $S "cat > $EV/sft-core/prompts-render-final.jsonl" || exit 1
    [ "$($S "sha256sum $EV/sft-core/prompts-render-final.jsonl | cut -d' ' -f1")" = "$want" ] || { echo "final prompts upload mismatch"; exit 1; }
    cat "$H/results-local/edit-worksheet.jsonl/holdout-ids.json" | $S "cat > $EV/holdout-ids.json" || exit 1
    $S "cd $EV/repo && STAGES='$stages' ARMS='$ARMS' nohup bash scripts/training/run_tr_dpo_eval_session.sh > $TR/logs/eval-launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $EV/eval-status.txt 2>/dev/null | tail -n 20; echo ---; tail -n 5 $TR/logs/eval-launch.log; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv"
    ;;
  fetch)
    dest=${1:?destination directory}; mkdir -p "$dest"
    for f in $TR/tr-dpo-heldout $(for a in $ARMS; do echo $EV/sft-core/$a-results; done); do
      b=$(basename $f); want=$($S "cut -d' ' -f1 $f.sha256 2>/dev/null | head -1"); [ -n "$want" ] || { echo "no $b"; continue; }
      $S "cat $f.tar.gz" > "$dest/$b.tar.gz" || exit 1
      got=$(sha256sum "$dest/$b.tar.gz" | cut -d' ' -f1)
      [ "$got" = "$want" ] && echo "FETCHED and verified $b" || { echo "CHECKSUM MISMATCH $b"; exit 1; }
    done
    ;;
  *) echo "usage: up [STAGES] | status | fetch DIR"; exit 2 ;;
esac
