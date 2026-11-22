set -uo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
PY=/workspace/.venvs/lfm3-stage/bin/python
cd /workspace/lfm3-evalv2/repo
B=experiments/turkish-capability/lfm3-1.7b/exp-000-baseline
O=/workspace/lfm3-evalv2/turblimp; mkdir -p $O
$PY scripts/evaluation/evaluate_lfm3_turblimp.py --experiment-dir $B --output-dir $O/base
for m in cpt selfdistill-a selfdistill-b-cpt selfdistill-c-x3; do
  $PY scripts/evaluation/evaluate_lfm3_turblimp.py --experiment-dir $B --output-dir $O/$m --merged-model /workspace/lfm3-evalv2/models/$m
done
echo TURBLIMP_DONE
