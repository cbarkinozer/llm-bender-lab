"""Hash-checked staged pilot160: untouched base, new GPU gates, training, inference."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_lfm3_sft160 import BASE, DATA, ROOT, RUNTIME, dump, read, sha, environment

EXPERIMENTS=['exp-007-sft160-lr1e4','exp-008-sft160-lr2e4']
ORIGINAL=BASE/'exp-000-baseline'
DEV=BASE/'sft160-dev-v01'
PY='/workspace/.venvs/lfm3-sft/bin/python'
VLLM='/workspace/.venvs/lfm3-vllm/bin/python'
TRAIN=ROOT/'scripts/training/run_lfm3_sft160.py'


def step(name,command,expected):
    receipt=RUNTIME/'stages'/f'{name}.json'
    command=list(map(str,command))
    if receipt.exists():
        r=read(receipt)
        assert r['command']==command and expected.exists(),name
        assert sha(expected)==r['expected_sha256'],'Completed artifact changed: '+name
        return
    log=RUNTIME/'logs'/f'{name}.log';log.parent.mkdir(parents=True,exist_ok=True)
    print('START '+name,flush=True);started=time.time()
    with log.open('wb') as stream:
        result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    assert result.returncode==0,f'{name} failed; inspect {log}; partial outputs are preserved, not overwritten'
    assert expected.exists(),name
    dump(receipt,dict(command=command,expected_sha256=sha(expected),seconds=time.time()-started,status='completed'))
    print('COMPLETED '+name,flush=True)


def inference(label,model,cohort,thinking=False):
    suffix='-thinking' if thinking else ''
    out=RUNTIME/'inference'/label/(cohort+suffix)
    cmd=[VLLM,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        '--experiment-dir',ORIGINAL,'--output-dir',out,'--limit','100',
        '--batch-size','4','--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
        '--protocol-name','sft160-dev-matched-v01'+suffix]
    if model:cmd+=['--merged-model',model]
    if cohort in ['dev20','reasoning4','smoke2']:
        packet=DEV/'questions.jsonl' if cohort=='dev20' else RUNTIME/(cohort+'.jsonl')
        cmd+=['--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
    if thinking:cmd+=['--enable-thinking']
    step(label+'-'+cohort+suffix,cmd,out/'manifest.json')
    r=read(out/'manifest.json')
    assert r['status']=='completed' and r['count']==r['expected_count']
    if cohort=='cetvel100':
        step(label+'-cetvel100-score',[VLLM,ROOT/'scripts/evaluation/score_lfm3_cetvel.py','--results-dir',out],out/'scores.json')


def grammar(label,model):
    out=RUNTIME/'inference'/label/'turblimp'
    cmd=[PY,ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py','--experiment-dir',ORIGINAL,'--output-dir',out]
    if model:cmd+=['--merged-model',model]
    step(label+'-turblimp',cmd,out/'scores.json')


def packet_checks():
    dm=read(DATA/'manifest.json')
    assert all(sha(DATA/name)==digest for name,digest in dm['files'].items())
    configs=[read(BASE/e/'config.yaml') for e in EXPERIMENTS]
    assert configs[0]['model']==configs[1]['model']
    for cfg in configs:
        assert cfg['dataset']['semantic_manifest_sha256']==sha(DATA/'manifest.json')
        assert cfg['dataset']['train_sha256']==sha(DATA/'train.jsonl')
    recipes=[dict(cfg['training']) for cfg in configs]
    assert [r.pop('learning_rate') for r in recipes]==[1e-4,2e-4]
    assert recipes[0]==recipes[1], 'Unexpected second training variable between jobs'
    baseline=read(ORIGINAL/'config-planned.json')['model']
    assert baseline['repo']==configs[0]['model']['parent_repo']
    assert baseline['revision']==configs[0]['model']['parent_revision']
    assert sha(DEV/'questions.jsonl')==read(DEV/'manifest.json')['questions_sha256']
    assert sha(ORIGINAL/'data-local/questions-500.jsonl')=='2ccd068e8f95259083f0f5c30853d414801b9e06e9790bcf936b471467c46b93'
    assert sha(ORIGINAL/'data-local/turblimp-1600.jsonl')=='59b083e817ddafafe15b42bb3a31fc99d2abff3876f41370c44f47d390b918d0'
    train=[json.loads(s) for s in (DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(train)==160
    import re
    norm=lambda s:' '.join(re.findall(r'\w+',s.casefold()))
    texts=[norm(' '.join(m['content'] for m in r['messages'] if m['role']!='system')+' '+(r.get('worked_solution') or '')) for r in train]
    hits=[]
    for line in (ORIGINAL/'data-local/turblimp-1600.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        for key in ['sentence_good','sentence_bad']:
            sentence=norm(r[key])
            if len(sentence)>=20:
                hits.extend([item['id'],r['id']] for item,text in zip(train,texts) if sentence in text)
    assert not hits,hits
    dev=[json.loads(s) for s in (DEV/'questions.jsonl').read_text(encoding='utf-8').splitlines()]
    reasoning=[r for r in dev if r['reasoning_probe']];assert len(reasoning)==4
    RUNTIME.mkdir(parents=True,exist_ok=True)
    (RUNTIME/'reasoning4.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reasoning),encoding='utf-8',newline='\n')
    smoke=[dict(id='sft160-engineering-'+str(i),task='engineering',messages=[dict(role='user',content=s)],evaluation_only=True) for i,s in enumerate(['Yalnızca merhaba yaz.','2 + 3 kaçtır? Yalnızca sonucu yaz.'])]
    (RUNTIME/'smoke2.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in smoke),encoding='utf-8',newline='\n')
    paths=[TRAIN,Path(__file__),ROOT/'scripts/training/merge_lfm3_sft160_checkpoint.py',
        ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py',
        ROOT/'scripts/training/setup_lfm3_sft160.sh',ROOT/'scripts/evaluation/score_lfm3_cetvel.py',
        ROOT/'scripts/evaluation/score_cetvel_generation.py',ORIGINAL/'config-planned.json',
        ORIGINAL/'requirements-gpu.txt',DATA/'manifest.json',DEV/'manifest.json',DEV/'README.md']+[BASE/e/'config.yaml' for e in EXPERIMENTS]
    receipt=dict(files={str(p.relative_to(ROOT)):sha(p) for p in paths},grammar_sentence_hits=hits)
    frozen=RUNTIME/'run-source-manifest.json'
    if frozen.exists():assert read(frozen)==receipt,'Run inputs changed; use new runtime revision'
    else:dump(frozen,receipt)
    return receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--phase',choices=['local-check','preflight','train','evaluate','all'],required=True)
    p.add_argument('--thinking-probe',action='store_true')
    a=p.parse_args();environment();packet_checks()
    if a.phase=='local-check':
        print('Packet hashes, dev separation metadata, grammar exact-sentence scan and source freeze passed. GPU gates pending.');return
    if a.phase in ['preflight','all']:
        step('prepare',[PY,TRAIN,'--mode','prepare'],RUNTIME/'cpt-merge.json')
        # Untouched base, not CPT, is generated before any SFT optimization.
        inference('base',None,'dev20');inference('base',None,'cetvel100');grammar('base',None)
        for mode in ['smoke','tiny-overfit']:
            result=BASE/EXPERIMENTS[0]/'results-local'/mode/'training-manifest.json'
            step(mode,[PY,TRAIN,'--mode',mode],result)
            assert read(result)['status']=='passed'
        inference('smoke',BASE/EXPERIMENTS[0]/'results-local/smoke/merged-model','smoke2')
        generated=[json.loads(s) for s in (RUNTIME/'inference/smoke/smoke2/answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(generated)==2 and all(r['prediction'].strip() and r['finish_reason']!='timeout' for r in generated)
        assert read(RUNTIME/'label-audit.json')['status']=='passed'
        dump(RUNTIME/'gpu-gate.json',dict(baseline_completed=True,labels_audited=True,smoke_passed=True,tiny_overfit_passed=True,
            semantic_review_passed=True,semantic_review_scope='Owner submitted160; lexical/lineage checks and independently authored dev; no formal semantic contamination guarantee',
            semantic_manifest_sha256=sha(DATA/'manifest.json'),tokenized_sha256=sha(RUNTIME/'train-tokenized.jsonl'),
            model_revision=read(BASE/EXPERIMENTS[0]/'config.yaml')['model']['revision'],training_source_sha256=sha(TRAIN),
            config_sha256={e:sha(BASE/e/'config.yaml') for e in EXPERIMENTS},dev_packet_sha256=sha(DEV/'questions.jsonl')))
    if a.phase in ['train','all']:
        assert (RUNTIME/'gpu-gate.json').exists(),'Run --phase preflight first'
        for e in EXPERIMENTS:
            out=BASE/e/'results-local/sft'
            step(e+'-sft',[PY,TRAIN,'--mode','sft','--experiment',e],out/'training-manifest.json')
    if a.phase in ['evaluate','all']:
        for e in EXPERIMENTS:
            for n in [60,100]:
                dest=BASE/e/'results-local'/f'merged-step{n}'
                step(e+f'-merge{n}',[PY,ROOT/'scripts/training/merge_lfm3_sft160_checkpoint.py','--experiment',e,'--step',str(n)],dest/'merge-receipt.json')
                label=e+f'-step{n}'
                inference(label,dest,'dev20');inference(label,dest,'cetvel100');grammar(label,dest)
                if a.thinking_probe:
                    inference(label,dest,'reasoning4');inference(label,dest,'reasoning4',True)
        if a.thinking_probe:
            inference('base',None,'reasoning4');inference('base',None,'reasoning4',True)
        dump(RUNTIME/'completion.json',dict(status='inference-completed-pending-development-grading',
            checkpoints=[e+f'-step{n}' for e in EXPERIMENTS for n in [60,100]],
            baseline='untouched LiquidAI/LFM3-1.7B',selection='Use frozen dev rubric; no winner inferred from loss',
            old20='Diagnostic only, not used by this checkpoint-selection pipeline'))


if __name__=='__main__':main()
