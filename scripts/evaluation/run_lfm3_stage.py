"""Logged, fail-fast remote stages. Secrets stay outside the artifact tree."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EXP=Path('experiments/turkish-capability/lfm3-1.7b/exp-000-baseline')
PY='/workspace/.venvs/lfm3/bin/python'
VLLM='/workspace/.venvs/lfm3-vllm/bin/python'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=['smoke','base','train-smoke','overfit','train','after'])
    a=p.parse_args()
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',
        PYTHONUNBUFFERED='1',WANDB_PROJECT='lfm3-turkish-post-training')
    if a.stage in ('train-smoke','overfit','train'):
        os.environ['WANDB_API_KEY']=Path('/workspace/.secrets/wandb-key').read_text().strip()
    for k in list(os.environ):
        if k.startswith('WANDB_SERVICE'):
            del os.environ[k]
    root=EXP/'results-local'
    control=root/'control';control.mkdir(parents=True,exist_ok=True)
    record=control/(a.stage+'-commands.jsonl')
    if record.exists():
        raise ValueError('Stage already invoked; preserve attempt and version next stage explicitly')
    def run(cmd,log):
        started=time.time()
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w') as stream:
            proc=subprocess.Popen([str(s) for s in cmd],stdout=stream,stderr=subprocess.STDOUT)
            code=proc.wait()
        with record.open('a') as stream:
            stream.write(json.dumps(dict(command=[str(s) for s in cmd],cwd=str(Path.cwd()),
                start_unix=started,seconds=time.time()-started,exit_code=code,log=str(log)))+'\n')
        if code:
            raise RuntimeError(f'Command failed ({code}), see {log}')
    if a.stage=='smoke':
        run([VLLM,'scripts/evaluation/evaluate_lfm3_vllm.py','--experiment-dir',EXP,
            '--output-dir',root/'engineering-smoke-v01','--limit','5'],root/'engineering-smoke-v01.log')
    elif a.stage in ('base','after'):
        folder=root/('base-v01' if a.stage=='base' else 'cpt-eval-v01')
        adapter=root/'cpt-v01/adapter'
        merged=root/'cpt-v01/merged-model'
        run([VLLM,'scripts/evaluation/evaluate_lfm3_vllm.py','--experiment-dir',EXP,
            '--output-dir',folder/'cetvel']+(['--merged-model',merged] if a.stage=='after' else []),folder/'cetvel.log')
        run([PY,'scripts/evaluation/score_lfm3_cetvel.py','--results-dir',folder/'cetvel'],folder/'scoring.log')
        for task in ('text','turblimp'):
            run([PY,f'scripts/evaluation/evaluate_lfm3_{task}.py','--experiment-dir',EXP,
                '--output-dir',folder/task]+(['--adapter',adapter] if a.stage=='after' else []),folder/(task+'.log'))
    else:
        mode={'train-smoke':('cpt-smoke-v01',['--smoke']),
            'overfit':('cpt-overfit-v01',['--tiny-overfit']),'train':('cpt-v01',[])}[a.stage]
        run([PY,'scripts/training/train_lfm3_cpt.py','--experiment-dir',EXP,
            '--output-dir',root/mode[0]]+mode[1],root/(mode[0]+'.log'))
    print(a.stage+' completed',flush=True)


if __name__=='__main__':
    main()
