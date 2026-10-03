"""Preserve earlier review queues; create exp010 development comparison."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import argilla as rg

def read(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='completed' and manifest['count']==20
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected
    rows=[json.loads(s) for s in (root/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    return {r['id']:r for r in rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results-root',type=Path,required=True)
    p.add_argument('--exp009-results',type=Path,required=True)
    a=p.parse_args()
    one=read(a.results_root/'validation-epoch1-v1'); two=read(a.results_root/'validation-epoch2-v1'); old=read(a.exp009_results)
    assert set(one)==set(two)==set(old) and len(two)==20
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')
    client=rg.Argilla(api_url=url,api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    name='exp-010-lr-validation-20'
    dataset=client.datasets(name=name,workspace='sft-review')
    records=[]
    for id,r in two.items():
        assert r['messages']==one[id]['messages']==old[id]['messages']
        records.append(rg.Record(id=id,fields=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),
            base_answer=r['original_answer'],desired_answer=r['desired_answer'],exp009_answer=old[id]['adapter_answer'],
            exp010_epoch1=one[id]['adapter_answer'],exp010_epoch2=r['adapter_answer'],category=r['category'])))
    if dataset is None:
        settings=rg.Settings(guidelines='Exp010 yalnizca LR 5e-5 -> 1e-4 degisikligi: ayni 80 egitim, 20 development-validation sorusu, iki epoch. Epoch1 ve epoch2 cevaplarini hedefe gore degerlendir. Dogruluk ve dogal Turkceyi kisaliktan once tut; gereksiz Markdown/emoji, uzatma, desteksiz iddia ve soru dongusunu isaretle. Bu bir egitim verisi duzeltme ekrani degil, model incelemesidir. Base eski vLLM run; diger cevaplar ayni Unsloth/Transformers backend. Inceleme blind degildir. Onceki exp009 annotasyonlari korunur.',
            fields=[rg.TextField(name=f,use_markdown=False) for f in ['conversation','base_answer','desired_answer','exp009_answer','exp010_epoch1','exp010_epoch2','category']],
            questions=[rg.LabelQuestion(name='best_exp010_epoch',title='Exp010 hangi epoch daha iyi?',labels=['epoch1','epoch2','tie','neither'],required=True),
                rg.LabelQuestion(name='epoch2_quality',title='Epoch2 hedefi karsiliyor mu?',labels=['pass','partial','fail'],required=True),
                rg.MultiLabelQuestion(name='epoch2_issues',title='Epoch2 sorunlari (varsa)',labels=['incorrect','turkish','too_long','too_short','markdown_emoji','unsupported_claim','anthropomorphism','unnecessary_question','repetition'],required=False),
                rg.TextQuestion(name='notes',required=False,use_markdown=False)])
        dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log(records)
    info=dict(name=name,id=str(dataset.id),url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (a.results_root/'argilla-link.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info))

if __name__=='__main__':
    main()
