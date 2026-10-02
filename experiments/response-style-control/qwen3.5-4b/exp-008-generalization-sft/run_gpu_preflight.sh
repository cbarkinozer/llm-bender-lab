#!/usr/bin/env bash
set -euo pipefail
run_mode="${1:-preflight}"
case "$run_mode" in
  smoke-only|preflight) ;;
  *) printf '%s\n' 'Usage: bash run_gpu_preflight.sh [smoke-only|preflight]' >&2; exit 2 ;;
esac
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-/workspace/.cache/pip}"
export WANDB_DIR="${WANDB_DIR:-/workspace/wandb}"
cd "$(git rev-parse --show-toplevel)"
experiment=experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft
shared=experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft
python "$experiment/validate_final.py"
python "$shared/train.py" --config "$experiment/config.yaml" --mode dry-run
if [ "$run_mode" = smoke-only ]; then
  python "$shared/train.py" --config "$experiment/config.yaml" --mode representation-check --output-dir "$experiment/results/representation-check-v1" --report-to none
  python "$shared/train.py" --config "$experiment/config.yaml" --mode smoke --output-dir "$experiment/results/smoke-v1" --report-to none
  exit 0
fi
python "$shared/evaluate.py" --config "$experiment/config.yaml" --role base --output "$experiment/results/development-base-v1.jsonl"
if [ ! -d "$experiment/results/representation-check-v1" ]; then
  python "$shared/train.py" --config "$experiment/config.yaml" --mode representation-check --output-dir "$experiment/results/representation-check-v1" --report-to none
fi
if [ ! -d "$experiment/results/smoke-v1" ]; then
  python "$shared/train.py" --config "$experiment/config.yaml" --mode smoke --output-dir "$experiment/results/smoke-v1" --report-to none
fi
python "$shared/train.py" --config "$experiment/config.yaml" --mode tiny-overfit --output-dir "$experiment/results/tiny-overfit-v1" --report-to none
