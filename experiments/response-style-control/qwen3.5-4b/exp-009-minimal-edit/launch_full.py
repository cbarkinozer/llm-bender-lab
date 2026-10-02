"""Launch gated full training with W&B credential received only on stdin."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import wandb

HERE=Path(__file__).resolve().parent
key=sys.stdin.read().strip()
if not key:
    raise ValueError('Missing stdin W&B credential')
os.environ.update(WANDB_API_KEY=key,WANDB_MODE='online',
    WANDB_PROJECT='llm-bender-lab-response-style-control',WANDB_DIR='/workspace/.cache/wandb',
    HF_HOME='/workspace/.cache/huggingface',PYTHONUNBUFFERED='1')
api=wandb.Api()
assert api.viewer
os.environ['WANDB_ENTITY']=api.default_entity
os.environ['WANDB_RUN_ID']=secrets.token_hex(4)
os.environ['WANDB_RUN_GROUP']='exp-009-minimal-edit'
output=Path('/workspace/exp009-runs/full-v1')
if output.exists():
    raise ValueError('Full run already exists; refusing overwrite')
gates=Path('/workspace/exp009-runs/gpu-gates.json')
assert gates.exists()
log=Path('/workspace/exp009-full.log')
with log.open('x') as handle:
    process=subprocess.Popen([sys.executable,'-u',str(HERE/'train_reviewed.py'),'--mode','full',
        '--gates',str(gates),'--output-dir',str(output)],stdout=handle,stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,start_new_session=True,env=os.environ.copy())
info=dict(pid=process.pid,entity=api.default_entity,project=os.environ['WANDB_PROJECT'],
    run_id=os.environ['WANDB_RUN_ID'],url=f"https://wandb.ai/{api.default_entity}/{os.environ['WANDB_PROJECT']}/runs/{os.environ['WANDB_RUN_ID']}")
Path('/workspace/exp009-runs/wandb-run.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info))
