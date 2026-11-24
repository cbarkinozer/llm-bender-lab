#!/usr/bin/env bash
# Local side for the exp-003 sampling job on a Vast RTX 4090 pod. Run from the repo root; the pod address is never stored in Git.
#   LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo_sampling.sh up       upload, set up the vLLM venv if missing, smoke, sample
#   ... status                                                                                  status lines and log tails
#   ... fetch DIR                                                                               download the sample tarball and verify its sha256
# No token goes to the pod: the models and the base tokenizer are public.
set -uo pipefail
: "${LFM3_POD_HOST:?set LFM3_POD_HOST}"; : "${LFM3_POD_PORT:?set LFM3_POD_PORT}"
K=${LFM3_POD_KEY:-$HOME/.ssh/id_ed25519_lfm3_bilingual}
S="ssh -i $K -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=15 -p $LFM3_POD_PORT root@$LFM3_POD_HOST"
R=/workspace/tr-dpo
D=experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality/data
cmd=${1:-}; shift || true
case $cmd in
  up)
    $S "mkdir -p $R/repo" || exit 1
    tar czf - --exclude=__pycache__ \
        scripts/training/sample_tr_dpo_candidates.py scripts/training/run_tr_dpo_sampling_session.sh scripts/training/setup_lfm3_stage_diagnostic.sh \
        scripts/evaluation/generate_lfm3_sft_samples.py scripts/evaluation/verify_lfm3_sft_samples.py \
        scripts/evaluation/lfm3_eval_v2_scoring.py scripts/evaluation/lfm3_sft_constraints.py \
        experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json \
        $D/prompts-tr-dpo.jsonl $D/prompts-skills-dpo.jsonl \
      | $S "cd $R/repo && tar xzf - && sed -i 's/\r\$//' scripts/training/*.sh && echo extracted" || exit 1
    $S "cd $R/repo && nohup bash -c '[ -x /workspace/.venvs/lfm3-stage/bin/python ] || bash scripts/training/setup_lfm3_stage_diagnostic.sh; bash scripts/training/run_tr_dpo_sampling_session.sh' > $R/launch.log 2>&1 < /dev/null & echo started"
    ;;
  status)
    $S "cat $R/status.txt 2>/dev/null; echo ---; tail -n 6 $R/launch.log; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv"
    ;;
  fetch)
    dest=${1:?destination directory}
    mkdir -p "$dest"
    want=$($S "cut -d' ' -f1 $R/tr-dpo-samples.sha256") || exit 1
    $S "cat $R/tr-dpo-samples.tar.gz" > "$dest/tr-dpo-samples.tar.gz" || exit 1
    got=$(sha256sum "$dest/tr-dpo-samples.tar.gz" | cut -d' ' -f1)
    [ "$got" = "$want" ] && echo "FETCHED and verified: $want" || { echo "CHECKSUM MISMATCH ($got vs $want)"; exit 1; }
    ;;
  *) echo "usage: up | status | fetch DIR"; exit 2 ;;
esac
