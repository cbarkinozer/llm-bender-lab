"""Sequential fresh-base GPU gates; never starts full training itself."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'exp-009-minimal-edit'
ROOT=Path('/workspace/exp010-runs')

def run(name,argv):
    with Path('/workspace/exp010-'+name+'.log').open('x') as log:
        subprocess.run([sys.executable,'-u',*map(str,argv)],stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Completed',name,flush=True)

def read(name):
    return json.loads((ROOT/name).read_text())

def main():
    for mode,name in [('representation-check','representation-v1'),('smoke','smoke-v1')]:
        run(name,[PARENT/'train_reviewed.py','--mode',mode,'--preflight-dir',HERE/'training-preflight-v1','--output-dir',ROOT/name])
    run('reload-v1',[PARENT/'reload_smoke_adapter.py','--adapter',ROOT/'smoke-v1/adapter','--output-dir',ROOT/'reload-v1'])
    run('tiny-v1',[PARENT/'train_reviewed.py','--mode','tiny-overfit','--preflight-dir',HERE/'training-preflight-v1','--output-dir',ROOT/'tiny-v1'])
    mask=read('representation-v1/mask-check.json'); smoke=read('smoke-v1/result.json')
    reload=read('reload-v1/reload-manifest.json'); tiny=read('tiny-v1/result.json')
    assert mask['all_rows_verified'] and mask['trainable_parameters']>0
    assert smoke['status']=='completed' and math.isfinite(smoke['metrics']['train_loss'])
    assert reload['status']=='adapter-reloaded' and math.isfinite(reload['finite_forward_loss'])
    before=tiny['tiny_before']['eval_loss']; after=tiny['tiny_after']['eval_loss']
    assert tiny['status']=='completed' and math.isfinite(after) and after<before
    gate=dict(training_config_sha256=hashlib.sha256((HERE/'training-preflight-v1/training-config.json').read_bytes()).hexdigest(),
        actual_batch_masking=True,smoke_finite_loss=True,adapter_save_reload=True,tiny_overfit_loss_decreased=True,
        wandb_connected=False,evidence=dict(smoke_loss=smoke['metrics']['train_loss'],reload_loss=reload['finite_forward_loss'],tiny_before=before,tiny_after=after))
    with (ROOT/'gpu-gates.json').open('x') as f:
        json.dump(gate,f,indent=2)
    print(json.dumps(gate),flush=True)

if __name__=='__main__':
    main()
