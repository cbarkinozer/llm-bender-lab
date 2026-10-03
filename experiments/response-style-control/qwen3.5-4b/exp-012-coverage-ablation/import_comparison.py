"""Import verified A/B final-epoch development outputs without altering older reviews."""
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
    args=p.parse_args()
    ma,a=read(args.results_root/'A/validation-v1')
    mb,b=read(args.results_root/'B/validation-v1')
    assert set(a)==set(b) and ma['validation_sha256']==mb['validation_sha256']
    for key in ('generation','seed','chat_template_sha256','backend','precision','revision'):
        assert ma[key]==mb[key],key
    fields={}
    for id,r in a.items():
        s=b[id]
        assert r['messages']==s['messages'] and r['desired_answer']==s['desired_answer'] and r['prompt_token_ids']==s['prompt_token_ids']
        fields[id]=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),
            desired_answer=r['desired_answer'],answer_A=r['adapter_answer'],answer_B=s['adapter_answer'],
            category=r['category'],termination=f"A: {r['finish_reason']}, {r['output_tokens']} tokens; B: {s['finish_reason']}, {s['output_tokens']} tokens. Non-EOS outputs are incomplete failures.")
    with (args.results_root/'desired-A-B-comparison.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['id',*next(iter(fields.values()))])
        writer.writeheader()
        for id,payload in fields.items():
            writer.writerow(dict(id=id,**payload))
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')
    key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    client=rg.Argilla(api_url=url,api_key=key)
    name='exp-011-012-paired-validation-20'
    dataset=client.datasets(name=name,workspace='sft-review')
    if dataset is None:
        guidelines=('A = exp011: mevcut 80 eğitim örneği, 4 epoch. B = exp012: aynı toplam 80 örnek, '
            '56 mevcut + 24 yeni onaylı senaryo, aynı 4 epoch ve LR1e-4. İkisi de bağımsız olarak aynı base modelden başlar. '
            'Bu ekran eğitim hedefi düzeltmek için değil, değişmeyen 20 development sorusunda final epoch4 cevaplarını karşılaştırmak içindir. '
            'Önce doğruluk, gerekçenin öneriye bağlantısı, desteksiz iddia/çelişki ve doğal Türkçe; sonra gereksiz soru, '
            'antropomorfizm, uzunluk, tekrar ve biçim. Hedefin sözcüklerini aynen kullanması gerekmez. '
            'Faydalı liste veya istenmiş Markdown tek başına hata değildir. Kısa cevap yanlışsa başarılı sayılmaz. '
            'Native EOS dışındaki duruşlar eksik başarısız çıktılardır. İnceleme kör değildir; bu set bağımsız final test değildir. '
            'B aynı adım sayısında yaklaşık %22.47 daha fazla hedef token görür; fark yalnızca veri kalitesine atfedilemez. '
            'me-049,050,059,069,070,079,089,090 ana tanısal sorular; kalanlar regresyon kontrolleridir.')
        settings=rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=f,use_markdown=False) for f in next(iter(fields.values()))],
            questions=[rg.LabelQuestion(name='preferred',title='Hangi cevap daha iyi?',labels=['A','B','tie','neither'],required=True),
                rg.LabelQuestion(name='A_substance',title='A: içerik hedefi karşılıyor mu?',labels=['pass','partial','fail'],required=True),
                rg.LabelQuestion(name='B_substance',title='B: içerik hedefi karşılıyor mu?',labels=['pass','partial','fail'],required=True),
                *[rg.MultiLabelQuestion(name=f'{arm}_issues',title=f'{arm}: sorunlar (varsa)',
                    labels=['incorrect','unsupported_claim','contradiction','turkish','unnecessary_question','anthropomorphism',
                            'too_long','too_short','markdown_emoji','repetition','incomplete'],required=False) for arm in ('A','B')],
                rg.TextQuestion(name='notes',title='Notlar',required=False,use_markdown=False)])
        dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log([rg.Record(id=id,fields=payload) for id,payload in fields.items()])
    request=urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100',headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(request,timeout=30) as response:
        items=json.load(response)['items']
    assert len(items)==20 and {r['external_id']:r['fields'] for r in items}==fields,'Existing queue differs; never overwrite annotations'
    info=dict(name=name,id=str(dataset.id),count=20,url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (args.results_root/'argilla-link.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(info))

if __name__=='__main__':
    main()
