"""Run the approved paired recipe sequentially; credentials stay in memory only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/exp011-exp012-runs')
RUNNER=HERE.parent/'exp-009-minimal-edit/train_reviewed.py'
WAIVER='ok make sure vast.ai pod is ready and just start, we already know how it gets ready so smoke test and overfit tests are not required we can just run two finetuning A and B and do inference and prepare an arguilla ui where i can compare actual answer we wrote, A , and B answers. Do not stop make sure this todo list finishes without waiting me in no steps.'

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def execute(argv,log):
    print('Starting',log.name,flush=True)
    with log.open('x') as out:
        subprocess.run([sys.executable,'-u',*map(str,argv)],stdout=out,stderr=subprocess.STDOUT,check=True)

def work():
    import wandb
    api=wandb.Api()
    assert api.viewer
    os.environ['WANDB_ENTITY']=api.default_entity
    # Never share a parent API client's service socket with trainer children.
    for name in list(os.environ):
        if name.startswith('WANDB_SERVICE'):
            os.environ.pop(name)
    write(ROOT/'tracking-auth.json',dict(authenticated=True,entity=api.default_entity,project=os.environ['WANDB_PROJECT']))
    for arm,folder in [('A','exp-011-duration-ablation'),('B','exp-012-coverage-ablation')]:
        run=ROOT/arm
        run.mkdir()
        preflight=HERE.parent/folder/'training-preflight-v1'
        execute([RUNNER,'--mode','representation-check','--preflight-dir',preflight,'--output-dir',run/'representation-v1'],run/'representation.log')
        result=json.loads((run/'representation-v1/result.json').read_text())
        mask=json.loads((run/'representation-v1/mask-check.json').read_text())
        assert result['status']=='passed' and mask['all_rows_verified'] and mask['trainable_parameters']>0
        gate=dict(training_config_sha256=hashlib.sha256((preflight/'training-config.json').read_bytes()).hexdigest(),experiment_id=folder,
            actual_batch_masking=True,smoke_finite_loss=False,adapter_save_reload=False,tiny_overfit_loss_decreased=False,wandb_connected=True,
            policy='explicit-user-approved-paired-run-waiver',waived_checks=['smoke_finite_loss','adapter_save_reload','tiny_overfit_loss_decreased'],
            user_instruction=WAIVER,date='2026-10-03',evidence=dict(representation=str(run/'representation-v1'),trainable_parameters=mask['trainable_parameters']),
            caveat='No new smoke or tiny-overfit pass claimed. Adapter reload is verified later by evaluation, not before SFT.')
        write(run/'gpu-gates.json',gate)
        import secrets
        os.environ.update(WANDB_RUN_GROUP=folder,WANDB_RUN_ID=secrets.token_hex(4))
        write(run/'wandb-run.json',dict(entity=api.default_entity,project=os.environ['WANDB_PROJECT'],run_id=os.environ['WANDB_RUN_ID'],
            url=f"https://wandb.ai/{api.default_entity}/{os.environ['WANDB_PROJECT']}/runs/{os.environ['WANDB_RUN_ID']}"))
        execute([RUNNER,'--mode','full','--preflight-dir',preflight,'--output-dir',run/'sft-v1','--gates',run/'gpu-gates.json'],run/'sft.log')
        completed=json.loads((run/'sft-v1/result.json').read_text())
        state=json.loads((run/'sft-v1/checkpoints/checkpoint-40/trainer_state.json').read_text())
        assert completed['status']=='completed' and state['global_step']==40 and state['epoch']==4
    for arm in ('A','B'):
        run=ROOT/arm
        execute([HERE.parent/'exp-009-minimal-edit/evaluate_adapter.py','--adapter',run/'sft-v1/adapter','--output-dir',run/'validation-v1','--bounded'],run/'validation.log')
        manifest=json.loads((run/'validation-v1/manifest.json').read_text())
        assert manifest['status']=='completed' and manifest['count']==20
        info=json.loads((run/'wandb-run.json').read_text())
        tracking=api.run(f"{info['entity']}/{info['project']}/{info['run_id']}")
        write(run/'wandb-history.json',list(tracking.scan_history()))
        write(run/'wandb-summary.json',dict(state=tracking.state,config=dict(tracking.config),summary=dict(tracking.summary)))
    write(ROOT/'status.json',dict(status='completed',arms=['A','B'],validation_rows_per_arm=20))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--worker',action='store_true')
    a=p.parse_args()
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',WANDB_DIR='/workspace/.cache/wandb',
        WANDB_MODE='online',WANDB_PROJECT='llm-bender-lab-response-style-control',PYTHONUNBUFFERED='1')
    if a.worker:
        try:
            work()
        except Exception:
            write(ROOT/'status.json',dict(status='failed',traceback=traceback.format_exc()))
            raise
    else:
        assert not ROOT.exists(),'Refusing existing paired run'
        key=sys.stdin.read().strip()
        assert key,'Missing stdin W&B credential'
        os.environ['WANDB_API_KEY']=key
        for name in list(os.environ):
            if name.startswith('WANDB_SERVICE'):
                os.environ.pop(name)
        ROOT.mkdir()
        with (ROOT/'pipeline.log').open('x') as log:
            child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker'],stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=os.environ.copy())
        write(ROOT/'status.json',dict(status='running',pid=child.pid))
        print(json.dumps(dict(pid=child.pid,root=str(ROOT))))

if __name__=='__main__':
    main()
