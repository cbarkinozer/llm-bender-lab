#!/usr/bin/env bash
# Local side for the preference-rl experiments on a fresh Vast RTX 4090 pod. Run from the repo root; the pod address is never stored in Git.
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_preference_rl.sh up [STAGES]
#   ... status                      print the pod's bootstrap and campaign status lines and the tail of the newest log
#   ... run "grpo"                  start more stages later (STAGES as in run_preference_rl_campaign.sh)
#   ... fetch DIR                   package the runs on the pod, download them resumably and verify the sha256 into DIR
# `up` uploads the scripts (a few hundred KB), then starts bootstrap and campaign detached on the pod. No token goes to the pod:
# the model and both datasets are public.
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/pref-rl
cmd=${1:-}; shift || true
case $cmd in
  up)
    stages=${1:-"baseline dpo-overfit dpo grpo-smoke"}
    $S "mkdir -p $R/repo $R/logs" || exit 1
    # a pod has no .git: record the commit and whether the uploaded scripts differ from it
    dirty=false; [ -n "$(git status --porcelain -- scripts)" ] && dirty=true
    printf '{"commit": "%s", "dirty": %s}
' "$(git rev-parse HEAD)" "$dirty" | $S "cat > $R/repo/GIT_STATE.json" || exit 1
    tar czf - --exclude=__pycache__ scripts/training/pref_rl_common.py scripts/training/run_pref_dpo_grounded_qa.py \
        scripts/training/run_pref_grpo_phone_tools.py scripts/training/pod_bootstrap_preference_rl.sh scripts/training/run_preference_rl_campaign.sh \
        scripts/evaluation/phone_tools_scoring.py scripts/evaluation/check_phone_tools_scoring.py \
      | $S "cd $R/repo && tar xzf - --no-same-owner && sed -i 's/\r\$//' scripts/training/*.sh && echo extracted" || exit 1
    $S "cd $R/repo && STAGES='$stages' nohup bash -c 'bash scripts/training/pod_bootstrap_preference_rl.sh && STAGES=\"$stages\" bash scripts/training/run_preference_rl_campaign.sh' > $R/logs/launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $R/bootstrap-status.txt $R/campaign-status.txt 2>/dev/null; echo ---; f=\$(ls -t $R/logs/*.log 2>/dev/null | head -1); echo \$f; tail -n 8 \"\$f\"; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv"
    ;;
  run)
    $S "cd $R/repo && STAGES='${1:?stages}' nohup bash scripts/training/run_preference_rl_campaign.sh > $R/logs/launch-run.log 2>&1 < /dev/null & echo started"
    ;;
  fetch)
    dest=${1:?destination directory}
    mkdir -p "$dest"
    $S "cd $R/repo && STAGES=package bash scripts/training/run_preference_rl_campaign.sh" || exit 1
    want=$($S "cut -d' ' -f1 $R/pref-rl-results.tar.gz.sha256") || exit 1
    size=$($S "stat -c %s $R/pref-rl-results.tar.gz") || exit 1
    part="$dest/pref-rl-results.tar.gz.part"
    for try in $(seq 1 60); do
      have=$( [ -f "$part" ] && stat -c %s "$part" || echo 0 )
      [ "$have" = "$size" ] && break
      timeout 180 $S "tail -c +$((have+1)) $R/pref-rl-results.tar.gz | head -c 8000000" >> "$part" 2>/dev/null
    done
    got=$(sha256sum "$part" | cut -d' ' -f1)
    [ "$got" = "$want" ] && { mv "$part" "$dest/pref-rl-results.tar.gz"; echo "FETCHED and verified: $want"; } || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up [STAGES] | status | run STAGES | fetch DIR"; exit 2 ;;
esac
