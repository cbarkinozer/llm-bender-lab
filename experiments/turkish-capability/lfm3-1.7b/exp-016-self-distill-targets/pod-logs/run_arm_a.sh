set -euo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
PY=/workspace/.venvs/lfm3-stage/bin/python
cd /workspace/lfm3-evalv2/repo
R=/workspace/lfm3-evalv2/runs; M=/workspace/lfm3-evalv2/models
$PY scripts/evaluation/merge_lfm3_adapter.py --adapter /workspace/lfm3-evalv2/exp016/sft-arm-a/adapter --output $M/selfdistill-a
cp $M/selfdistill-a/merge-receipt.json $R/merge-receipts/selfdistill-a.json
for mode in off on; do
  $PY scripts/evaluation/run_lfm3_eval_v2.py --name selfdistill-a-think-$mode --thinking $mode --model $M/selfdistill-a --output-dir $R/selfdistill-a-think-$mode
  $PY scripts/evaluation/score_lfm3_eval_v2.py score --run-dir $R/selfdistill-a-think-$mode > $R/logs/score-selfdistill-a-$mode.log
done
echo ARM_A_DONE
