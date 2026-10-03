"""Verified desired/A/C/D development review, without modifying old annotations."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import argilla as rg


def read(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='completed' and manifest['count']==20
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
    rows=[json.loads(line) for line in (root/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==20 and len({r['id'] for r in rows})==20
    return manifest,{r['id']:r for r in rows}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results-root',type=Path,required=True)
    p.add_argument('--a-results',type=Path,required=True)
    args=p.parse_args()
    arms={'A':read(args.a_results),'C':read(args.results_root/'C/validation-v1'),
          'D':read(args.results_root/'D/validation-v1')}
    ma,a=arms['A']
    for arm,(manifest,rows) in arms.items():
        assert set(a)==set(rows)
        for key in ('validation_sha256','generation','seed','chat_template_sha256','backend','precision','revision'):
            assert ma[key]==manifest[key],(arm,key)
        for id,row in a.items():
            assert row['messages']==rows[id]['messages'] and row['desired_answer']==rows[id]['desired_answer']
            assert row['prompt_token_ids']==rows[id]['prompt_token_ids'],(arm,id)
    fields={}
    for id,r in a.items():
        reference_note=('Tartışmalı referans: assistant QA kısaltmasıdır, kullanıcının ilk hedefi değildir. '
                        'Eski referans korunmuştur; 19 soruluk hassasiyet özeti ayrıca raporlanmalı.' if id=='me-089' else '')
        fields[id]=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),
            desired_answer=r['desired_answer'],answer_A=r['adapter_answer'],
            answer_C=arms['C'][1][id]['adapter_answer'],answer_D=arms['D'][1][id]['adapter_answer'],
            category=r['category'],reference_note=reference_note,
            termination='; '.join(f"{arm}: {rows[id]['finish_reason']}, {rows[id]['output_tokens']} tokens" for arm,(_,rows) in arms.items()))
    with (args.results_root/'desired-A-C-D-comparison.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['id',*next(iter(fields.values()))])
        writer.writeheader()
        writer.writerows(dict(id=id,**value) for id,value in fields.items())
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')
    key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    client=rg.Argilla(api_url=url,api_key=key)
    name='exp-013-014-A-C-D-validation-20'
    dataset=client.datasets(name=name,workspace='sft-review')
    if dataset is None:
        guidelines=('A=exp011 eski80 hedef,4epoch. C=exp013 aynı80 toplam:68eski+12onaylı yeni,4epoch. '
            'D=exp014 C ile BİREBİR aynı eğitim verisi,6epoch. Her biri fresh base başlangıç; LR1e-4,rank16. '
            'C/A veri değişimi; D/C daha uzun cosine eğitim reçetesi. C hedef token/epoch yaklaşık%5 fazla. '
            'Önce içerik doğruluğu, kanıt, gerekçenin öneriye bağlantısı, doğal Türkçe ve belirsizlik; '
            'sonra gereksiz soru, antropomorfizm, tekrar/uzunluk/biçim. Kısa olması tek başına başarı değil. '
            'Hedefin sözcüklerini aynen kullanmak gerekmiyor. Native EOS dışı duruş eksik başarısız çıktı. '
            'me-089 referansı tartışmalı, reference_note alanını okuyun. Bu20 tekrar kullanılan development '
            'setidir, bağımsız final test değil; inceleme kör değildir. Eğitim hedeflerini burada değiştirmeyin.')
        settings=rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=f,use_markdown=False) for f in next(iter(fields.values()))],
            questions=[rg.LabelQuestion(name='preferred',title='Hangi cevap daha iyi?',labels=['A','C','D','tie','neither'],required=True),
                *[rg.LabelQuestion(name=f'{arm}_substance',title=f'{arm}: içerik hedefi karşılıyor mu?',
                    labels=['pass','partial','fail'],required=True) for arm in arms],
                *[rg.MultiLabelQuestion(name=f'{arm}_issues',title=f'{arm}: sorunlar',labels=['incorrect','unsupported_claim',
                    'contradiction','turkish','unnecessary_question','anthropomorphism','too_long','too_short',
                    'markdown_emoji','repetition','incomplete'],required=False) for arm in arms],
                rg.TextQuestion(name='notes',title='Notlar',required=False,use_markdown=False)])
        dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log([rg.Record(id=id,fields=value) for id,value in fields.items()])
    request=urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100&include=responses',
        headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(request,timeout=30) as response:
        actual=json.load(response)
    assert actual['total']==len(actual['items'])==20
    assert {r['external_id']:r['fields'] for r in actual['items']}==fields,'Never overwrite changed existing fields/reviews'
    info=dict(name=name,id=str(dataset.id),count=20,url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (args.results_root/'argilla-link.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(info))


if __name__=='__main__':
    main()
