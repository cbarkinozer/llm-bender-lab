#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mode="${BELEBELE_MODE:-thinking}"
limit="${BELEBELE_LIMIT:-10}"
max_new_tokens="${BELEBELE_MAX_NEW_TOKENS:-512}"
seed="${BELEBELE_SEED:-3407}"
run_id="${BELEBELE_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/belebele-generation/${mode}/${run_id}"

mkdir -p "${result_dir}"
exec > >(tee "${result_dir}/run.log") 2>&1
export PYTHONHASHSEED="${seed}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8

nvidia-smi -q >"${result_dir}/nvidia-smi-start.txt"
python -m pip freeze >"${result_dir}/pip-freeze.txt"
df -h >"${result_dir}/disk-start.txt"
free -h >"${result_dir}/memory-start.txt"
ps -eo pid,ppid,pcpu,pmem,rss,vsz,etime,cmd >"${result_dir}/processes-start.txt"
nvidia-smi --query-gpu=timestamp,name,uuid,driver_version,pstate,temperature.gpu,power.draw,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.sm,clocks.mem --format=csv -l 1 >"${result_dir}/gpu-samples.csv" &
monitor_pid=$!
cleanup() {
  status=$?
  kill "${monitor_pid}" 2>/dev/null || true
  wait "${monitor_pid}" 2>/dev/null || true
  printf '%s\n' "${status}" >"${result_dir}/exit-code.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/finished-at.txt"
  df -h >"${result_dir}/disk-finish.txt"
  free -h >"${result_dir}/memory-finish.txt"
  find "${result_dir}" -maxdepth 2 -type f ! -name sha256sums.txt -print0 | sort -z | xargs -0 sha256sum >"${result_dir}/sha256sums.txt"
}
trap cleanup EXIT

date -u +%Y-%m-%dT%H:%M:%SZ >"${result_dir}/started-at.txt"
printf '%q ' python "${repo_root}/scripts/evaluation/evaluate_belebele_generation.py" --output-dir "${result_dir}/evaluation" --mode "${mode}" --limit "${limit}" --max-new-tokens "${max_new_tokens}" --seed "${seed}" >"${result_dir}/command.txt"
printf '\n' >>"${result_dir}/command.txt"
python "${repo_root}/scripts/evaluation/evaluate_belebele_generation.py" --output-dir "${result_dir}/evaluation" --mode "${mode}" --limit "${limit}" --max-new-tokens "${max_new_tokens}" --seed "${seed}"
