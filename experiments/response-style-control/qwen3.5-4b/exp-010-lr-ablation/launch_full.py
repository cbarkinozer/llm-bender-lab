"""Authenticate W&B via stdin and start a detached fresh-base exp010 run."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import wandb

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/exp010-runs')
key=sys.stdin.read().strip()
assert key,'Missing stdin credential'
os.environ.update(WANDB_API_KEY=key,WANDB_MODE='online',WANDB_PROJECT='llm-bender-lab-response-style-control',
    WANDB_DIR='/workspace/.cache/wandb',WANDB_RUN_GROUP='exp-010-lr-ablation',
    HF_HOME='/workspace/.cache/huggingface',PYTHONUNBUFFERED='1')
api=wandb.Api(); assert api.viewer
entity=api.default_entity
gate_path=ROOT/'gpu-gates.json'
gate=json.loads(gate_path.read_text())
assert gate['training_config_sha256']==hashlib.sha256((HERE/'training-preflight-v1/training-config.json').read_bytes()).hexdigest()
for name in ('actual_batch_masking','smoke_finite_loss','adapter_save_reload','tiny_overfit_loss_decreased'):
    assert gate[name] is True
output=ROOT/'full-v1'
assert not output.exists(),'Refusing existing full output'
gate['wandb_connected']=True
gate['evidence']['wandb_entity']=entity
gate_path.write_text(json.dumps(gate,indent=2)+'\n')
os.environ.update(WANDB_ENTITY=entity,WANDB_RUN_ID=secrets.token_hex(4))
for name in list(os.environ):
    if name.startswith('WANDB_SERVICE'):
        os.environ.pop(name)
with Path('/workspace/exp010-full.log').open('x') as log:
    child=subprocess.Popen([sys.executable,'-u',str(HERE.parent/'exp-009-minimal-edit/train_reviewed.py'),
        '--mode','full','--preflight-dir',str(HERE/'training-preflight-v1'),'--gates',str(gate_path),
        '--output-dir',str(output)],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env=os.environ.copy())
info=dict(pid=child.pid,entity=entity,project=os.environ['WANDB_PROJECT'],run_id=os.environ['WANDB_RUN_ID'],
    url=f"https://wandb.ai/{entity}/{os.environ['WANDB_PROJECT']}/runs/{os.environ['WANDB_RUN_ID']}")
(ROOT/'wandb-run.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info))
