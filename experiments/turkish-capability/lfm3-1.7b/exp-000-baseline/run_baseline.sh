#!/usr/bin/env bash
set -euo pipefail
PY=/workspace/.venvs/lfm3/bin/python
EXP=experiments/turkish-capability/lfm3-1.7b/exp-000-baseline
RUN="$EXP/results-local/$(date -u +%Y%m%dT%H%M%SZ)-base"
mkdir -p "$RUN"
exec > >(tee -a "$RUN/coordinator.log") 2>&1
"$PY" -m pip freeze > "$RUN/pip-freeze.txt"
nvidia-smi > "$RUN/nvidia-smi.txt"
"$PY" scripts/evaluation/evaluate_lfm3_cetvel.py --experiment-dir "$EXP" --output-dir "$RUN/cetvel-smoke" --limit 5 --allow-reviewed-remote-code
"$PY" scripts/evaluation/score_lfm3_cetvel.py --results-dir "$RUN/cetvel-smoke"
# Run the full commands below after inspecting smoke termination, memory and ETA.
printf '\nSmoke complete. Inspect the five outputs before full evaluation. Run folder: %s\n' "$RUN"
printf '%s\n' 'Full benchmark commands are in GPU-RUNBOOK.md.'
