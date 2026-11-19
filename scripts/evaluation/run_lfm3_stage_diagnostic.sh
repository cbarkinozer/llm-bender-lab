#!/usr/bin/env bash
# Inference-only controller. Keep its stdout OUTSIDE the packaged artifacts.
set -euo pipefail
cd /workspace/repos/llm-bender-lab
R=experiments/turkish-capability/lfm3-1.7b/stage-diagnostic-v01-local
mkdir -p "$R/logs"
bash scripts/training/setup_lfm3_stage_diagnostic.sh > "$R/logs/setup.log" 2>&1
source /workspace/lfm3-stage-env.sh
P=/workspace/.venvs/lfm3-stage/bin/python
$P scripts/evaluation/run_lfm3_stage_diagnostic.py verify
$P -u scripts/training/download_lfm3_session.py > "$R/logs/download.log" 2>&1
cp /workspace/stage-setup-logs/environment.txt "$R/logs/environment.txt"
nvidia-smi > "$R/logs/nvidia-smi.txt"
$P -u scripts/evaluation/run_lfm3_stage_diagnostic.py prepare > "$R/logs/prepare.log" 2>&1
$P -u scripts/evaluation/run_lfm3_stage_diagnostic.py run
$P -u scripts/evaluation/run_lfm3_stage_diagnostic.py package > /workspace/stage-diagnostic-package.json
echo ALL_DONE
