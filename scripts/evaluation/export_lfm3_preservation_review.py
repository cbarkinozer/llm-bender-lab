"""Preserve submitted ABCD judgments and decode per-record identities, with ties."""
from datetime import datetime,timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import statistics

import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'preservation-session-v01-local'
OUT=RUN/'argilla'
MODELS=['base','bilingual69','exp-012-base-bilingual','exp-013-base-preservation']

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def parse(text):
    text=text.upper().strip().replace('→','>')
    assert re.fullmatch(r'[A-D\s>,;=]+',text),'Use A-D with > or ='
    groups=re.split(r'[>,;\s]+',re.sub(r'\s*=\s*','=',text))
    ranks={}
    for rank,group in enumerate(groups,1):
        for letter in group.split('='):
            assert len(letter)==1 and letter in 'ABCD' and letter not in ranks
            ranks[letter]=rank
    assert set(ranks)==set('ABCD'),'Every letter exactly once'
    return ranks

def main():
    receipt=read(OUT/'receipt.json');key=read(OUT/'PRIVATE-model-key.json')
    mapping={r['record_id']:r for r in key['records']}
    for model,digest in key['sources'].items():
        p=RUN/'inference/fresh'/model/'answers.jsonl'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    load_dotenv(ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900').rstrip('/')
    response=requests.get(url+f"/api/v1/datasets/{receipt['id']}/records",params={'limit':100,'include':'responses'},
        headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')},timeout=30)
    response.raise_for_status();raw=response.json()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');snapshot=OUT/f'owner-responses-{stamp}.json'
    dump(snapshot,raw)
    assert len(raw['items'])==16
    prompts={r['id']:r for r in map(json.loads,(BASE/'capability-preservation-v01/eval-prompts.jsonl').read_text(encoding='utf-8').splitlines())}
    answers={model:{r['id']:r['raw_output'] for r in map(json.loads,(RUN/'inference/fresh'/model/'answers.jsonl').read_text(encoding='utf-8').splitlines())} for model in MODELS}
    decoded=[];invalid=[];statuses={}
    for row in raw['items']:
        rid=row['external_id'];assert rid in mapping
        identity=mapping[rid];tid=identity['task_id']
        for letter,model in identity['models'].items():assert row['fields'][letter.lower()]==answers[model][tid]
        submitted=[r for r in row['responses'] if r['status']=='submitted']
        for r in row['responses']:statuses[r['status']]=statuses.get(r['status'],0)+1
        assert len(submitted)<=1,'Multiple submitted judgments need adjudication'
        if not submitted:continue
        values=submitted[0]['values']
        try:
            ranks=parse(values['ranking']['value']);notes=values['notes']['value'];assert notes.strip()
            decoded.append(dict(record_id=rid,task_id=tid,category=prompts[tid]['category'],
                ranking=values['ranking']['value'],notes=notes,
                model_ranks={model:ranks[letter] for letter,model in identity['models'].items()}))
        except (AssertionError,KeyError) as e:invalid.append(dict(record_id=rid,error=str(e)))
    result=dict(records=16,valid_submitted=len(decoded),invalid=invalid,response_status_counts=statuses,
        review_provenance='Owner-supplied review; user reports API reading and AI-assisted evaluation. Judge model/prompt unavailable; not independent human correctness adjudication.',
        snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),snapshot_path=snapshot.relative_to(ROOT).as_posix(),reviews=decoded)
    dump(OUT/'decoded-owner-review.json',result)
    assert len(decoded)==16 and not invalid and len({r['task_id'] for r in decoded})==16
    def scores(subset):
        return {m:dict(pairwise_preference=sum(sum(1 if r['model_ranks'][m]<r['model_ranks'][o] else .5 if r['model_ranks'][m]==r['model_ranks'][o] else 0 for o in MODELS if o!=m) for r in subset)/(3*len(subset)),
            mean_rank=statistics.mean(1+sum(v<r['model_ranks'][m] for v in r['model_ranks'].values())+(sum(v==r['model_ranks'][m] for v in r['model_ranks'].values())-1)/2 for r in subset),
            top_including_ties=sum(r['model_ranks'][m]==min(r['model_ranks'].values()) for r in subset)) for m in MODELS}
    summary=dict(snapshot_sha256=result['snapshot_sha256'],n=16,metric='Preference among mostly unsuccessful answers; NOT accuracy',
        review_provenance=result['review_provenance'],models=scores(decoded),pairs={},subsets={})
    for left,right in itertools.combinations(MODELS,2):
        signs=[1 if r['model_ranks'][left]<r['model_ranks'][right] else 0 if r['model_ranks'][left]==r['model_ranks'][right] else -1 for r in decoded]
        rng=random.Random(3407);boot=sorted(statistics.mean(rng.choices(signs,k=16)) for _ in range(10000))
        summary['pairs'][left+' vs '+right]=dict(wins=signs.count(1),ties=signs.count(0),losses=signs.count(-1),
            net_win_rate=statistics.mean(signs),exploratory_item_bootstrap_95=[boot[249],boot[9749]])
    for label,ids in [('numeric',set(range(1,8))),('logic',{8}),('general_language',set(range(17,25)))]:
        subset=[r for r in decoded if int(r['task_id'].split('-')[-1]) in ids]
        summary['subsets'][label]=dict(n=len(subset),models=scores(subset))
    dump(RUN/'analysis/owner-preference-summary.json',summary)
    dump(BASE/'PRESERVATION-OWNER-REVIEW.json',dict(decoded=result,summary=summary))
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
