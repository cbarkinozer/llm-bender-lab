"""Create the preselected20-item blind base/F comparison; preserve all responses."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import urllib.request

from score_pair import load

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--experiment-dir', type=Path, default=HERE)
    args = parser.parse_args()
    bm, base = load(args.results_root / 'base')
    fm, adapted = load(args.results_root / 'F')
    for key in ('config', 'questions_sha256', 'packages', 'backend', 'precision', 'chat_template_sha256', 'eos_token_ids'):
        assert bm[key] == fm[key], key
    for a, b in zip(base, adapted):
        for key in ('id', 'document', 'target', 'semantic_prompt', 'rendered_prompt', 'prompt_token_ids'):
            assert a[key] == b[key], (a['id'], key)
    config = json.loads((args.experiment_dir / 'config.json').read_text())
    count = config.get('human_review_count', 20)
    ids = json.loads((args.experiment_dir / config.get('human_review_ids_file', 'data-v1/human-review-20-ids.json')).read_text())
    assert len(ids) == len(set(ids)) == count and count % 2 == 0
    rng = random.Random(config.get('human_review_blind_seed', 'cetvel-tiny-human-blind-3407'))
    labels = ['base'] * (count // 2) + ['F'] * (count // 2)
    rng.shuffle(labels)
    mapping = {item_id: dict(P=first, Q='F' if first == 'base' else 'base')
               for item_id, first in zip(ids, labels)}
    private = args.results_root / 'blind-human-mapping-v1.json'
    blob = (json.dumps(mapping, indent=2) + '\n').encode()
    if private.exists():
        assert private.read_bytes() == blob
    else:
        private.write_bytes(blob)
    indexed = {'base': {r['id']: r for r in base}, 'F': {r['id']: r for r in adapted}}
    fields = {}
    for item_id in ids:
        row = indexed['base'][item_id]
        target = row['target']
        if isinstance(target, dict):
            target = ' / '.join(target['answers']['text']) or '(Kaynakta cevap yok)'
        value = dict(conversation=row['semantic_prompt'], reference_answer=target)
        for position, model in mapping[item_id].items():
            value['answer_' + position] = indexed[model][item_id]['raw_output']
        value['termination'] = '; '.join(position + ': ' + indexed[model][item_id]['finish_reason']
                                        for position, model in mapping[item_id].items())
        fields[item_id] = value
    import argilla as rg
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    client = rg.Argilla(api_url=url, api_key=key)
    name = config.get('argilla_dataset_name', 'cetvel-tiny-base-f-blind-20-v1')
    dataset = client.datasets(name=name, workspace='sft-review')
    if dataset is None:
        guidelines = (f'Bu{count} soru çıktıları görmeden rastgele seçildi: her görevden{count // 5}. P/Q her soruda yeniden '
            'karıştırılmıştır; sabit model kimliği değildir. Her cevaba pass/partial/fail ver, '
            'sonra en iyi P/Q/tie/neither seç. Pass=doğru, anlamı koruyor ve yeterli; partial=önemli eksik '
            'veya yerel sorun; fail=yanlış, uydurma, anlamı bozuyor veya görevi karşılamıyor. '
            'Önce içerik ve anlam, sonra doğal Türkçe ve uygun uzunluk. Referansla aynı sözcükler şart değil; '
            'doğru alternatif çeviri/düzeltme/özet kabul edilir. Sadece kısalık/Markdown bir içerik kazanımı '
            'değildir. Referans özet tüm kabul edilebilir cevapların listesi değildir. '
            'Native EOS dışındaki sonlanmalar eksik üretimdir; notta belirt. İstersen kısa gerekçe yaz.')
        titles = dict(conversation='Soru / kaynak', reference_answer='Referans cevap',
                      answer_P='P cevabı', answer_Q='Q cevabı', termination='Sonlandırma')
        settings = rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=name, title=titles[name], use_markdown=False)
                    for name in next(iter(fields.values()))], questions=[
                rg.LabelQuestion(name='best_output', title='En iyi cevap?', labels=['P', 'Q', 'tie', 'neither']),
                rg.LabelQuestion(name='P_grade', title='P', labels=['pass', 'partial', 'fail']),
                rg.LabelQuestion(name='Q_grade', title='Q', labels=['pass', 'partial', 'fail']),
                rg.TextQuestion(name='notes', title='Kısa not (isteğe bağlı)', required=False, use_markdown=False)])
        dataset = rg.Dataset(name=name, workspace='sft-review',
                             settings=settings, client=client).create()
        dataset.records.log([rg.Record(id=item_id, fields=value) for item_id, value in fields.items()])
    request = urllib.request.Request(f'{url}/api/v1/datasets/{dataset.id}/records?limit=100&include=responses',
                                     headers={'X-Argilla-Api-Key': key})
    actual = json.load(urllib.request.urlopen(request, timeout=30))
    assert actual['total'] == len(actual['items']) == count
    assert {r['external_id']: r['fields'] for r in actual['items']} == fields
    info = dict(id=str(dataset.id), count=count, fields_verified=True, blinded=True,
                mapping_sha256=hashlib.sha256(blob).hexdigest(),
                url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
    (args.results_root / 'argilla-link.json').write_text(json.dumps(info, indent=2) + '\n')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
