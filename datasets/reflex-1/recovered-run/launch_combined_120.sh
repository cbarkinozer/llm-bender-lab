#!/usr/bin/env bash
set -euo pipefail
cd /workspace/reflex-decision
set -a
source .env
set +a
exec .venv/bin/python tools/train_combined_routing.py \
  --phone-data-dir data/prepared/phone-routing-human-reviewed-v2-1080-fixedval-20261013 \
  --general-data-dir data/prepared/general-routing-v1-balanced \
  --output-dir runs/combined-balanced-scratch-120step-s3407 \
  --max-seq-length 4096 \
  --phone-weight 1.0 \
  --general-weight 1.0 \
  --max-steps 120 \
  --batch-size 2 \
  --grad-accum 16 \
  --lr 2e-4 \
  --lora-r 16 \
  --lora-alpha 16 \
  --seed 3407 \
  --wandb-project reflexmodels \
  --wandb-run-name qwen35-08b-combined-balanced-scratch-120step-s3407
