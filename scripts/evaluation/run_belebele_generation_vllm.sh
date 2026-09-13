#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
venv_dir="${VLLM_QWEN35_VENV:-/workspace/.venvs/vllm-qwen35}"
port="${VLLM_QWEN35_PORT:-8000}"
max_model_len="${VLLM_QWEN35_MAX_MODEL_LEN:-32768}"
max_num_seqs="${VLLM_QWEN35_MAX_NUM_SEQS:-32}"
max_num_batched_tokens="${VLLM_QWEN35_MAX_NUM_BATCHED_TOKENS:-8192}"
limit="${BELEBELE_LIMIT:-100}"
max_new_tokens_direct="${BELEBELE_MAX_NEW_TOKENS_DIRECT:-512}"
max_new_tokens_thinking="${BELEBELE_MAX_NEW_TOKENS_THINKING:-2048}"
seed="${BELEBELE_SEED:-3407}"
run_id="${BELEBELE_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/belebele-generation-vllm/${run_id}"
mkdir -p "${result_dir}"

exec > >(tee "${result_dir}/run.log") 2>&1
source "${venv_dir}/bin/activate"
export HF_HOME=/workspace/.cache/huggingface
export VLLM_LOGGING_LEVEL=INFO
export PYTHONHASHSEED="${seed}"
# See run_vllm_qwen35_smoke.sh: system nvcc (12.4) can't build flashinfer's JIT
# sampler kernel against this nightly's cu132 torch build.
export VLLM_USE_FLASHINFER_SAMPLER=0

nvidia-smi -q >"${result_dir}/nvidia-smi-start.txt"
python -m pip freeze >"${result_dir}/pip-freeze.txt"
df -h >"${result_dir}/disk-start.txt"
free -h >"${result_dir}/memory-start.txt"
ps -eo pid,ppid,pcpu,pmem,rss,vsz,etime,cmd >"${result_dir}/processes-start.txt"
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
  df -h >"${result_dir}/disk-finish.txt"
  free -h >"${result_dir}/memory-finish.txt"
  find "${result_dir}" -type f ! -name sha256sums.txt -print0 | sort -z | xargs -0 sha256sum >"${result_dir}/sha256sums.txt"
}
trap cleanup EXIT

date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/started-at.txt"

# Observed cold start (model load + torch.compile + CUDA graph capture) took
# ~220s on this GPU; poll for up to 300s before giving up.
for _ in $(seq 1 150); do
  if curl -fsS "http://127.0.0.1:${port}/v1/models" >"${result_dir}/models.json"; then
    break
  fi
  sleep 2
done
test -s "${result_dir}/models.json"

for mode in direct thinking; do
  max_new_tokens="${max_new_tokens_direct}"
  [ "${mode}" = thinking ] && max_new_tokens="${max_new_tokens_thinking}"
  printf '%q ' python "${repo_root}/scripts/evaluation/evaluate_belebele_generation_vllm.py" \
    --output-dir "${result_dir}/${mode}" --mode "${mode}" --limit "${limit}" \
    --max-new-tokens "${max_new_tokens}" --seed "${seed}" --port "${port}" >"${result_dir}/command-${mode}.txt"
  printf '\n' >>"${result_dir}/command-${mode}.txt"
  python "${repo_root}/scripts/evaluation/evaluate_belebele_generation_vllm.py" \
    --output-dir "${result_dir}/${mode}" --mode "${mode}" --limit "${limit}" \
    --max-new-tokens "${max_new_tokens}" --seed "${seed}" --port "${port}"
done

python "${repo_root}/scripts/evaluation/paired_analysis_belebele.py" \
  --direct-samples "${result_dir}/direct/samples.jsonl" \
  --thinking-samples "${result_dir}/thinking/samples.jsonl" \
  --output "${result_dir}/paired-analysis.json"
