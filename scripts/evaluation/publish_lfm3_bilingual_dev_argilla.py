"""Blind original-versus-four-checkpoint development ranking; never expose final-test refs."""
import hashlib
import json
import os
from pathlib import Path
import random
import uuid

import argilla as rg
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'bilingual-runtime-local'
OUT=RUN/'argilla-dev20'
NAME='turkish-bilingual-sft160-dev20-blind-v01'
MODELS=['base','exp-010-tr-only-sft160-step60','exp-010-tr-only-sft160-step100',
        'exp-011-bilingual-sft640-step69','exp-011-bilingual-sft640-step113']


def main():
    assert (RUN/'development-completion.json').exists()
    questions=[json.loads(l) for l in (BASE/'sft160-dev-v01/questions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(questions)==20
    answers={};sources={}
    for model in MODELS:
        p=RUN/'inference'/model/'dev20/answers.jsonl'
        values=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        answers[model]={r['id']:r['prediction'] for r in values}
        assert set(answers[model])=={r['id'] for r in questions}
        sources[model]=hashlib.sha256(p.read_bytes()).hexdigest()
    rng=random.Random(34071118)
    orders=[]
    for _ in range(4):
        block=list(MODELS);rng.shuffle(block)
        orders.extend([block[i:]+block[:i] for i in range(5)])
    rng.shuffle(orders);rng.shuffle(questions)
    records=[];mapping=[]
    for question,order in zip(questions,orders):
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+':'+question['id']))
        prompt='\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in question['messages'])
        fields={'prompt':prompt}
        for letter,model in zip('ABCDE',order):fields['answer_'+letter.lower()]=answers[model][question['id']]
        records.append(dict(id=rid,fields=fields))
        mapping.append(dict(record_id=rid,question_id=question['id'],models=dict(zip('ABCDE',order))))
    for letter in 'ABCDE':
        assert all(sum(r['models'][letter]==m for r in mapping)==4 for m in MODELS)
    OUT.mkdir(parents=True,exist_ok=True)
    payload=dict(sources=sources,records=mapping)
    private=OUT/'PRIVATE-model-key.json'
    if private.exists():assert json.loads(private.read_text(encoding='utf-8'))==payload
    else:private.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    load_dotenv(ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900').rstrip('/')
    client=rg.Argilla(api_url=url,api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    workspace=os.getenv('ARGILLA_WORKSPACE','sft-review')
    dataset=client.datasets(name=NAME,workspace=workspace)
    if dataset is None:
        settings=rg.Settings(fields=[rg.TextField(name='prompt',title='Question',use_markdown=False)]
            +[rg.TextField(name='answer_'+x.lower(),title='Answer '+x,use_markdown=False) for x in 'ABCDE'],
            questions=[rg.TextQuestion(name='ranking',title='Best to worst: A B C D E',required=True,
                description='Example: A > C > E > B = D. Include each letter once; ties allowed.'),
                rg.TextQuestion(name='notes',title='Your reasoning',required=True)],
            guidelines='Rank all five answers and explain your reasoning. Ties allowed. Assess correctness, meaning, requested format and natural Turkish. Flag all-bad answers rather than rewarding fluent mistakes. A-E identities change per question. Only ranking and reasoning; no extra scores. Raw model output is preserved. These are development tasks for checkpoint selection, not the sealed fresh final evaluation.',
            allow_extra_metadata=False)
        dataset=rg.Dataset(name=NAME,workspace=workspace,settings=settings,client=client).create()
    expected={r['id']:r['fields'] for r in records}
    current={str(r.id):r.to_dict() for r in dataset.records}
    assert set(current)<=set(expected)
    for rid,r in current.items():assert r['fields']==expected[rid]
    pending=[rg.Record(id=r['id'],fields=r['fields']) for r in records if r['id'] not in current]
    if pending:dataset.records.log(pending,batch_size=20)
    actual={str(r.id):r.to_dict() for r in dataset.records}
    assert set(actual)==set(expected)
    assert all(r['fields']==expected[rid] for rid,r in actual.items())
    receipt=dict(name=NAME,dataset_id=str(dataset.id),records=20,answers_per_record=5,added=len(pending),
        url=f'{url}/dataset/{dataset.id}/annotation-mode',blind_balanced_positions=True,raw_outputs_verified=True,
        fresh_final_eval_used=False)
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
