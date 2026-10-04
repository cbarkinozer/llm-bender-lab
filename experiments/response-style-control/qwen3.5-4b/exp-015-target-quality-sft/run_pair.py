"""E/F fixed-step pipeline. Fresh model processes, genuine gates, no inherited waiver."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/exp015-exp016-runs')
RUNNER=HERE.parent/'exp-009-minimal-edit/train_reviewed.py'
C_ADAPTER=Path('/workspace/comparators/C-adapter')

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def execute(argv,log):
    print('Starting',str(log),flush=True)
    with log.open('x') as out:
        subprocess.run([sys.executable,'-u',*map(str,argv)],stdout=out,stderr=subprocess.STDOUT,check=True)

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def work():
    import wandb
    api=wandb.Api()
    assert api.viewer
    entity=api.default_entity
    os.environ['WANDB_ENTITY']=entity
    for name in list(os.environ):
        if name.startswith('WANDB_SERVICE'):
            os.environ.pop(name)
    write(ROOT/'tracking-auth.json',dict(authenticated=True,entity=entity,project=os.environ['WANDB_PROJECT']))
    execute([HERE/'verify_ready.py'],ROOT/'cpu-readiness.log')
    for arm,adapter in [('base',None),('C',C_ADAPTER)]:
        command=[HERE/'evaluate_models.py','--output-dir',ROOT/(arm+'-evaluation-v1')]
        if adapter:
            assert (adapter/'adapter_model.safetensors').is_file()
            command+=['--adapter',adapter]
        execute(command,ROOT/(arm+'-evaluation.log'))
    for arm,folder in [('E','exp-015-target-quality-sft'),('F','exp-016-diverse-coverage-sft')]:
        run=ROOT/arm; run.mkdir()
        preflight=HERE.parent/folder/'training-preflight-v1'
        for mode in ('representation-check','smoke','tiny-overfit'):
            execute([RUNNER,'--mode',mode,'--preflight-dir',preflight,'--output-dir',run/mode],run/(mode+'.log'))
        mask=read(run/'representation-check/mask-check.json')
        smoke=read(run/'smoke/result.json'); tiny=read(run/'tiny-overfit/result.json')
        assert mask['all_rows_verified'] and mask['trainable_parameters']==21233664
        assert smoke['status']=='completed' and math.isfinite(smoke['metrics']['train_loss'])
        assert tiny['status']=='completed' and tiny['tiny_after']['eval_loss']<tiny['tiny_before']['eval_loss']
        execute([HERE/'evaluate_models.py','--adapter',run/'smoke/adapter','--reload-check',preflight/'train-tokenized.jsonl',
            '--output-dir',run/'smoke-reload'],run/'smoke-reload.log')
        assert read(run/'smoke-reload/result.json')['adapter_save_reload']
        gate=dict(training_config_sha256=hashlib.sha256((preflight/'training-config.json').read_bytes()).hexdigest(),
            experiment_id=folder,actual_batch_masking=True,smoke_finite_loss=True,adapter_save_reload=True,
            tiny_overfit_loss_decreased=True,wandb_connected=True,policy='genuine-checks-passed',
            evidence=dict(representation='representation-check',smoke='smoke',reload='smoke-reload',tiny='tiny-overfit'))
        write(run/'gpu-gates.json',gate)
        os.environ.update(WANDB_RUN_GROUP=folder,WANDB_RUN_ID=secrets.token_hex(4))
        info=dict(entity=entity,project=os.environ['WANDB_PROJECT'],run_id=os.environ['WANDB_RUN_ID'])
        info['url']=f"https://wandb.ai/{entity}/{info['project']}/runs/{info['run_id']}"
        write(run/'wandb-run.json',info)
        execute([RUNNER,'--mode','full','--preflight-dir',preflight,'--output-dir',run/'sft-v1','--gates',run/'gpu-gates.json'],run/'sft.log')
        assert read(run/'sft-v1/result.json')['status']=='completed'
        state=read(run/'sft-v1/checkpoints/checkpoint-40/trainer_state.json')
        assert state['global_step']==40
        execute([HERE/'evaluate_models.py','--adapter',run/'sft-v1/adapter','--output-dir',ROOT/(arm+'-evaluation-v1')],run/'evaluation.log')
        tracking=api.run(f"{entity}/{info['project']}/{info['run_id']}")
        write(run/'wandb-history.json',list(tracking.scan_history()))
        write(run/'wandb-summary.json',dict(state=tracking.state,config=dict(tracking.config),summary=dict(tracking.summary)))
    baseline=[json.loads(s) for s in (ROOT/'base-evaluation-v1/answers.jsonl').read_text().splitlines()]
    for arm in ('C','E','F'):
        manifest=read(ROOT/(arm+'-evaluation-v1')/'manifest.json')
        data=[json.loads(s) for s in (ROOT/(arm+'-evaluation-v1')/'answers.jsonl').read_text().splitlines()]
        assert manifest['status']=='completed' and len(data)==len(baseline)==32
        assert all((a['id'],a['messages'],a['rendered_prompt'],a['prompt_token_ids'])==
                   (b['id'],b['messages'],b['rendered_prompt'],b['prompt_token_ids']) for a,b in zip(data,baseline))
    write(ROOT/'status.json',dict(status='completed',arms=['base','C','E','F'],rows_per_arm=32,prompt_parity=True))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--worker',action='store_true'); a=p.parse_args()
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',WANDB_DIR='/workspace/.cache/wandb',
        WANDB_MODE='online',WANDB_PROJECT='llm-bender-lab-response-style-control',PYTHONUNBUFFERED='1')
    if a.worker:
        try:
            work()
        except Exception:
            write(ROOT/'status.json',dict(status='failed',traceback=traceback.format_exc())); raise
    else:
        assert not ROOT.exists(),'Refusing overwrite'
        key=sys.stdin.read().strip(); assert key,'Missing stdin W&B key'
        os.environ['WANDB_API_KEY']=key
        for name in list(os.environ):
            if name.startswith('WANDB_SERVICE'):
                os.environ.pop(name)
        ROOT.mkdir()
        with (ROOT/'pipeline.log').open('x') as log:
            child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker'],stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=os.environ.copy(),cwd='/workspace')
        write(ROOT/'status.json',dict(status='running',pid=child.pid)); print(json.dumps(dict(pid=child.pid,root=str(ROOT))))

if __name__=='__main__':
    main()
