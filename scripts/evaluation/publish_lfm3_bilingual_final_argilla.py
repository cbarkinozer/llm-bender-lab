"""35 blind grouped tasks, three models and four directions; ranking and notes only."""
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
RUN=BASE/'final-eval-v01-local'
OUT=RUN/'argilla'
NAME='turkish-bilingual-final35-blind-v01'
MODELS=['base','turkish60','bilingual69']
DIRECTIONS=['tr-tr','en-tr','tr-en','en-en']


def main():
    assert json.loads((RUN/'completion.json').read_text())['status']=='completed'
    rows=[json.loads(l) for l in (BASE/'bilingual-pilot-v01/eval-v01/eval-prompts.jsonl').read_text(encoding='utf-8').splitlines()]
    groups={}
    for r in rows:groups.setdefault(r['group_id'],{})[r['direction']]=r
    assert len(groups)==35 and all(set(g)==set(DIRECTIONS) for g in groups.values())
    answers={};sources={}
    for model in MODELS:
        p=RUN/'inference'/model/'answers.jsonl'
        values=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        assert len(values)==148
        answers[model]={r['id']:r['raw_output'] for r in values}
        sources[model]=hashlib.sha256(p.read_bytes()).hexdigest()
    rng=random.Random(34071119)
    orders=[]
    for i in range(12):
        block=list(MODELS);rng.shuffle(block)
        orders.extend([block[j:]+block[:j] for j in range(3)])
    orders=orders[:35];rng.shuffle(orders)
    group_ids=list(groups);rng.shuffle(group_ids)
    records=[];mapping=[]
    for gid,order in zip(group_ids,orders):
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+':'+gid));fields={}
        for direction in DIRECTIONS:
            r=groups[gid][direction];prefix=direction.replace('-','_')
            fields[prefix+'_prompt']='\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in r['messages'])
            for letter,model in zip('ABC',order):fields[prefix+'_'+letter.lower()]=answers[model][r['id']]
        records.append(dict(id=rid,fields=fields))
        mapping.append(dict(record_id=rid,group_id=gid,models=dict(zip('ABC',order))))
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
        fields=[]
        for direction in DIRECTIONS:
            prefix=direction.replace('-','_')
            fields.append(rg.TextField(name=prefix+'_prompt',title=direction.upper()+' — Question',use_markdown=False))
            fields.extend(rg.TextField(name=prefix+'_'+x.lower(),title=direction.upper()+' — Answer '+x,use_markdown=False) for x in 'ABC')
        settings=rg.Settings(fields=fields,questions=[
            rg.TextQuestion(name='ranking',title='Overall best to worst: A B C',required=True,description='Example: A > C > B; ties: A = B > C. Each letter once.'),
            rg.TextQuestion(name='notes',title='Your reasoning',required=True)],
            guidelines='Each record is ONE task in four language directions. A/B/C identify the same models within this record, but change between records. Rank overall correctness, meaning preservation, requested language and naturalness. Mention specific directions in your notes where useful. Mark all-wrong cases in notes. Raw outputs, including special tokens, are preserved. Only ranking and reasoning are required. References and model identities are hidden.',allow_extra_metadata=False)
        dataset=rg.Dataset(name=NAME,workspace=workspace,settings=settings,client=client).create()
    expected={r['id']:r['fields'] for r in records}
    current={str(r.id):r.to_dict() for r in dataset.records}
    assert set(current)<=set(expected)
    assert all(r['fields']==expected[rid] for rid,r in current.items())
    pending=[rg.Record(id=r['id'],fields=r['fields']) for r in records if r['id'] not in current]
    if pending:dataset.records.log(pending,batch_size=10)
    actual={str(r.id):r.to_dict() for r in dataset.records}
    assert set(actual)==set(expected) and all(r['fields']==expected[rid] for rid,r in actual.items())
    receipt=dict(name=NAME,dataset_id=str(dataset.id),records=35,answers_per_record=12,
        url=f'{url}/dataset/{dataset.id}/annotation-mode',raw_outputs_verified=True,identities_consistent_within_group=True)
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
