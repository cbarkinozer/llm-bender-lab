#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
experiment=experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft
shared=experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft
python "$experiment/validate_final.py"
python "$shared/train.py" --config "$experiment/config.yaml" --mode dry-run
python "$shared/evaluate.py" --config "$experiment/config.yaml" --role base --output "$experiment/results/development-base-v1.jsonl"
python "$shared/train.py" --config "$experiment/config.yaml" --mode representation-check --output-dir "$experiment/results/representation-check-v1" --report-to none
python "$shared/train.py" --config "$experiment/config.yaml" --mode smoke --output-dir "$experiment/results/smoke-v1" --report-to none
python "$shared/train.py" --config "$experiment/config.yaml" --mode tiny-overfit --output-dir "$experiment/results/tiny-overfit-v1" --report-to none
