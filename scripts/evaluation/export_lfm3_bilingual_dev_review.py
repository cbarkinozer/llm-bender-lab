"""Preserve owner rankings, decoding five anonymous answers only after submission."""
from datetime import datetime,timezone
import hashlib
import json
import os
import re

from dotenv import load_dotenv
import requests
from publish_lfm3_bilingual_dev_argilla import ROOT,BASE,OUT


def parse(text):
    value=text.upper().strip().replace('\u2192','>')
    assert re.fullmatch(r'[A-E\s>,;=]+',value),'Use A-E only, with > or ='
    value=re.sub(r'\s*=\s*','=',value)
    groups=re.split(r'[>,;\s]+',value)
    ranks={}
    for rank,group in enumerate(groups,1):
        for letter in group.split('='):
            assert letter in 'ABCDE' and len(letter)==1 and letter not in ranks
            ranks[letter]=rank
    assert set(ranks)==set('ABCDE'),'Every letter must occur exactly once'
    return ranks


def main():
    receipt=json.loads((OUT/'receipt.json').read_text(encoding='utf-8'))
    private=json.loads((OUT/'PRIVATE-model-key.json').read_text(encoding='utf-8'))
    key={r['record_id']:r for r in private['records']}
    load_dotenv(ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900').rstrip('/')
    response=requests.get(url+f"/api/v1/datasets/{receipt['dataset_id']}/records",
        params={'limit':100,'include':'responses'},headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')},timeout=30)
    response.raise_for_status();raw=response.json()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot=OUT/f'owner-responses-{stamp}.json'
    snapshot.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    decoded=[];invalid=[]
    for row in raw['items']:
        rid=row['external_id']
        assert rid in key
        submitted=[r for r in row['responses'] if r['status']=='submitted']
        assert len(submitted)<=1,'Multiple owner responses require adjudication'
        if not submitted:continue
        values=submitted[0]['values']
        try:
            ranks=parse(values.get('ranking',{}).get('value',''))
            notes=values.get('notes',{}).get('value','')
            assert notes.strip(),'Reasoning missing'
            decoded.append(dict(question_id=key[rid]['question_id'],ranking=values['ranking']['value'],notes=notes,
                model_ranks={model:ranks[letter] for letter,model in key[rid]['models'].items()}))
        except AssertionError as e:invalid.append(dict(record_id=rid,error=str(e)))
    result=dict(records=20,valid_submitted=len(decoded),invalid=invalid,
        snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),reviews=decoded)
    (OUT/'decoded-owner-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['records','valid_submitted','invalid']},ensure_ascii=False))


if __name__=='__main__':main()
