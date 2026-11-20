#!/usr/bin/env bash
set -euo pipefail
cd /workspace/reflex-decision

combined_adapter=${1:?Pass the validation-selected combined adapter path}
test_dir=data/prepared/followup-official-test-s3407
phone_test=data/prepared/phone-routing-human-reviewed-v2-1080-fixedval-20261013/test.jsonl

.venv/bin/python tools/prepare_followup_test_sets.py \
  --general-train data/prepared/general-routing-v1-balanced/train.jsonl \
  --phone-train data/prepared/phone-routing-human-reviewed-v2-1080-fixedval-20261013/train.jsonl \
  --output-dir "$test_dir" > heldout-test-preparation.log 2>&1

run_eval() {
  local name=$1 model=$2
  .venv/bin/python tools/evaluate_decision_followups.py \
    --model "$model" \
    --phone-test "$phone_test" \
    --general-test-dir "$test_dir" \
    --output-dir "runs/eval-${name}-s3407" \
    --max-seq-length 4096 \
    --batch-size 8 > "eval-${name}-s3407.log" 2>&1
}

run_eval base unsloth/Qwen3.5-0.8B
run_eval phone runs/phone-reviewed-scratch-full-s3407/adapter
run_eval general runs/general-balanced-scratch-full-s3407/adapter
run_eval combined "$combined_adapter"
