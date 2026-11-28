"""Programmatic Turkish prompts with 2-4 stacked countable constraints (preference-rl exp-006).

  python tr_dpo6_prompts.py build --out DIR --topics topics.jsonl --passages passages.jsonl --kiraz train.jsonl \
      [--per-split train=5000,dev=300,heldout=700] [--mix topic=0.6,question=0.25,passage=0.15] [--seed 20261127]

A task plus 2-4 constraints that tr_dpo6_checks can verify. Three sources: `topic` (a task template on a topic from the built-in list plus the
AI-written topics file), `question` (an explain-type question from the Turkish-CoT-Instruct-Dataset, questions only, never its answers),
`passage` (a task over an AI-written source passage, grounded: the invented-number check is on). Every source is split by a hash of its
topic / question / passage, so none appears in two splits. Contradictory stacks are never built (see `compatible`).
Output rows: id, source, kind, split, topic, prompt, check={'items': [...]}, grounded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re

TASKS = [
    '{t} hakkında kısa bir bilgi metni yaz.',
    '{t} konusunu bir arkadaşına anlatır gibi açıkla.',
    '{t} üzerine bir öğrencinin okuyacağı kısa bir yazı hazırla.',
    '{t} hakkında bir mahalle bülteni için kısa bir duyuru yaz.',
    '{t} ile ilgili okuyucuya fayda sağlayacak öneriler sun.',
    '{t} konusunda bir dergi köşesi için kısa bir yazı kaleme al.',
]
# (topic phrase, keyword that fits the topic)
TOPICS = [
    ('sabah yürüyüşü', 'yürüyüş'), ('evde geri dönüşüm', 'geri dönüşüm'), ('küçük bir fırın', 'fırın'), ('yüzme öğrenmek', 'yüzme'),
    ('yağmurlu bir gün', 'yağmur'), ('öğrenciyken para biriktirmek', 'para'), ('trenle seyahat', 'tren'), ('günlük tutmak', 'günlük'),
    ('mahalle kütüphanesi', 'kütüphane'), ('arkadaşlara akşam yemeği hazırlamak', 'yemek'), ('dağ köyünde yaşam', 'köy'),
    ('uykunun önemi', 'uyku'), ('bisikletle şehir turu', 'bisiklet'), ('balkonda sebze yetiştirmek', 'sebze'),
    ('ilk kez ev taşımak', 'taşınma'), ('kitap okuma alışkanlığı', 'kitap'), ('sağlıklı kahvaltı', 'kahvaltı'),
    ('çocuklarla müzeye gitmek', 'müze'), ('yeni bir dil öğrenmek', 'dil'), ('telefon kullanımını azaltmak', 'telefon'),
    ('deprem öncesi hazırlık', 'deprem'), ('su tasarrufu', 'su'), ('enerji tasarrufu', 'enerji'), ('kamp yapmak', 'kamp'),
    ('sokak hayvanlarına yardım', 'hayvan'), ('ders çalışma planı', 'plan'), ('iş görüşmesine hazırlanmak', 'görüşme'),
    ('evde ofis düzeni', 'ofis'), ('fotoğraf çekmek', 'fotoğraf'), ('satranç öğrenmek', 'satranç'), ('bahçe bakımı', 'bahçe'),
    ('ilk yardım temelleri', 'ilk yardım'), ('toplu taşıma kullanmak', 'toplu taşıma'), ('semt pazarı alışverişi', 'pazar'),
    ('kış aylarında evi ısıtmak', 'kış'), ('yaz tatili planlamak', 'tatil'), ('komşuluk ilişkileri', 'komşu'),
    ('öğle yemeği hazırlamak', 'öğle'), ('çay demlemek', 'çay'), ('ekmek yapmak', 'ekmek'), ('Türk kahvesi', 'kahve'),
    ('ağaç dikmek', 'ağaç'), ('güneş enerjisi', 'güneş'), ('e-posta yazma adabı', 'e-posta'), ('zaman yönetimi', 'zaman'),
    ('stresle başa çıkmak', 'stres'), ('düzenli egzersiz', 'egzersiz'), ('el yapımı hediye', 'hediye'), ('ev bütçesi', 'bütçe'),
    ('ikinci el eşya alışverişi', 'ikinci el'), ('çocuklara masal okumak', 'masal'), ('doğada kuş gözlemi', 'kuş'),
    ('bilgisayar güvenliği', 'şifre'), ('sosyal medya molası', 'sosyal medya'), ('okulda arkadaşlık', 'arkadaş'),
    ('yeni bir hobi edinmek', 'hobi'), ('elektrikli araçlar', 'elektrikli'), ('akıllı saat kullanımı', 'saat'),
    ('mutfakta gıda israfı', 'israf'), ('uzun yolculukta araba bakımı', 'araba'), ('kütüphaneden ödünç kitap almak', 'ödünç'),
    ('hava durumuna göre giyinmek', 'giyim'), ('gönüllü olarak çalışmak', 'gönüllü'), ('yerel festivaller', 'festival'),
    ('el sanatları atölyesi', 'atölye'), ('şehirde sessiz bir köşe bulmak', 'sessiz'), ('yaşlı komşuya yardım', 'yardım'),
    ('okulda öğle arası', 'okul'), ('akşam yürüyüşü', 'akşam'), ('çiçek bakımı', 'çiçek'), ('sebze çorbası', 'çorba'),
    ('müzik dinlemek', 'müzik'), ('resim yapmaya başlamak', 'resim'), ('gitar çalmak', 'gitar'), ('yeni bir şehre alışmak', 'şehir'),
    ('sınav haftası', 'sınav'), ('hafta sonu temizliği', 'temizlik'), ('doğum günü hazırlığı', 'doğum günü'),
    ('nehir kenarında piknik', 'piknik'), ('bilgi yarışması', 'yarışma'), ('trafikte güvenlik', 'trafik'),
    ('mahalle spor sahası', 'spor'), ('ev yapımı reçel', 'reçel'), ('kış lastiği', 'lastik'), ('kitap kulübü', 'kulüp'),
    ('sinemaya gitmek', 'sinema'), ('tiyatro izlemek', 'tiyatro'), ('deniz kıyısında yaşam', 'deniz'), ('dağa tırmanmak', 'dağ'),
    ('balık tutmak', 'balık'), ('kuru gıda saklamak', 'gıda'), ('bilimle ilgili belgesel izlemek', 'belgesel'),
    ('astronomi ve yıldızlar', 'yıldız'), ('Ay tutulması', 'tutulma'), ('depremde güvenli toplanma alanı', 'toplanma'),
    ('çocuk bisikleti seçimi', 'çocuk'), ('hayvan barınağında gönüllülük', 'barınak'), ('okul bahçesinde bostan', 'bostan'),
    ('köy okulu', 'öğretmen'), ('internetten alışveriş', 'alışveriş'), ('çevrimiçi dersler', 'ders'), ('ev içinde bitki yetiştirmek', 'bitki'),
    ('acil durum çantası', 'çanta'), ('eski eşyaları yenilemek', 'eşya'), ('mevsim meyveleri', 'meyve'), ('havadaki kirlilik', 'hava'),
    ('trafik ışıkları', 'ışık'), ('yürüyüş ayakkabısı seçmek', 'ayakkabı'), ('yeni başlayanlar için koşu', 'koşu'),
    ('ev arkadaşıyla yaşamak', 'ev'), ('toplantıda not tutmak', 'toplantı'), ('sunum hazırlamak', 'sunum'), ('basit bir tarif', 'tarif'),
    ('atık pil toplama', 'pil'), ('mahalle sakinleri toplantısı', 'toplantı'), ('çocuklar için oyun saati', 'oyun'),
    ('ilk maaşı harcamak', 'maaş'), ('kış güneşi', 'güneş'), ('kar yağışında yolculuk', 'kar'), ('evde yangın güvenliği', 'yangın'),
    ('uzun bir kitabı bitirmek', 'kitap'), ('küçük bir şehirde bisiklet yolu', 'yol'), ('yeni bir iş başlangıcı', 'iş'),
    ('kısa bir mola vermek', 'mola'), ('okul servis saati', 'servis'), ('mahallede nöbetçi eczane', 'eczane'),
]
FORBIDDEN = ['çok', 'önemli', 'genellikle', 'aslında', 'güzel', 'kolay', 'bazı', 'özellikle']


def constraint_pool(rng, topic_keyword):
    """All constraints one prompt may draw from: (group, item, instruction text)."""
    max_n = rng.choice([40, 60, 80, 100, 120])
    min_n = rng.choice([25, 35, 50])
    bullets = rng.choice([3, 4, 5])
    exact = rng.choice([2, 3, 4])
    max_s = rng.choice([3, 4, 5])
    forbidden = rng.choice(FORBIDDEN)
    return [
        ('max_words', dict(type='max_words', n=max_n), f'En fazla {max_n} kelime kullan.'),
        ('min_words', dict(type='min_words', n=min_n), f'En az {min_n} kelime yaz.'),
        ('structure', dict(type='bullets', n=bullets), f'Yanıtı tam olarak {bullets} maddelik bir liste olarak ver.'),
        ('structure', dict(type='exact_sentences', n=exact), f'Yanıtın tam olarak {exact} cümle olsun.'),
        ('structure', dict(type='max_sentences', n=max_s), f'En fazla {max_s} cümle kullan.'),
        ('include', dict(type='must_include', word=topic_keyword), f'Yanıtta "{topic_keyword}" kelimesi geçsin.'),
        ('forbid', dict(type='must_not_include', word=forbidden), f'"{forbidden}" kelimesini kullanma.'),
        ('greeting', dict(type='no_greeting'), 'Selamlama ya da giriş cümlesi yazma.'),
        ('question', dict(type='no_closing_question'), 'Yanıtı bir soruyla bitirme.'),
    ]


def compatible(items):
    """No contradictory or unsatisfiable stacks: one length bound each, at most one structure rule, room for the content."""
    by = {}
    for item in items:
        by.setdefault(item['type'], []).append(item)
    structure = [i for i in items if i['type'] in ('bullets', 'exact_sentences', 'max_sentences')]
    if len(structure) > 1:
        return False
    max_w = by.get('max_words', [{}])[0].get('n')
    min_w = by.get('min_words', [{}])[0].get('n')
    if max_w and min_w and max_w < min_w + 20:
        return False
    if max_w and by.get('bullets') and max_w < 12 * by['bullets'][0]['n']:
        return False
    if min_w and by.get('exact_sentences') and min_w > 25 * by['exact_sentences'][0]['n']:
        return False
    if min_w and by.get('max_sentences') and min_w > 25 * by['max_sentences'][0]['n']:
        return False
    return True


PASSAGE_TASKS = ['Metni özetle.', 'Metindeki bilgileri düzenli biçimde aktar.', 'Metne dayanarak okuyucuya kısa bir not hazırla.',
                 'Metnin ana bilgilerini bir arkadaşına anlatır gibi yaz.']
KIRAZ_REVISION = '3473e6c6350564d5a7000faf3ff140e9c4b9d1f2'


def hash_split(key):
    bucket = int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16) % 100
    return 'heldout' if bucket < 15 else 'dev' if bucket < 25 else 'train'


def read_jsonl(path):
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def is_explain_question(text):
    """Explain-type questions only: no multiple choice, code or calculation (the checks cannot tell a right answer from a wrong one)."""
    low = text.lower()
    if re.search(r'^\s*[A-E]\)', text, re.M) or '```' in text or 'python' in low:
        return False
    if re.search(r'hesapla|bulunuz|kaç\b|kaçtır|değeri|toplam|oran|yüzde|\d+\s*[x×*/+=]\s*\d+', low):
        return False
    return bool(re.search(r'açıkla|neden|nasıl|tartış|değerlendir|yorumla|karşılaştır|anlat', low)) and len(text.split()) <= 120


def load_sources(topics_path, passages_path, kiraz_path):
    topics = list(TOPICS)
    if topics_path:
        have = {t[0].lower() for t in topics}
        topics += [(r['topic'], r['keyword']) for r in read_jsonl(topics_path) if r['topic'].lower() not in have]
    passages = [(r['id'], r['text']) for r in read_jsonl(passages_path)] if passages_path else []
    questions = []
    if kiraz_path:
        for r in read_jsonl(kiraz_path):
            user = [m['content'] for m in r['messages'] if m['role'] == 'user'][0].strip()
            if is_explain_question(user):
                questions.append(user)
    return topics, passages, sorted(set(questions))


def stack(rng, pool, lo=2, hi=4):
    """2-4 constraints from different groups that do not contradict each other, or None."""
    chosen = rng.sample(pool, rng.choice(range(lo, hi + 1)))
    if len({g for g, _, _ in chosen}) < len(chosen) or not compatible([i for _, i, _ in chosen]):
        return None
    return chosen


def build_rows(per_split, mix, seed, topics, passages, questions):
    rng = random.Random(seed)
    rows, seen, counters = [], set(), {}
    for split, want in per_split.items():
        pools = dict(topic=[t for t in topics if hash_split(t[0]) == split],
                     question=[q for q in questions if hash_split(q) == split],
                     passage=[p for p in passages if hash_split(p[0]) == split])
        weights = {k: w for k, w in mix.items() if pools[k]}
        assert weights, f'no material in split {split}'
        made, attempts = 0, 0
        while made < want:
            attempts += 1
            assert attempts < want * 400, f'cannot make {want} unique prompts in {split} ({ {k: len(v) for k, v in pools.items()} })'
            kind = rng.choices(list(weights), list(weights.values()))[0]
            if kind == 'topic':
                topic, keyword = rng.choice(pools['topic'])
                head = rng.choice(TASKS).format(t=topic[0].upper() + topic[1:])
                pool, ref, grounded = constraint_pool(rng, keyword), topic, False
            elif kind == 'question':
                ref = rng.choice(pools['question'])
                head, grounded = ref, False
                pool = [c for c in constraint_pool(rng, 'x') if c[0] != 'include']
            else:
                pid, text = rng.choice(pools['passage'])
                head = 'Aşağıdaki metne dayanarak görevi yap. Metinde olmayan bilgi ekleme.\n\nMetin: ' + text + '\n\nGörev: ' + rng.choice(PASSAGE_TASKS)
                ref, grounded = pid, True
                pool = [c for c in constraint_pool(rng, 'x') if c[0] != 'include']
            chosen = stack(rng, pool)
            if chosen is None:
                continue
            prompt = head + ' ' + ' '.join(text for _, _, text in chosen)
            if prompt in seen:
                continue
            seen.add(prompt)
            made += 1
            counters[(split, kind)] = counters.get((split, kind), 0) + 1
            rows.append(dict(id=f'dpo6-{split}-{made:05d}', source=kind, kind='dpo6_constraint', split=split,
                             topic=ref[:80], prompt=prompt, check=dict(items=[i for _, i, _ in chosen]), grounded=grounded))
    return rows, counters


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['build'])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--topics', type=Path)
    ap.add_argument('--passages', type=Path)
    ap.add_argument('--kiraz', type=Path, help='train.jsonl of AlicanKiraz0/Turkish-CoT-Instruct-Dataset at the pinned revision')
    ap.add_argument('--per-split', default='train=5000,dev=300,heldout=700')
    ap.add_argument('--mix', default='topic=0.6,question=0.25,passage=0.15')
    ap.add_argument('--seed', type=int, default=20261127)
    args = ap.parse_args()
    per_split = {k: int(v) for k, v in (p.split('=') for p in args.per_split.split(','))}
    mix = {k: float(v) for k, v in (p.split('=') for p in args.mix.split(','))}
    topics, passages, questions = load_sources(args.topics, args.passages, args.kiraz)
    rows, counters = build_rows(per_split, mix, args.seed, topics, passages, questions)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / 'prompts-dpo6.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8', newline='\n')

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest() if p else None
    by_split = lambda items, key: {s: sum(hash_split(key(i)) == s for i in items) for s in per_split}  # noqa: E731
    manifest = dict(rows=len(rows), per_split=per_split, mix=mix, seed=args.seed,
                    rows_by_split_and_source={f'{s}/{k}': n for (s, k), n in sorted(counters.items())},
                    material=dict(topics=len(topics), topics_by_split=by_split(topics, lambda t: t[0]),
                                  passages=len(passages), passages_by_split=by_split(passages, lambda p: p[0]),
                                  questions=len(questions), questions_by_split=by_split(questions, lambda q: q)),
                    inputs=dict(topics_sha256=sha(args.topics), passages_sha256=sha(args.passages), kiraz_sha256=sha(args.kiraz),
                                kiraz_revision=KIRAZ_REVISION),
                    prompts_sha256=sha(path), script_sha256=sha(Path(__file__)),
                    constraint_types={t: sum(i['type'] == t for r in rows for i in r['check']['items'])
                                      for t in sorted({i['type'] for r in rows for i in r['check']['items']})})
    (args.out / 'prompts-dpo6.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
