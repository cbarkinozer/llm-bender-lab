"""Sixteen Turkish questions, four blinded candidates, ranking and notes only."""
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
RUN=BASE/'preservation-session-v01-local'
NAME='turkish-preservation16-blind-v01'
MODELS=['base','bilingual69','exp-012-base-bilingual','exp-013-base-preservation']

def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]

def main():
    assert json.loads((RUN/'completion.json').read_text())['status']=='completed'
    prompts=[r for r in rows(BASE/'capability-preservation-v01/eval-prompts.jsonl') if r['output_language']=='tr']
    assert len(prompts)==16
    answers={};sources={}
    for model in MODELS:
        p=RUN/'inference/fresh'/model/'answers.jsonl';values=rows(p)
        assert len(values)==32
        answers[model]={r['id']:r['raw_output'] for r in values};sources[model]=hashlib.sha256(p.read_bytes()).hexdigest()
    rng=random.Random(34071120);orders=[]
    for block in range(4):
        order=MODELS.copy();rng.shuffle(order)
        orders.extend([order[j:]+order[:j] for j in range(4)])
    rng.shuffle(orders);rng.shuffle(prompts)
    records=[];key=[]
    for prompt,order in zip(prompts,orders):
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+':'+prompt['id']))
        fields={'prompt':'\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in prompt['messages'])}
        for letter,model in zip('ABCD',order):fields[letter.lower()]=answers[model][prompt['id']]
        records.append(dict(id=rid,fields=fields));key.append(dict(record_id=rid,task_id=prompt['id'],models=dict(zip('ABCD',order))))
    out=RUN/'argilla';out.mkdir(parents=True,exist_ok=True)
    payload=dict(sources=sources,records=key);private=out/'PRIVATE-model-key.json'
    if private.exists():assert json.loads(private.read_text(encoding='utf-8'))==payload
    else:private.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    load_dotenv(ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900').rstrip('/')
    client=rg.Argilla(api_url=url,api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    workspace=os.getenv('ARGILLA_WORKSPACE','sft-review');dataset=client.datasets(name=NAME,workspace=workspace)
    if dataset is None:
        settings=rg.Settings(fields=[rg.TextField(name='prompt',title='Question',use_markdown=False)]+[
            rg.TextField(name=x.lower(),title='Answer '+x,use_markdown=False) for x in 'ABCD'],
            questions=[rg.TextQuestion(name='ranking',title='Best to worst: A B C D',required=True,
                description='Example: A > C > B > D. Ties: A = C > B > D. Use every letter once.'),
                rg.TextQuestion(name='notes',title='Your reasoning',required=True)],
            guidelines='One Turkish question per record. Rank correctness, preserved meaning, natural Turkish and instruction following. Note arithmetic errors, ambiguity or all-wrong cases. A/B/C/D are shuffled independently between records: never total letters across records. Only ranking and reasoning are required. Raw outputs are preserved; references and model identities are hidden.',allow_extra_metadata=False)
        dataset=rg.Dataset(name=NAME,workspace=workspace,settings=settings,client=client).create()
    expected={r['id']:r['fields'] for r in records};current={str(r.id):r.to_dict() for r in dataset.records}
    assert set(current)<=set(expected)
    assert all(r['fields']==expected[rid] for rid,r in current.items())
    pending=[rg.Record(id=r['id'],fields=r['fields']) for r in records if r['id'] not in current]
    if pending:dataset.records.log(pending,batch_size=8)
    actual={str(r.id):r.to_dict() for r in dataset.records}
    assert set(actual)==set(expected) and all(r['fields']==expected[rid] for rid,r in actual.items())
    receipt=dict(name=NAME,id=str(dataset.id),records=16,answers_per_record=4,
        url=f'{url}/dataset/{dataset.id}/annotation-mode',raw_outputs_verified=True)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
