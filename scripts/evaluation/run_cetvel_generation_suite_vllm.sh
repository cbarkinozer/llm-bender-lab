#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
venv_dir="${VLLM_QWEN35_VENV:-/workspace/.venvs/vllm-qwen35}"
cetvel_venv_dir="${CETVEL_VENV:-/workspace/.venvs/cetvel}"
port="${VLLM_QWEN35_PORT:-8000}"
max_model_len="${VLLM_QWEN35_MAX_MODEL_LEN:-32768}"
max_num_seqs="${VLLM_QWEN35_MAX_NUM_SEQS:-32}"
max_num_batched_tokens="${VLLM_QWEN35_MAX_NUM_BATCHED_TOKENS:-8192}"
seed="${CETVEL_GEN_SEED:-3407}"
run_id="${CETVEL_GEN_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/cetvel-generation-suite/${run_id}"
mkdir -p "${result_dir}"

# Frozen per-task item ranges and output caps (Codex-reviewed, locked in).
# format: task:start:limit:max_tokens
task_specs=(
  "gecturk:0:200:128"
  "tquad:0:150:128"
  "xquad_tr:0:150:128"
  "wmt_en_tr:0:100:256"
  "mlsum_tr:0:100:768"
)

exec > >(tee "${result_dir}/run.log") 2>&1
source "${venv_dir}/bin/activate"
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
export VLLM_LOGGING_LEVEL=INFO
export PYTHONHASHSEED="${seed}"
export VLLM_USE_FLASHINFER_SAMPLER=0

nvidia-smi -q >"${result_dir}/nvidia-smi-start.txt"
python -m pip freeze >"${result_dir}/pip-freeze.txt"
nvidia-smi --query-gpu=timestamp,name,uuid,driver_version,pstate,temperature.gpu,power.draw,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.sm,clocks.mem --format=csv -l 1 >"${result_dir}/gpu-samples.csv" &
monitor_pid=$!

python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3.5-4B \
  --served-model-name Qwen/Qwen3.5-4B \
  --port "${port}" \
  --max-model-len "${max_model_len}" \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs "${max_num_seqs}" \
  --max-num-batched-tokens "${max_num_batched_tokens}" \
  --reasoning-parser qwen3 \
  --language-model-only \
  >"${result_dir}/server.log" 2>&1 &
server_pid=$!
printf '%s\n' "${server_pid}" >"${result_dir}/server.pid"

cleanup() {
  status=$?
  kill "${monitor_pid}" 2>/dev/null || true
  wait "${monitor_pid}" 2>/dev/null || true
  kill "${server_pid}" 2>/dev/null || true
  for _ in $(seq 1 15); do
    kill -0 "${server_pid}" 2>/dev/null || break
    sleep 2
  done
  kill -9 "${server_pid}" 2>/dev/null || true
  wait "${server_pid}" 2>/dev/null || true
  printf '%s\n' "${status}" >"${result_dir}/exit-code.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/finished-at.txt"
  find "${result_dir}" -type f ! -name sha256sums.txt -print0 | sort -z | xargs -0 sha256sum >"${result_dir}/sha256sums.txt"
}
trap cleanup EXIT

date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/started-at.txt"

for _ in $(seq 1 150); do
  if curl -fsS "http://127.0.0.1:${port}/v1/models" >"${result_dir}/models.json"; then
    break
  fi
  sleep 2
done
test -s "${result_dir}/models.json"

for spec in "${task_specs[@]}"; do
  IFS=':' read -r task start limit max_tokens <<< "${spec}"
  python "${repo_root}/scripts/evaluation/evaluate_cetvel_generation_vllm.py" \
    --task "${task}" --output-dir "${result_dir}/${task}" \
    --start-index "${start}" --limit "${limit}" --max-new-tokens "${max_tokens}" \
    --seed "${seed}" --port "${port}"
done

# Scoring needs sacrebleu/rouge-score (installed in the CETVEL venv), not
# the vLLM venv -- deactivate and switch venvs for this part, no GPU needed.
deactivate
source "${cetvel_venv_dir}/bin/activate"
for spec in "${task_specs[@]}"; do
  IFS=':' read -r task start limit max_tokens <<< "${spec}"
  python "${repo_root}/scripts/evaluation/score_cetvel_generation.py" \
    --task "${task}" --samples "${result_dir}/${task}/samples.jsonl" \
    --output "${result_dir}/${task}/score.json"
done
