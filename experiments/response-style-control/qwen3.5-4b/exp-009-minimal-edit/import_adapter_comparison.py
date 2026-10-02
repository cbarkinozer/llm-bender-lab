"""Create a separate 20-item development review; preserve previous annotations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import argilla as rg

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results-dir',type=Path,required=True)
    a=p.parse_args()
    manifest=json.loads((a.results_dir/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='completed' and manifest['count']==20
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((a.results_dir/name).read_bytes()).hexdigest()==expected
    rows=[json.loads(s) for s in (a.results_dir/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==20 and [r['id'] for r in rows]==manifest['ids']
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')
    client=rg.Argilla(api_url=url,api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    name='exp-009-adapter-validation-20'
    dataset=client.datasets(name=name,workspace='sft-review')
    if dataset is None:
        fields=['conversation','base_answer','desired_answer','adapter_answer','category']
        settings=rg.Settings(
            guidelines='Bu 20 kayit egitimde kullanilmayan development-validation karsilastirmasidir. Base, istedigin cevap ve adaptor cevabini karsilastir. Dogruluk, dogal Turkce, gerekli detay, gereksiz uzunluk/Markdown/emoji, desteksiz iddia, antropomorfizm ve gereksiz soru sormayi degerlendir. Kisaligi tek basina basari sayma. Istenen cevap bir referanstir, birebir kelime eslesmesi gerekmez. Base vLLM, adaptor Unsloth/Transformers kullandi; backend farki vardir. Bu inceleme kor/blind degildir. Burada egitim hedeflerini degistirmiyoruz.',
            fields=[rg.TextField(name=f,use_markdown=False) for f in fields],
            questions=[
                rg.LabelQuestion(name='preference',title='Hangisi daha iyi?',labels=['adapter','base','tie'],required=True),
                rg.LabelQuestion(name='adapter_quality',title='Adaptor cevabi hedefi karsiliyor mu?',labels=['pass','partial','fail'],required=True),
                rg.MultiLabelQuestion(name='issues',title='Adaptor sorunlari (yalnizca varsa)',labels=['incorrect','turkish','too_long','too_short','markdown_emoji','unsupported_claim','anthropomorphism','unnecessary_question','repetition'],required=False),
                rg.TextQuestion(name='notes',title='Notlar',required=False,use_markdown=False)])
        dataset=rg.Dataset(name=name,workspace='sft-review',settings=settings,client=client).create()
        dataset.records.log([rg.Record(id=r['id'],fields=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),base_answer=r['original_answer'],desired_answer=r['desired_answer'],adapter_answer=r['adapter_answer'],category=r['category'])) for r in rows])
    info=dict(id=str(dataset.id),name=name,url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (a.results_dir/'argilla-comparison-link.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(info))

if __name__=='__main__':
    main()
