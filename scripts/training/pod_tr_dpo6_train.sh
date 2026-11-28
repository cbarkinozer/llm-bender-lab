#!/usr/bin/env bash
# Local side for the exp-006 training runs (pod that already has the pref-rl and lfm3-stage venvs). Run from the repo root; the pod address is never stored in Git.
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo6_train.sh up PAIRS EVAL_PROMPTS [STAGES]
#   ... status
#   ... fetch DIR      results of the runs (manifests, adapters, evaluation samples), checksum verified
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/tr-dpo6
cmd=${1:-}; shift || true
case $cmd in
  up)
    pairs=${1:?pairs file (trainer format)}; evalp=${2:?evaluation prompts file}; stages=${3:-"overfit sweep"}
    $S "mkdir -p $R/repo $R/logs $R/runs $R/eval" || exit 1
    dirty=false; [ -n "$(git status --porcelain -- scripts)" ] && dirty=true
    printf '{"commit": "%s", "dirty": %s}\n' "$(git rev-parse HEAD)" "$dirty" | $S "cat > $R/repo/GIT_STATE.json" || exit 1
    tar czf - --exclude=__pycache__ scripts/training/pref_rl_common.py scripts/training/run_tr_dpo_train.py scripts/training/run_tr_dpo6_train_session.sh \
        scripts/training/sample_tr_dpo_candidates.py \
      | $S "cd $R/repo && tar xzf - --no-same-owner && sed -i 's/\r\$//' scripts/training/*.sh && echo extracted" || exit 1
    $S "cat > $R/pairs-trainer.jsonl.new && mv -n $R/pairs-trainer.jsonl.new $R/pairs-trainer.jsonl; sha256sum $R/pairs-trainer.jsonl" < "$pairs" || exit 1
    $S "cat > $R/prompts-eval.jsonl" < "$evalp" && $S "sha256sum $R/prompts-eval.jsonl" || exit 1
    $S "cd $R/repo && STAGES='$stages' nohup bash scripts/training/run_tr_dpo6_train_session.sh > $R/logs/train-launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $R/train-status.txt 2>/dev/null | tail -n 12; echo ---; f=\$(ls -t $R/logs/*.log 2>/dev/null | head -1); echo \$f; tail -c 700 \"\$f\" | tr '\r' '\n' | tail -n 4; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"
    ;;
  fetch)
    dest=${1:?destination directory}
    mkdir -p "$dest"
    $S "cd $R/repo && STAGES=package bash scripts/training/run_tr_dpo6_train_session.sh" || exit 1
    want=$($S "cut -d' ' -f1 $R/tr-dpo6-train-results.sha256") || exit 1
    $S "cat $R/tr-dpo6-train-results.tar.gz" > "$dest/tr-dpo6-train-results.tar.gz" || exit 1
    got=$(sha256sum "$dest/tr-dpo6-train-results.tar.gz" | cut -d' ' -f1)
    [ "$got" = "$want" ] && echo "FETCHED and verified: $want" || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up PAIRS EVAL_PROMPTS [STAGES] | status | fetch DIR"; exit 2 ;;
esac
