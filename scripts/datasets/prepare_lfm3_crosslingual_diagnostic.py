"""Freeze a tiny matched language-transfer diagnostic; never training data."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE / 'crosslingual-holdout-v01'
CASES = [
    dict(case='purchase', task='arithmetic',
         en='You have 150 lira. You buy three notebooks costing 18 lira each, then spend half of the remaining money on a bag. How many lira do you have left? Give a brief calculation and the result.',
         tr='150 liran var. Tanesi 18 lira olan üç defter alıyorsun, ardından kalan paranın yarısını bir çantaya harcıyorsun. Kaç liran kalır? Kısa bir hesaplama ve sonucu yaz.',
         target_en='The notebooks cost 3 × 18 = 54 lira. After buying them, 150 − 54 = 96 lira remains; spending half leaves 48 lira.',
         target_tr='Defterler 3 × 18 = 54 lira tutar. Geriye 150 − 54 = 96 lira kalır; bunun yarısı harcanınca 48 lira kalır.',
         rubric='Final amount 48 lira; intermediate amounts 54 and 96 if shown. No contradictory arithmetic. Equivalent correct working accepted.'),
    dict(case='repair', task='grounding',
         en='Repair note: "The screen was replaced on Monday. The speaker was tested on Tuesday and was working. The battery has not yet been checked." Based only on this note, can we conclude that the battery needs replacing? Answer in at most two sentences and explain why.',
         tr='Onarım notu: "Pazartesi ekran değiştirildi. Salı hoparlör denendi ve çalıştığı görüldü. Pil henüz kontrol edilmedi." Yalnızca bu nota dayanarak pilin değiştirilmesi gerektiği sonucuna varabilir miyiz? En fazla iki cümleyle yanıtla ve nedenini belirt.',
         target_en='No. The battery has not been checked, so the note does not establish whether it needs replacing.',
         target_tr='Hayır. Pil henüz kontrol edilmediği için değiştirilmesinin gerekip gerekmediği bu nottan anlaşılamaz.',
         rubric='Distinguish unknown battery condition from known good/bad. No invented fault or replacement decision. At most two sentences.'),
    dict(case='delivery', task='faithful_generation',
         en='Express these notes as one natural sentence without adding information: "The parcel arrived today, not yesterday. The recipient was away. The parcel was left with the building caretaker."',
         tr='Şu notları bilgi eklemeden tek ve doğal bir cümleyle ifade et: "Paket dün değil, bugün geldi. Alıcı evde yoktu. Paket apartman görevlisine bırakıldı."',
         target_en='The parcel arrived today rather than yesterday and was left with the building caretaker because the recipient was away.',
         target_tr='Dün değil bugün gelen paket, alıcı evde olmadığı için apartman görevlisine bırakıldı.',
         rubric='One natural sentence retaining today-not-yesterday, absent recipient and caretaker as recipient of parcel. No changed roles, added date or invented detail. Linking absence to handover accepted; merely joining the facts also accepted.'),
]


def normalized(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def freeze(path, data):
    if path.exists():
        assert path.read_bytes() == data, f'Frozen artifact differs: {path}'
    else:
        path.write_bytes(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for src, dst in [('en', 'en'), ('tr', 'en'), ('en', 'tr'), ('tr', 'tr')]:
        instruction = ({'en': 'Answer in English.', 'tr': 'Answer in Turkish.'} if src == 'en'
                       else {'en': 'İngilizce yanıt ver.', 'tr': 'Türkçe yanıt ver.'})[dst]
        for case in CASES:
            rows.append(dict(id=f'xling-v01-{src}-{dst}-{case["case"]}',
                semantic_id=case['case'], task=case['task'], input_language=src,
                output_language=dst, messages=[dict(role='user', content=case[src] + '\n' + instruction)],
                target=case['target_' + dst], rubric=case['rubric'], evaluation_only=True,
                provenance='Independently agent-authored 2026-11-17; no dataset extraction'))
    # Distinct symbolic controls; not additional language conditions.
    controls = [dict(id=f'xling-v01-symbolic-{i}', semantic_id=f'symbolic-{i}',
        task='symbolic_arithmetic', input_language='symbolic', output_language='numeric',
        messages=[dict(role='user', content=f'{expr} = ?\nOutput only the number. / Yalnızca sayıyı yaz.')],
        target=str(answer), rubric='Exact numeric value; score numeric correctness separately from extra text.',
        evaluation_only=True, provenance='Agent-authored symbolic control; 2026-11-17')
        for i, (expr, answer) in enumerate([('176 - 8 * 9', 176 - 8 * 9),
                                           ('(63 + 27) / 6', (63 + 27) // 6),
                                           ('125 * 4 + 75', 125 * 4 + 75)], 1)]
    protected = []
    sources = [BASE / 'sft-pilot160-v01' / f'{s}.jsonl' for s in ['train', 'test']]
    sources += [BASE / 'sft160-dev-v01/questions.jsonl']
    for path in sources:
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            protected.extend(m['content'] for m in row['messages'] if m['role'] == 'user')
    assert len(rows) == len({r['id'] for r in rows}) == 12
    for row in rows + controls:
        assert normalized(row['messages'][0]['content']) not in {normalized(p) for p in protected}
    files = {}
    for name, items in [('questions.jsonl', rows), ('symbolic-controls.jsonl', controls)]:
        data = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in items).encode('utf-8')
        freeze(OUT / name, data)
        files[name] = dict(rows=len(items), sha256=hashlib.sha256(data).hexdigest())
    manifest = dict(status='frozen-before-inference', files=files, underlying_matched_cases=3,
        conditions=['en-en', 'tr-en', 'en-tr', 'tr-tr'], training_allowed=False,
        reference_policy='Illustrative wording; accept semantically equivalent correct answers.',
        overlap_check='Normalized exact user-prompt exclusion against train160, old20 and dev20 passed. No formal semantic/translation independence guarantee.',
        protected_files_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        limitations='Tiny diagnostic, not a broad benchmark. Only three independent matched cases, not twelve independent tasks. Reuse for training decisions makes this development data; fresh final test required.')
    freeze(OUT / 'manifest.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
