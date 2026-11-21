"""Cookbook Turkish development review, three blinded candidates, ranking and notes only."""
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
RUN=BASE/'cookbook-runtime-local'
NAME='turkish-cookbook34-blind-v01'
MODELS=['base','exp-014-completion-mask','exp-015-cookbook-recipe']

def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]

def main():
    receipt=json.loads((RUN/'LOCAL-BACKUP-RECEIPT.json').read_text())
    assert receipt['status']=='verified' and not receipt['full_weights_included']
    prompts=[];answers={};sources={}
    for mode,packet in [('off','prompts.jsonl'),('on','thinking-prompts.jsonl')]:
        selected=[dict(r,review_mode=mode) for r in rows(BASE/'stage-diagnostic-v01'/packet)
                  if r.get('direction') in ['tr-tr','en-tr'] and r['cohort']!='seen-training-probe']
        assert len(selected)==(26 if mode=='off' else 8)
        prompts.extend(selected)
        for model in MODELS:
            root=RUN/'base' if model=='base' else BASE/model/'results-local'
            p=root/('inference-'+mode)/'answers.jsonl';values=rows(p)
            manifest=json.loads((p.parent/'manifest.json').read_text())
            assert manifest['status']=='completed' and len(values)==(72 if mode=='off' else 16)
            assert manifest['decoding']['enable_thinking']==(mode=='on')
            sources[model+'/'+mode]=hashlib.sha256(p.read_bytes()).hexdigest()
            answers[model,mode]={r['id']:r['raw_output'] for r in values}
    rng=random.Random(34071121);orders=[]
    for block in range(12):
        order=MODELS.copy();rng.shuffle(order)
        orders.extend([order[j:]+order[:j] for j in range(3)])
    orders=orders[:len(prompts)];rng.shuffle(orders);rng.shuffle(prompts)
    records=[];key=[]
    for prompt,order in zip(prompts,orders):
        mode=prompt['review_mode']
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+':'+mode+':'+prompt['id']))
        context='Thinking '+('ON' if mode=='on' else 'OFF')+' | '+prompt['direction'].upper()
        fields={'prompt':context+'\n\n'+'\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in prompt['messages'])}
        for letter,model in zip('ABC',order):fields[letter.lower()]=answers[model,mode][prompt['id']]
        records.append(dict(id=rid,fields=fields))
        key.append(dict(record_id=rid,task_id=prompt['id'],mode=mode,direction=prompt['direction'],cohort=prompt['cohort'],models=dict(zip('ABC',order))))
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
            rg.TextField(name=x.lower(),title='Answer '+x,use_markdown=False) for x in 'ABC'],
            questions=[rg.TextQuestion(name='ranking',title='Best to worst: A B C',required=True,
                description='Example: A > C > B. Ties: A = C > B. Use every letter once.'),
                rg.TextQuestion(name='notes',title='Your reasoning',required=True)],
            guidelines='34 records: 26 Turkish-output questions with thinking OFF and eight Turkish arithmetic questions with thinking ON. Modes are shown in the question. Judge the final answer and note missing thinking closure; raw reasoning is retained. This is consumed development data, not a fresh test. One question per record. Rank correctness, preserved meaning, natural Turkish and instruction following. Note arithmetic errors, ambiguity or all-wrong cases. A/B/C are shuffled independently between records: never total letters across records. Only ranking and reasoning are required. Raw outputs are preserved; references and model identities are hidden.',allow_extra_metadata=False)
        dataset=rg.Dataset(name=NAME,workspace=workspace,settings=settings,client=client).create()
    expected={r['id']:r['fields'] for r in records};current={str(r.id):r.to_dict() for r in dataset.records}
    assert set(current)<=set(expected)
    assert all(r['fields']==expected[rid] for rid,r in current.items())
    pending=[rg.Record(id=r['id'],fields=r['fields']) for r in records if r['id'] not in current]
    if pending:dataset.records.log(pending,batch_size=8)
    actual={str(r.id):r.to_dict() for r in dataset.records}
    assert set(actual)==set(expected) and all(r['fields']==expected[rid] for rid,r in actual.items())
    receipt=dict(name=NAME,id=str(dataset.id),records=len(records),answers_per_record=3,
        url=f'{url}/dataset/{dataset.id}/annotation-mode',raw_outputs_verified=True)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
