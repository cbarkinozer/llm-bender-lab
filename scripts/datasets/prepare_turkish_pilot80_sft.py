"""Version owner-approved pilot corrections and shared systems; no tokenization yet."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
SOURCE = BASE / 'reviewed-pilot-v01'
OUT = BASE / 'sft-pilot80-v01'
SYSTEM = ('Sen doğru, yardımsever ve güvenilir bir Türkçe asistansın. '
          'Kullanıcının istediği biçime ve kısıtlara uy. Yanıtın ayrıntısını sorunun '
          'gerektirdiği düzeye göre ayarla. Belirsizliği belirt; eksik bilgiyi uydurma.')
FIXES = {
    'atlas:train.chat.jsonl:312719': {
        'reason': 'Owner-authorized correction: distinguish profit margin from markup.',
        'worked_solution': ('Kâr marjı, kârın KDV hariç satış fiyatına oranıdır. '
                            'Satış fiyatına S dersek (S - 450) / S = 0,20 olur. '
                            'Buradan 0,80S = 450 ve S = 562,50 TL bulunur. '
                            'KDV 562,50 × 0,20 = 112,50 TL; toplam 675 TL olur.'),
        'answer': ('KDV dahil satış fiyatı 675 TL olur. %20 kâr marjı için '
                   'KDV hariç fiyat 450 / 0,80 = 562,50 TL olmalıdır. '
                   '%20 KDV eklendiğinde 562,50 × 1,20 = 675 TL elde edilir. '
                   'Maliyetin üzerine %20 eklemek ise kâr marjı değil, maliyet üzerinden kâr oranıdır.'),
    },
    'cot:train.jsonl:247': {
        'reason': 'Owner-authorized correction: insufficient premises for forced contradiction.',
        'worked_solution': None,
        'answer': ('Verilen bilgilerle seçeneklerden hiçbiri zorunlu olarak doğru değildir. '
                   'Yeni vergi kalemleri eklenirken farklı vergilerde indirim yapılabilir; '
                   'bu iki politika aynı anda uygulanabilir. B seçeneğindeki çelişkiyi '
                   'söyleyebilmek için aynı verginin, aynı mükellef grubu ve aynı dönem '
                   'için aynı koşullarda hem artırılacağı hem azaltılacağı belirtilmelidir. '
                   'Metin bunu söylemediği için B kesin cevap olamaz; soru bu haliyle kusurludur.'),
    },
    'atlas:train.chat.jsonl:213455': {
        'reason': 'Owner-authorized correction: do not assume unauthorized access.',
        'worked_solution': None,
        'answer': ('Kendi maaş bilginize mi, yoksa göreviniz kapsamında erişim yetkiniz '
                   'olan bir kayda mı ulaşmak istiyorsunuz? Kendi bilginiz için çalışan '
                   'portalını veya İK’nın resmî talep kanalını kullanabilirsiniz. Yetkili '
                   'bir raporlama görevi içinse kurumun onaylı İK uygulamasını ve size '
                   'tanımlanmış erişim izinlerini kullanın; veritabanı erişimi gerekiyorsa '
                   'İK ve sistem yöneticisinden uygun yetkiyi talep edin.'),
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
    OUT.mkdir(exist_ok=True)
    changes = []
    ids = set()
    for split, count in [('train', 80), ('test', 20)]:
        source = SOURCE / f'{split}.jsonl'
        assert sha(source) == manifest['files'][source.name]
        rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
        assert len(rows) == count
        for row in rows:
            assert row['split'] == split and row['id'] not in ids
            ids.add(row['id'])
            row['original_reviewed_messages'] = copy.deepcopy(row['messages'])
            row['original_reviewed_target'] = row['reviewed_target']
            row['original_worked_solution'] = row['worked_solution']
            if split == 'train' and row['id'] in FIXES:
                fix = FIXES[row['id']]
                row['messages'][-1]['content'] = fix['answer']
                row['worked_solution'] = fix['worked_solution']
                row['reviewed_target'] = (f"<thinking>{fix['worked_solution']}</thinking>"
                                          if fix['worked_solution'] else '') + fix['answer']
                changes.append({'id': row['id'], **fix})
            row['messages'] = [m for m in row['messages'] if m['role'] != 'system']
            row['messages'].insert(0, {'role': 'system', 'content': SYSTEM})
            row['preparation_policy'] = 'shared-system-v01; three owner-authorized train corrections'
            row['serialization_status'] = 'semantic only; native reasoning, EOS and loss labels pending'
        (OUT / f'{split}.jsonl').write_text(
            ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows),
            encoding='utf-8', newline='\n')
    assert len(changes) == 3
    (OUT / 'corrections.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2) + '\n',
                                          encoding='utf-8', newline='\n')
    receipt = {'status': 'semantic-prepared-not-training-ready',
               'source_manifest_sha256': sha(SOURCE / 'manifest.json'),
               'builder_sha256': sha(Path(__file__)),
               'authorization': 'Owner approved three minimal corrections in conversation, 2026-11-16',
               'counts': {'train': 80, 'test': 20}, 'corrected_train_rows': 3,
               'test_reference_edits': 0, 'system': SYSTEM,
               'files': {name: sha(OUT / name) for name in ['train.jsonl', 'test.jsonl', 'corrections.json']}}
    (OUT / 'manifest.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='\n')
    print(json.dumps({'status': receipt['status'], 'counts': receipt['counts'], 'corrections': len(changes)}))


if __name__ == '__main__':
    main()
