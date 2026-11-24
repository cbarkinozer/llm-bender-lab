#!/usr/bin/env bash
# Local side for the exp-004 sampling job on the pod that already has the lfm3-stage venv (see pod_tr_dpo_sampling.sh). Run from the repo root; the pod address is never stored in Git.
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo4_sampling.sh up | status | fetch DIR
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/tr-dpo
D=experiments/preference-rl/lfm3-1.7b/exp-004-dpo-onpolicy-turkish/data
cmd=${1:-}; shift || true
case $cmd in
  up)
    tar czf - --exclude=__pycache__ scripts/training/sample_tr_dpo_candidates.py scripts/training/run_tr_dpo4_sampling_session.sh $D/prompts-tr-dpo4.jsonl \
      | $S "cd $R/repo && tar xzf - && sed -i 's/\r\$//' scripts/training/*.sh && echo extracted" || exit 1
    $S "cd $R/repo && nohup bash scripts/training/run_tr_dpo4_sampling_session.sh > $R/launch4.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $R/status4.txt 2>/dev/null; echo ---; tail -n 5 $R/launch4.log; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv"
    ;;
  fetch)
    dest=${1:?destination directory}
    mkdir -p "$dest"
    want=$($S "cut -d' ' -f1 $R/tr-dpo4-samples.sha256") || exit 1
    $S "cat $R/tr-dpo4-samples.tar.gz" > "$dest/tr-dpo4-samples.tar.gz" || exit 1
    got=$(sha256sum "$dest/tr-dpo4-samples.tar.gz" | cut -d' ' -f1)
    [ "$got" = "$want" ] && echo "FETCHED and verified: $want" || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up | status | fetch DIR"; exit 2 ;;
esac
