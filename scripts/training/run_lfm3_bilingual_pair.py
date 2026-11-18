"""Recoverable training and development-only evaluation; fresh final test stays frozen."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from run_lfm3_bilingual_gpu import BASE,PILOT,ROOT,RUN,EXPERIMENTS,environment,dump,read,sha,load,fingerprints

PY='/workspace/.venvs/lfm3-sft/bin/python'
VLLM='/workspace/.venvs/lfm3-vllm/bin/python'
ORIGINAL=BASE/'exp-000-baseline'
TRAIN=ROOT/'scripts/training/run_lfm3_bilingual_gpu.py'


def stage(name,command,expected):
    command=list(map(str,command))
    receipt=RUN/'stages'/f'{name}.json'
    if receipt.exists():
        old=read(receipt)
        assert old['command']==command and sha(expected)==old['expected_sha256']
        return
    log=RUN/'logs'/f'{name}.log';log.parent.mkdir(parents=True,exist_ok=True)
    assert not log.exists(),'Existing unfinished stage log; inspect before retrying'
    print('START '+name,flush=True);start=time.time()
    with log.open('xb') as f:
        result=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    assert result.returncode==0,f'{name} failed; see {log}'
    assert expected.exists(),str(expected)
    dump(receipt,dict(command=command,status='completed',seconds=time.time()-start,expected_sha256=sha(expected)))
    print('DONE '+name,flush=True)


def check_baseline_and_data():
    assert sha(ORIGINAL/'data-local/questions-500.jsonl')=='2ccd068e8f95259083f0f5c30853d414801b9e06e9790bcf936b471467c46b93'
    assert sha(ORIGINAL/'data-local/turblimp-1600.jsonl')=='59b083e817ddafafe15b42bb3a31fc99d2abff3876f41370c44f47d390b918d0'
    expected_decoding=dict(temperature=.1,top_k=50,top_p=1.,repetition_penalty=1.1,max_new_tokens=4096,
                          context_budget=8192,enable_thinking=False,ignore_eos=True,stop_token_ids=[124900])
    evidence={}
    for cohort,count in [('dev20',20),('cetvel100',100)]:
        path=RUN/'inference/base'/cohort
        manifest=read(path/'manifest.json')
        answers=[json.loads(l) for l in (path/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert manifest['status']=='completed' and manifest['count']==len(answers)==count
        assert manifest['model']['repo']=='LiquidAI/LFM3-1.7B'
        assert manifest['model']['revision']=='0dc4268b561499c648c7ba7c9466bf3d8d01517a'
        assert manifest['merged_model'] is None and manifest['decoding']==expected_decoding
        assert manifest['packages']['vllm']=='0.34.0rc1.dev251+g7cc0a8a2b'
        assert {r['id'] for r in answers}==set(manifest['selected_ids'])
        evidence[cohort]=dict(manifest_sha256=sha(path/'manifest.json'),answers_sha256=sha(path/'answers.jsonl'),
            note='Exact pinned untouched-original baseline reused from pilot160; not regenerated or relabeled as a new run.')
    assert read(RUN/'inference/base/dev20/manifest.json')['questions_sha256']==sha(BASE/'sft160-dev-v01/questions.jsonl')
    assert read(RUN/'inference/base/cetvel100/manifest.json')['questions_sha256']==sha(ORIGINAL/'data-local/questions-500.jsonl')
    assert (RUN/'inference/base/turblimp/scores.json').exists()
    _,rows,_=load(EXPERIMENTS[1])
    norm=lambda s:' '.join(re.findall(r'\w+',s.casefold()))
    texts=[norm(' '.join(m['content'] for m in r['messages'] if m['role']!='system')+' '+(r.get('worked_solution') or '')) for r in rows]
    hits=[]
    for line in (ORIGINAL/'data-local/turblimp-1600.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        for k in ['sentence_good','sentence_bad']:
            text=norm(r[k])
            if len(text)>=20:
                hits.extend([rows[i]['id'],r['id']] for i,t in enumerate(texts) if text in t)
    assert not hits,hits
    dump(RUN/'baseline-and-data-receipt.json',dict(status='passed',baseline=evidence,
        grammar_sentence_hits=hits,all_640_training_rows_checked=True,
        scope='Private research continuation on existing pinned public-source corpus under owner training instructions; license/source-provenance gaps remain documented, not falsely marked cleared.'))


def gate():
    check_baseline_and_data()
    for exp in EXPERIMENTS:
        audit=read(RUN/'native'/exp/'label-audit.json')
        assert audit['status']=='passed' and audit['train_sha256']==load(exp)[0]['dataset']['train_sha256']
    smoke=read(BASE/EXPERIMENTS[1]/'results-local/smoke/training-manifest.json')
    tiny=read(BASE/EXPERIMENTS[0]/'results-local/tiny-overfit/training-manifest.json')
    assert smoke['status']==tiny['status']=='passed'
    assert smoke['fingerprints']==fingerprints(EXPERIMENTS[1])
    assert tiny['fingerprints']==fingerprints(EXPERIMENTS[0])
    assert smoke['adapter_reload_exact'] and len(smoke['smoke_generations'])==2
    assert tiny['final_train_nll']<tiny['initial_train_nll']*.8
    dump(RUN/'gpu-gate.json',dict(baseline_completed=True,native_labels_passed=True,
        smoke_passed=True,tiny_overfit_passed=True,owner_data_decisions_recorded=True,
        source_rights_clearance_claimed=False,
        source_use_scope='Previously used pinned public sources; continuation explicitly requested by owner for this private research pilot. Existing upstream uncertainty remains recorded.',
        experiments={e:fingerprints(e) for e in EXPERIMENTS},
        smoke_manifest_sha256=sha(BASE/EXPERIMENTS[1]/'results-local/smoke/training-manifest.json'),
        tiny_manifest_sha256=sha(BASE/EXPERIMENTS[0]/'results-local/tiny-overfit/training-manifest.json')))


def inference(label,model,cohort):
    out=RUN/'inference'/label/cohort
    command=[VLLM,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        '--experiment-dir',ORIGINAL,'--output-dir',out,'--merged-model',model,
        '--batch-size','4','--temperature','0.1','--top-k','50','--repetition-penalty','1.1',
        '--protocol-name','bilingual-pilot-v01-development-thinking-off']
    if cohort=='dev20':
        packet=BASE/'sft160-dev-v01/questions.jsonl'
        command+=['--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
    elif cohort=='crosslingual15':
        packet=RUN/'crosslingual15.jsonl'
        command+=['--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
    else:
        command+=['--limit','100']
    stage(label+'-'+cohort,command,out/'manifest.json')
    manifest=read(out/'manifest.json')
    assert manifest['status']=='completed' and manifest['count']=={'dev20':20,'crosslingual15':15,'cetvel100':100}[cohort]
    if cohort=='cetvel100':
        assert manifest['selected_ids']==read(RUN/'inference/base/cetvel100/manifest.json')['selected_ids']
        stage(label+'-score',[VLLM,ROOT/'scripts/evaluation/score_lfm3_cetvel.py','--results-dir',out],out/'scores.json')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['train','evaluate','all'],default='all')
    args=parser.parse_args();environment();RUN.mkdir(parents=True,exist_ok=True)
    frozen=BASE/'crosslingual-holdout-v01'
    packet_rows=[]
    for name in ['questions.jsonl','symbolic-controls.jsonl']:
        packet_rows += [json.loads(l) for l in (frozen/name).read_text(encoding='utf-8').splitlines()]
    (RUN/'crosslingual15.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packet_rows),encoding='utf-8')
    assert len(packet_rows)==15
    if args.phase in ['train','all']:
        gate()
        for exp in EXPERIMENTS:
            stage(exp+'-sft',[PY,TRAIN,'--mode','sft','--experiment',exp],BASE/exp/'results-local/sft/training-manifest.json')
        dump(RUN/'training-completion.json',dict(status='completed',experiments=EXPERIMENTS,
            adapters_only_for_local_recovery=True,source_commit='e52fad8 plus recorded GPU runner changes'))
    if args.phase in ['evaluate','all']:
        for exp in EXPERIMENTS:
            cfg,_,_=load(exp)
            for step in cfg['training']['save_steps']:
                model=BASE/exp/'results-local'/f'merged-step{step}'
                label=exp+f'-step{step}'
                stage(label+'-merge',[PY,ROOT/'scripts/training/merge_lfm3_bilingual_checkpoint.py','--experiment',exp,'--step',step],model/'merge-receipt.json')
                for cohort in ['dev20','crosslingual15','cetvel100']:
                    inference(label,model,cohort)
                scores=RUN/'inference'/label/'turblimp'
                stage(label+'-grammar',[PY,ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py',
                    '--experiment-dir',ORIGINAL,'--output-dir',scores,'--merged-model',model],scores/'scores.json')
        dump(RUN/'development-completion.json',dict(status='completed-pending-owner-checkpoint-selection',
            checkpoints=4,dev_prompts_per_checkpoint=35,cetvel_per_checkpoint=100,grammar_pairs_per_checkpoint=1600,
            fresh_final_eval_used=False,note='Keep eval-v01 140+8 sealed until checkpoint selection from development results.'))


if __name__=='__main__':main()
