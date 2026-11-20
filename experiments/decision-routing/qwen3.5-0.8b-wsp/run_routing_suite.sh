#!/usr/bin/env bash
set -euo pipefail
cd /workspace/reflex-wsp
exec 9>routing-suite.lock
flock -n 9
export HF_HOME=/workspace/.cache/huggingface
export WANDB_MODE=disabled UNSLOTH_DISABLE_STATISTICS=1 TOKENIZERS_PARALLELISM=false
TRAIN=/workspace/.venvs/reflex-wsp/bin/python
EVAL=/workspace/.venvs/reflex-eval/bin/python
stage() { printf '%s\n' "$1" > routing-stage.txt; }
trap 'stage failed; echo "Routing suite failed at line $LINENO" >&2' ERR
stage wsp_native_baseline
$TRAIN -u tools/evaluate_routing.py wsp > logs/routing-wsp.log 2>&1
stage released_reference
$TRAIN -u tools/evaluate_routing.py released > logs/routing-released.log 2>&1
stage parent_phone_generative
$EVAL -u tools/evaluate_phone_base.py parent > logs/phone-generative-parent.log 2>&1
stage wsp_phone_generative
$EVAL -u tools/evaluate_phone_base.py wsp > logs/phone-generative-wsp.log 2>&1
stage quantized_delta_gate
$TRAIN - <<'PY'
import json
from pathlib import Path
r=Path('/workspace/reflex-wsp')
p=json.loads((r/'eval/routing/parent/manifest.json').read_text())['quantized_weight_audit']
w=json.loads((r/'eval/routing/wsp/manifest.json').read_text())['quantized_weight_audit']
assert len(p)==len(w)==2 and p.keys()==w.keys()
assert all(p[k]['dequantized_sha256']!=w[k]['dequantized_sha256'] for k in p), 'WSP deltas lost under 4-bit loading'
(r/'quantized-delta-gate.json').write_text(json.dumps({'passed':True,'parent':p,'wsp':w},indent=2)+'\n')
PY
stage candidate_smoke
WSP=$($TRAIN -c 'import json;print(json.load(open("models.json"))["wsp_training"])')
COMMON=(--phone-data-dir data/reflex-1/phone-routing-human-reviewed-v2-1080-fixedval-20261013 --general-data-dir data/reflex-1/general-routing-v1-balanced --base-model "$WSP" --max-seq-length 4096 --phone-weight 1 --general-weight 1 --max-steps 120 --batch-size 2 --grad-accum 16 --lr 2e-4 --lora-r 16 --lora-alpha 16 --seed 3407)
$TRAIN -u tools/train_combined_routing.py "${COMMON[@]}" --smoke --output-dir runs/wsp-smoke > logs/wsp-training-smoke.log 2>&1
stage tiny_overfit_reload_gate
$TRAIN -u tools/training_gate.py > logs/wsp-training-gate.log 2>&1
stage candidate_training
$TRAIN -u tools/train_combined_routing.py "${COMMON[@]}" --output-dir runs/wsp-candidate-s3407 > logs/wsp-candidate-training.log 2>&1
stage candidate_routing_evaluation
$TRAIN -u tools/evaluate_routing.py candidate --model runs/wsp-candidate-s3407/adapter > logs/routing-candidate.log 2>&1
stage completed
