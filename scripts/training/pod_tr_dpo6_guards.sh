#!/usr/bin/env bash
# Local side for the exp-006 guard suite (rule 4). Run from the repo root; the pod address is never stored in Git.
#   LFM3_FINAL_PROMPTS=path/to/prompts-render-final.jsonl LFM3_POD_HOST=... LFM3_POD_PORT=... ARMS="dpo-s101 sft-s101" bash scripts/training/pod_tr_dpo6_guards.sh up
#   ... status
#   ... fetch DIR
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
EV=/workspace/lfm3-evalv2
L=experiments/turkish-capability/lfm3-1.7b
ARMS=${ARMS:-"dpo-s101 sft-s101"}
cmd=${1:-}; shift || true
case $cmd in
  up)
    FINAL=${LFM3_FINAL_PROMPTS:?set LFM3_FINAL_PROMPTS to the final-test prompt render (prompts-render-final.jsonl)}
    $S "mkdir -p $EV/repo $EV/sft-core $EV/vendor/instruction_following_eval $EV/repo/$L/eval-v2/source-cache" || exit 1
    tar czf - --exclude=__pycache__ --exclude=$L/eval-v2/runs-local --exclude=$L/eval-v2/source-cache --exclude=$L/eval-v2/results scripts $L/eval-v2 \
      $L/exp-000-baseline/config-planned.json $L/exp-000-baseline/data-local/turblimp-1600.jsonl $L/exp-000-baseline/turblimp-manifest-v01.json \
      $L/exp-014-completion-mask/config.json $L/exp-012-base-bilingual/config.yaml \
      | $S "cd $EV/repo && tar xzf - --no-same-owner && find scripts -name '*.sh' -exec sed -i 's/\r\$//' {} + && echo extracted" || exit 1
    tar czf - -C $L/eval-v2/source-cache belebele-eng_Latn.jsonl belebele-tur_Latn.jsonl | $S "tar xzf - --no-same-owner -C $EV/repo/$L/eval-v2/source-cache" || exit 1
    tar czf - -C $L/eval-v2/source-cache/ifeval-code . | $S "tar xzf - --no-same-owner -C $EV/vendor/instruction_following_eval" || exit 1
    want=$(sha256sum "$FINAL" | cut -d' ' -f1)
    cat "$FINAL" | $S "cat > $EV/sft-core/prompts-render-final.jsonl" || exit 1
    [ "$($S "sha256sum $EV/sft-core/prompts-render-final.jsonl | cut -d' ' -f1")" = "$want" ] || { echo "final prompts upload mismatch"; exit 1; }
    $S "cd $EV/repo && ARMS='$ARMS' nohup bash scripts/training/run_tr_dpo6_guard_session.sh > $EV/guard-launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "tail -n 14 $EV/guard-status.txt 2>/dev/null; echo ---; tail -n 3 $EV/guard-launch.log; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"
    ;;
  fetch)
    dest=${1:?destination directory}; mkdir -p "$dest"
    want=$($S "cut -d' ' -f1 $EV/exp006-guard-results.sha256") || exit 1
    $S "cat $EV/exp006-guard-results.tar.gz" > "$dest/exp006-guard-results.tar.gz" || exit 1
    got=$(sha256sum "$dest/exp006-guard-results.tar.gz" | cut -d' ' -f1)
    [ "$got" = "$want" ] && echo "FETCHED and verified: $want" || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up | status | fetch DIR"; exit 2 ;;
esac
