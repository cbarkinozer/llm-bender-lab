#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
external_root="${LLM_BENDER_EXTERNAL_ROOT:-${repo_root}/.cache/external}"
cetvel_dir="${external_root}/cetvel"
run_id="${CETVEL_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/mc-bias-spotcheck/${run_id}"
model_revision="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
# Three different choice-counts (2/3/4) to check whether the position bias
# found in belebele_tr (4-choice) is specific to that task or general to the
# harness's log-likelihood MC scoring on this model.
tasks="xcopa_tr,nli_tr,turkish_plu"
limit="${CETVEL_SPOTCHECK_LIMIT:-100}"

mkdir -p "${result_dir}" "${result_dir}/request-cache"
export HF_DATASETS_TRUST_REMOTE_CODE=true

python "${repo_root}/scripts/evaluation/preflight_cetvel.py" \
  "${cetvel_dir}" "${result_dir}/preflight-manifest.json"

nvidia-smi --query-gpu=timestamp,name,driver_version,memory.total,memory.used,utilization.gpu \
  --format=csv -l 5 >"${result_dir}/gpu-samples.csv" &
monitor_pid=$!
cleanup() {
  status=$?
  kill "${monitor_pid}" 2>/dev/null || true
  wait "${monitor_pid}" 2>/dev/null || true
  printf '%s\n' "${status}" >"${result_dir}/exit-code.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/finished-at.txt"
  find "${result_dir}" -type f ! -name sha256sums.txt -print0 | sort -z | xargs -0 sha256sum >"${result_dir}/sha256sums.txt"
}
trap cleanup EXIT

date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/started-at.txt"
printf '%s\n' "${tasks}" >"${result_dir}/task-selectors.txt"
printf '%s\n' "${limit}" >"${result_dir}/items-per-task-limit.txt"

python -m lm_eval \
  --model hf \
  --include_path "${cetvel_dir}/tasks" \
  --model_args "pretrained=Qwen/Qwen3.5-4B,revision=${model_revision},dtype=bfloat16,max_length=4096" \
  --tasks "${tasks}" \
  --device cuda:0 \
  --batch_size 1 \
  --num_fewshot 0 \
  --apply_chat_template \
  --limit "${limit}" \
  --write_out \
  --log_samples \
  --use_cache "${result_dir}/request-cache/requests" \
  --output_path "${result_dir}"

for f in "${result_dir}"/Qwen__Qwen3.5-4B/samples_*.jsonl; do
  echo "=== ${f} ==="
  python "${repo_root}/scripts/evaluation/analyze_mc_bias.py" "${f}"
done | tee "${result_dir}/bias-report.txt"
