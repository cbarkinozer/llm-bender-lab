#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
external_root="${LLM_BENDER_EXTERNAL_ROOT:-${repo_root}/.cache/external}"
cetvel_dir="${external_root}/cetvel"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/smoke"
manifest_path="${result_dir}/preflight-manifest.json"

cetvel_revision="6119c517e06cce23aaeac103ce3504c9380655e3"
harness_revision="6e49b1f6910931882a4b3b105794c6faf96b74e5"
model_revision="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
task="${CETVEL_SMOKE_TASK:-belebele_tr}"

# CETVEL's legacy TQuAD dataset is implemented as a pinned loading script.
# Datasets 2.x otherwise prompts interactively and breaks unattended runs.
export HF_DATASETS_TRUST_REMOTE_CODE=true

mkdir -p "${external_root}" "${result_dir}"

if [[ ! -d "${cetvel_dir}/.git" ]]; then
  git clone https://github.com/KUIS-AI/cetvel.git "${cetvel_dir}"
fi

git -C "${cetvel_dir}" fetch origin "${cetvel_revision}"
git -C "${cetvel_dir}" checkout --detach "${cetvel_revision}"
git -C "${cetvel_dir}" submodule update --init

actual_harness_revision="$(git -C "${cetvel_dir}/lm-evaluation-harness" rev-parse HEAD)"
if [[ "${actual_harness_revision}" != "${harness_revision}" ]]; then
  echo "Pinned harness revision mismatch: ${actual_harness_revision}" >&2
  exit 1
fi

if ! grep -q "enable_thinking=False" "${cetvel_dir}/lm-evaluation-harness/lm_eval/models/huggingface.py"; then
  echo "Required Qwen3.5 non-thinking harness patch is not applied." >&2
  exit 1
fi

python "${repo_root}/scripts/evaluation/preflight_cetvel.py" \
  "${cetvel_dir}" "${manifest_path}"

python -m lm_eval \
  --model hf \
  --include_path "${cetvel_dir}/tasks" \
  --model_args "pretrained=Qwen/Qwen3.5-4B,revision=${model_revision},dtype=bfloat16,max_length=4096" \
  --tasks "${task}" \
  --device cuda:0 \
  --batch_size 1 \
  --num_fewshot 0 \
  --apply_chat_template \
  --limit 1 \
  --write_out \
  --log_samples \
  --output_path "${result_dir}"
