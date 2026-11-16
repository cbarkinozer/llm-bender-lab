"""Sequential, resumable pilot orchestration on the authorized GPU pod."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_lfm3_sft_pilot import BASE, DATA, ROOT, RUNTIME, dump, read, sha, environment

PY = '/workspace/.venvs/lfm3-sft/bin/python'
VLLM = '/workspace/.venvs/lfm3-vllm/bin/python'
ORIGINAL = BASE / 'exp-000-baseline'
EXPERIMENTS = ['exp-005-sft-lr1e4', 'exp-006-sft-lr2e4']


def step(name, command, expected):
    receipt = RUNTIME/'stages'/f'{name}.json'
    if receipt.exists():
        previous = read(receipt)
        assert previous['command'] == list(map(str,command)), 'Stage command changed: '+name
        assert expected.exists(), 'Missing completed-stage artifact: '+name
        return
    print('START '+name, flush=True)
    log = RUNTIME/'logs'/f'{name}.log'; log.parent.mkdir(parents=True,exist_ok=True)
    started = time.time()
    with log.open('wb') as stream:
        result = subprocess.run(list(map(str,command)), cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print('FAILED '+name+': see '+str(log), flush=True)
        raise RuntimeError(f'{name} exited {result.returncode}')
    assert expected.exists(), name
    dump(receipt,dict(status='completed',command=list(map(str,command)),start_unix=started,
                      seconds=time.time()-started,expected=str(expected),expected_sha256=sha(expected)))
    print('COMPLETED '+name, flush=True)


def inference(label, model, cohort, limit):
    out = RUNTIME/'inference'/label/cohort
    command = [VLLM,ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        '--experiment-dir',ORIGINAL,'--output-dir',out,'--merged-model',model,
        '--limit',str(limit),'--batch-size','4','--temperature','0.1','--top-k','50',
        '--repetition-penalty','1.1','--protocol-name','pilot80-matched-general-v01']
    if cohort in ['holdout20','smoke2']:
        packet = RUNTIME/(cohort+'.jsonl')
        command += ['--packet-path',packet,'--packet-sha256',sha(packet),'--all-rows']
    step(label+'-'+cohort,command,out/'manifest.json')
    report = read(out/'manifest.json')
    assert report['status']=='completed' and report['count']==report['expected_count']
    if cohort.startswith('cetvel'):
        step(label+'-'+cohort+'-score', [VLLM,ROOT/'scripts/evaluation/score_lfm3_cetvel.py',
             '--results-dir',out],out/'scores.json')


def grammar(label, model):
    out = RUNTIME/'inference'/label/'turblimp'
    step(label+'-turblimp',[PY,ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py',
        '--experiment-dir',ORIGINAL,'--merged-model',model,'--output-dir',out],out/'scores.json')


def prepare_packets(limit):
    assert sha(ORIGINAL/'data-local/questions-500.jsonl') == '2ccd068e8f95259083f0f5c30853d414801b9e06e9790bcf936b471467c46b93'
    assert sha(ORIGINAL/'data-local/turblimp-1600.jsonl') == '59b083e817ddafafe15b42bb3a31fc99d2abff3876f41370c44f47d390b918d0'
    import re
    semantic = read(DATA/'semantic-review.json')
    assert semantic['status']=='passed' and semantic['semantic_manifest_sha256']==sha(DATA/'manifest.json')
    def norm(text):
        return ' '.join(re.findall(r'\w+',text.casefold()))
    training = [json.loads(s) for s in (DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    full_train = [norm(' '.join(m['content'] for m in r['messages'] if m['role']!='system') +
                       ' '+(r['worked_solution'] or '')) for r in training]
    grammar_rows = [json.loads(s) for s in (ORIGINAL/'data-local/turblimp-1600.jsonl').read_text(encoding='utf-8').splitlines()]
    sentence_hits = []
    for r in grammar_rows:
        for key in ['sentence_good','sentence_bad']:
            sentence = norm(r[key])
            if len(sentence)>=20:
                for item,text in zip(training,full_train):
                    if sentence in text:
                        sentence_hits.append(dict(train_id=item['id'],grammar_id=r['id'],field=key))
    assert not sentence_hits, sentence_hits
    semantic['grammar_exact_sentence_hits'] = sentence_hits
    semantic['grammar_packet_sha256'] = sha(ORIGINAL/'data-local/turblimp-1600.jsonl')
    dump(RUNTIME/'semantic-review.json',semantic)
    rows = [json.loads(s) for s in (DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()]
    packet = [dict(id=r['id'], task='reviewed_holdout',messages=r['messages'][:-1],
                   target=r['messages'][-1]['content'],evaluation_only=True) for r in rows]
    (RUNTIME/'holdout20.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packet),encoding='utf-8')
    smoke = [dict(id='engineering-'+str(i),task='engineering',messages=[dict(role='user',content=text)],evaluation_only=True)
             for i,text in enumerate(['Yalnızca merhaba yaz.','2 + 3 kaçtır? Yalnızca sonucu yaz.'])]
    (RUNTIME/'smoke2.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in smoke),encoding='utf-8')
    # Do not expose any holdout predictions to optimization or checkpoint decisions.
    files = [ROOT/'scripts/training/run_lfm3_sft_pilot.py',Path(__file__),
             ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py',
             DATA/'manifest.json']+[BASE/e/'config.yaml' for e in EXPERIMENTS]
    dump(RUNTIME/'run-source-manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in files},
        evaluation_limit=limit,holdout_packet_sha256=sha(RUNTIME/'holdout20.jsonl'),
        cohort_policy='CETVEL is development evidence; protected20 for final reporting, no tuning',
        implementation='Explicit native labels with Transformers Trainer/PEFT; training recipe identical except LR'))


def summary(limit):
    report = dict(status='completed',cetvel_count=limit,models={})
    outputs = {}
    for name in ['cpt']+EXPERIMENTS:
        held = RUNTIME/'inference'/name/'holdout20'
        rows = [json.loads(s) for s in (held/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        outputs[name]={r['id']:r for r in rows}
        lengths = sorted(r['generated_tokens'] for r in rows)
        report['models'][name] = dict(
            holdout=dict(count=len(rows),termination=dict(collections.Counter(r['finish_reason'] for r in rows)),
                generated_tokens=sum(lengths),median_tokens=(lengths[9]+lengths[10])/2,max_tokens=max(lengths),
                exact_reference_matches=sum(r['prediction'].strip()==r['target'].strip() for r in rows),
                note='Exact match is descriptive only; semantic correctness requires manual grading.'),
            cetvel=read(RUNTIME/'inference'/name/f'cetvel{limit}'/'scores.json'),
            grammar=read(RUNTIME/'inference'/name/'turblimp'/'scores.json'))
    # Deterministic blinded columns for owner review; mapping stored separately.
    names=['exp-006-sft-lr2e4','cpt','exp-005-sft-lr1e4']
    dump(RUNTIME/'blind-column-key.json',dict(zip(['A','B','C'],names)))
    comparisons=[]
    for rid,row in outputs['cpt'].items():
        comparisons.append(dict(id=rid,messages=row['messages'],reference=row['target'],
            answers={col:outputs[name][rid]['prediction'] for col,name in zip(['A','B','C'],names)}))
    dump(RUNTIME/'blind-review.json',comparisons)
    dump(RUNTIME/'summary.json',report)


def main():
    p=argparse.ArgumentParser();p.add_argument('--cetvel-count',type=int,choices=[100,500],required=True)
    a=p.parse_args();environment(); RUNTIME.mkdir(parents=True,exist_ok=True)
    prepare_packets(a.cetvel_count)
    assert read(RUNTIME/'label-audit.json')['status']=='passed'
    assert read(RUNTIME/'cpt-merge.json')['status']=='passed'
    semantic=read(RUNTIME/'semantic-review.json')
    assert semantic['status']=='passed' and semantic['semantic_manifest_sha256']==sha(DATA/'manifest.json')
    # Disposable train-only diagnostics can run while the separate inference
    # environment finishes installation; neither modifies the CPT checkpoint.
    for mode in ['smoke','tiny-overfit']:
        out=BASE/EXPERIMENTS[0]/'results-local'/mode
        step(mode,[PY,ROOT/'scripts/training/run_lfm3_sft_pilot.py','--mode',mode],out/'training-manifest.json')
        assert read(out/'training-manifest.json')['status']=='passed'
    cpt=RUNTIME/'cpt-merged'
    ready = Path(VLLM).parent.parent/'lib/python3.12/site-packages/vllm/__init__.py'
    deadline = time.monotonic()+1800
    if not ready.exists():
        print('Waiting for isolated vLLM environment installation',flush=True)
    while not ready.exists():
        if time.monotonic()>deadline:
            raise RuntimeError('vLLM installation did not finish within 30 minutes')
        time.sleep(5)
    inference('cpt',cpt,'holdout20',20)
    inference('cpt',cpt,f'cetvel{a.cetvel_count}',a.cetvel_count)
    grammar('cpt',cpt)
    inference('smoke',BASE/EXPERIMENTS[0]/'results-local/smoke/merged-model','smoke2',2)
    dump(RUNTIME/'gpu-gate.json',dict(baseline_completed=True,labels_audited=True,smoke_passed=True,
        tiny_overfit_passed=True,semantic_review_passed=True,semantic_manifest_sha256=sha(DATA/'manifest.json'),
        tokenized_sha256=sha(RUNTIME/'train-tokenized.jsonl'),
        model_revision=read(BASE/EXPERIMENTS[0]/'config.yaml')['model']['revision']))
    for name in EXPERIMENTS:
        out=BASE/name/'results-local/sft'
        step(name+'-sft',[PY,ROOT/'scripts/training/run_lfm3_sft_pilot.py','--mode','sft','--experiment',name],out/'training-manifest.json')
    for name in EXPERIMENTS:
        model=BASE/name/'results-local/sft/merged-model'
        inference(name,model,'holdout20',20)
        inference(name,model,f'cetvel{a.cetvel_count}',a.cetvel_count)
        grammar(name,model)
    summary(a.cetvel_count)
    print('PAIR COMPLETED',flush=True)


if __name__=='__main__':
    main()
