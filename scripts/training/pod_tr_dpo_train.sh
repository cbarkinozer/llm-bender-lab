#!/usr/bin/env bash
# Local side for the exp-003 training stages on the pod that already ran the sampling and the pref-rl bootstrap. Run from the repo root; the pod address is never stored in Git.
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo_train.sh up PAIRS [STAGES]    upload runner and pairs, start the stages detached
#   ... status                                                                                          status lines and the tail of the newest log
#   ... fetch DIR                                                                                       package adapters and manifests, download, verify the sha256
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/tr-dpo
cmd=${1:-}; shift || true
case $cmd in
  up)
    pairs=${1:?pairs file}; stages=${2:-"overfit dpo-on-sft dpo-on-base"}
    dirty=false; [ -n "$(git status --porcelain -- scripts)" ] && dirty=true
    printf '{"commit": "%s", "dirty": %s}\n' "$(git rev-parse HEAD)" "$dirty" | $S "cat > $R/repo/GIT_STATE.json" || exit 1
    tar czf - --exclude=__pycache__ scripts/training/pref_rl_common.py scripts/training/run_tr_dpo_train.py scripts/training/run_tr_dpo_train_session.sh \
      | $S "cd $R/repo && tar xzf - && sed -i 's/\r\$//' scripts/training/*.sh && echo extracted" || exit 1
    $S "cat > $R/pairs-dpo.jsonl.new && mv -n $R/pairs-dpo.jsonl.new $R/pairs-dpo.jsonl; sha256sum $R/pairs-dpo.jsonl" < "$pairs" || exit 1
    $S "mkdir -p $R/logs $R/runs"
    $S "cd $R/repo && STAGES='$stages' VARIANT_NAME='${VARIANT_NAME:-}' VARIANT_ARGS='${VARIANT_ARGS:-}' nohup bash scripts/training/run_tr_dpo_train_session.sh > $R/logs/train-launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $R/train-status.txt 2>/dev/null; echo ---; f=\$(ls -t $R/logs/tr-dpo-*.log 2>/dev/null | head -1); echo \$f; tail -c 1500 \"\$f\"; echo; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv"
    ;;
  fetch)
    dest=${1:?destination directory}
    mkdir -p "$dest"
    $S "mkdir -p $R/logs $R/runs"
    $S "cd $R/repo && STAGES=package bash scripts/training/run_tr_dpo_train_session.sh" || exit 1
    want=$($S "cut -d' ' -f1 $R/tr-dpo-train-results.sha256") || exit 1
    $S "cat $R/tr-dpo-train-results.tar.gz" > "$dest/tr-dpo-train-results.tar.gz" || exit 1
    got=$(sha256sum "$dest/tr-dpo-train-results.tar.gz" | cut -d' ' -f1)
    [ "$got" = "$want" ] && echo "FETCHED and verified: $want" || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up PAIRS [STAGES] | status | fetch DIR"; exit 2 ;;
esac
