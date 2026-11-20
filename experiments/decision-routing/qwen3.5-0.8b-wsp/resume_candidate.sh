#!/usr/bin/env bash
set -euo pipefail
cd /workspace/reflex-wsp
exec 9>routing-suite.lock
flock -n 9
export HF_HOME=/workspace/.cache/huggingface
export WANDB_MODE=disabled UNSLOTH_DISABLE_STATISTICS=1 TOKENIZERS_PARALLELISM=false
TRAIN=/workspace/.venvs/reflex-wsp/bin/python
stage() { printf '%s\n' "$1" > routing-stage.txt; }
trap 'stage failed; echo "Candidate continuation failed at line $LINENO" >&2' ERR
$TRAIN - <<'PY'
import json
from pathlib import Path
r=Path('/workspace/reflex-wsp')
assert json.loads((r/'quantized-delta-gate.json').read_text())['passed']
m=json.loads((r/'runs/wsp-smoke/run-manifest.json').read_text())
assert m['run_completed'] and m['smoke'] and m['calibration_ok']
PY
stage tiny_overfit_reload_gate
$TRAIN -u tools/training_gate.py > logs/wsp-training-gate-attempt2.log 2>&1
WSP=$($TRAIN -c 'import json;print(json.load(open("models.json"))["wsp_training"])')
stage candidate_training
$TRAIN -u tools/train_combined_routing.py --phone-data-dir data/reflex-1/phone-routing-human-reviewed-v2-1080-fixedval-20261013 --general-data-dir data/reflex-1/general-routing-v1-balanced --base-model "$WSP" --max-seq-length 4096 --phone-weight 1 --general-weight 1 --max-steps 120 --batch-size 2 --grad-accum 16 --lr 2e-4 --lora-r 16 --lora-alpha 16 --seed 3407 --output-dir runs/wsp-candidate-s3407 > logs/wsp-candidate-training.log 2>&1
stage candidate_routing_evaluation
$TRAIN -u tools/evaluate_routing.py candidate --model runs/wsp-candidate-s3407/adapter > logs/routing-candidate.log 2>&1
$TRAIN tools/write_routing_report.py > logs/routing-report.log
stage completed
