#!/usr/bin/env bash
set -euo pipefail

# Fallback runner: no vLLM server needed, single process, generation + scoring
# both happen inside the CETVEL venv. See docs/environment-setup-gotchas.md
# ("vLLM nightly requiring newer CUDA driver than the pod has") for why.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cetvel_venv_dir="${CETVEL_VENV:-/workspace/.venvs/cetvel}"
seed="${CETVEL_GEN_SEED:-3407}"
run_id="${CETVEL_GEN_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
result_dir="${repo_root}/experiments/turkish-capability/qwen3.5-4b/exp-000-baseline/results/cetvel-generation-suite/${run_id}"
mkdir -p "${result_dir}"

# Frozen per-task item ranges and output caps (Codex-reviewed, locked in) --
# identical to run_cetvel_generation_suite_vllm.sh.
task_specs=(
  "gecturk:0:200:128"
  "tquad:0:150:128"
  "xquad_tr:0:150:128"
  "wmt_en_tr:0:100:256"
  "mlsum_tr:0:100:768"
)

exec > >(tee "${result_dir}/run.log") 2>&1
source "${cetvel_venv_dir}/bin/activate"
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
export PYTHONHASHSEED="${seed}"

nvidia-smi -q >"${result_dir}/nvidia-smi-start.txt"
python -m pip freeze >"${result_dir}/pip-freeze.txt"
nvidia-smi --query-gpu=timestamp,name,uuid,driver_version,pstate,temperature.gpu,power.draw,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.sm,clocks.mem --format=csv -l 1 >"${result_dir}/gpu-samples.csv" &
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

for spec in "${task_specs[@]}"; do
  IFS=':' read -r task start limit max_tokens <<< "${spec}"
  python "${repo_root}/scripts/evaluation/evaluate_cetvel_generation_transformers.py" \
    --task "${task}" --output-dir "${result_dir}/${task}" \
    --start-index "${start}" --limit "${limit}" --max-new-tokens "${max_tokens}" \
    --seed "${seed}"
done

for spec in "${task_specs[@]}"; do
  IFS=':' read -r task start limit max_tokens <<< "${spec}"
  python "${repo_root}/scripts/evaluation/score_cetvel_generation.py" \
    --task "${task}" --samples "${result_dir}/${task}/samples.jsonl" \
    --output "${result_dir}/${task}/score.json"
done
