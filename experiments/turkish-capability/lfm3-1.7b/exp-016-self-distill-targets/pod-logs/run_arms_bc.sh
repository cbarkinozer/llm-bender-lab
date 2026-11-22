set -euo pipefail
source /workspace/lfm3-stage-env.sh
export HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
PY=/workspace/.venvs/lfm3-stage/bin/python
cd /workspace/lfm3-evalv2/repo
R=/workspace/lfm3-evalv2/runs; M=/workspace/lfm3-evalv2/models; X=/workspace/lfm3-evalv2/exp016
$PY scripts/training/run_lfm3_self_distill_sft.py --parent $M/cpt --out $X/sft-arm-b-cpt-parent
$PY scripts/training/run_lfm3_self_distill_sft.py --repeat 3 --out $X/sft-arm-c-base-x3
# arm B adapter sits on the CPT-merged parent; merge by loading that parent
$PY - <<'PY'
import torch,gc
from peft import PeftModel
from transformers import AutoModelForCausalLM,AutoTokenizer
M='/workspace/lfm3-evalv2/models'; X='/workspace/lfm3-evalv2/exp016'
tok=AutoTokenizer.from_pretrained('LiquidAI/LFM3-1.7B',revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a')
m=AutoModelForCausalLM.from_pretrained(M+'/cpt',trust_remote_code=True,dtype=torch.bfloat16).to('cuda')
m=PeftModel.from_pretrained(m,X+'/sft-arm-b-cpt-parent/adapter').merge_and_unload(safe_merge=True).eval()
m.save_pretrained(M+'/selfdistill-b-cpt',safe_serialization=True); tok.save_pretrained(M+'/selfdistill-b-cpt'); print('merged b')
PY
$PY scripts/evaluation/merge_lfm3_adapter.py --adapter $X/sft-arm-c-base-x3/adapter --output $M/selfdistill-c-x3
for arm in selfdistill-b-cpt selfdistill-c-x3; do
 for mode in off on; do
  $PY scripts/evaluation/run_lfm3_eval_v2.py --name $arm-think-$mode --thinking $mode --model $M/$arm --output-dir $R/$arm-think-$mode
  $PY scripts/evaluation/score_lfm3_eval_v2.py score --run-dir $R/$arm-think-$mode > $R/logs/score-$arm-$mode.log
 done
done
echo ARMS_BC_DONE
