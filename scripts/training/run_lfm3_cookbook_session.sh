#!/usr/bin/env bash
set -euo pipefail
cd /workspace/lfm3-cookbook/repo
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1 PYTHONUNBUFFERED=1
P=/workspace/.venvs/lfm3-cookbook/bin/python
LOG=/workspace/lfm3-cookbook
trap 'echo SESSION_FAILED_AT_LINE_${LINENO} >&2' ERR
for experiment in exp-014-completion-mask exp-015-cookbook-recipe; do
  for mode in smoke tiny-overfit sft; do
    echo "START $experiment $mode $(date -u)"
    "$P" scripts/training/run_lfm3_cookbook.py "$mode" --experiment "$experiment" > "$LOG/$experiment-$mode.log" 2>&1
    echo "PASSED $experiment $mode $(date -u)"
  done
done
echo TRAINING_BOTH_COMPLETE
