"""Build the Turkish prompts for the answer-quality DPO data (experiment preference-rl exp-003).

  python tr_dpo_prompts.py build --out DIR

Two sources, both unseen by the exp-021 Turkish SFT model:
  atlas      Turkce Atlas prompts (MIT) of the SFT core pack whose answer exp-021 was NOT trained on (443 of 500)
  template   hand-written everyday prompts for the categories where exp-021 was weakest and Atlas has none
             (explain, email, rewrite, translate, creative, countable constraints)
Nothing here overlaps the 40 writing-probe prompts: exact duplicates and near duplicates are rejected (loud failure).
Needs the local SFT core files (experiments/turkish-capability/lfm3-1.7b/sft-core-v01/samples-local, pack-local), which are not in Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
TR = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
ATLAS_RENDER = TR / 'sft-core-v01/samples-local/prompts-render-en.jsonl'
EXP021_TRAIN = TR / 'sft-core-v01/pack-local/lfm3-exp021/train.jsonl'
PROBE = TR / 'eval-v2/writing-prompts-tr.jsonl'

EXPLAIN = [
    'Yerçekimi nedir? Bir ortaokul öğrencisine anlatır gibi açıkla.',
    'Depremler neden olur? Gündelik bir örnekle anlat.',
    'Bir ağaç sudan ve topraktan nasıl beslenir? Kısa ve anlaşılır yaz.',
    'Elektrik evimize nasıl ulaşır? Teknik terimleri en aza indirerek anlat.',
    'Vergi neden ödenir ve toplanan vergiler nerelere harcanır? Basit bir dille açıkla.',
    'Aşılar vücudu hastalıklara karşı nasıl korur? Teknik bilgisi olmayan birine anlat.',
    'Bir kitap bastırılırken hangi aşamalardan geçer? Adım adım anlat.',
    'Ay neden evre değiştirir? Dünya ile Güneş\'ten bahsederek açıkla.',
    'Kredi kartı ile banka kartı arasındaki fark nedir? Basit bir dille anlat.',
    'Şehirlerde trafik neden sıkışır? İki üç nedenle açıkla.',
    'Geri dönüşüm neden önemlidir? Bir örnek vererek anlat.',
    'Bir uçak havada nasıl durur? Çocuklara anlatır gibi açıkla.',
    'Bilgisayarda bellek (RAM) ile depolama alanı arasındaki fark nedir? Gündelik bir benzetmeyle anlat.',
    'Okyanuslarda gelgit neden olur? Kısa bir açıklama yaz.',
    'Sigorta nasıl çalışır? Bir örnekle açıkla.',
]
EMAIL = [
    'Apartman yöneticisine, çatıdan su sızdığını bildiren kibar ama net bir e-posta yaz.',
    'Kargo şirketine, üç gündür gelmeyen paketin durumunu soran bir e-posta yaz.',
    'Çocuğunun öğretmenine, yarın okula gelemeyeceğini bildiren kısa bir mesaj yaz.',
    'İş arkadaşına, perşembe günkü toplantıyı cumaya almayı öneren bir e-posta yaz.',
    'Bir kafeye, doğum günü için yirmi kişilik rezervasyon yapmak istediğini bildiren bir e-posta yaz.',
    'Kitap kulübü arkadaşlarına, bu ayki kitabın değiştiğini duyuran kısa bir mesaj yaz.',
    'İnternet servis sağlayıcısına, faturadaki hatalı tutarı bildiren ve düzeltme isteyen resmî bir e-posta yaz.',
    'Yeni işe başlayan bir çalışana, ilk gün için hoş geldin diyen sıcak bir e-posta yaz.',
    'Eski ev sahibine, depozitonun iade edilmesini rica eden kibar bir e-posta yaz.',
    'Staj başvurusu yaptığın şirkete, başvurunun durumunu soran kısa bir e-posta yaz.',
    'Takım arkadaşlarına, haftalık toplantı notlarını paylaşan kısa bir e-posta yaz.',
    'Bir etkinlik organizatörüne, katılımcı listesine adını eklemelerini isteyen kısa bir e-posta yaz.',
    'Mahalle sakinlerine, bahçe temizliği için cumartesi günü gönüllü aradığını duyuran bir mesaj yaz.',
    'Bir kurs eğitmenine, kaçırdığın dersin notlarını isteyen nazik bir e-posta yaz.',
]
REWRITE = [
    'Şu cümleyi daha resmî bir dille yeniden yaz: "Selam, dünkü sunumun dosyasını bana atar mısın, acil lazım."',
    'Şu cümleyi daha resmî bir dille yeniden yaz: "Arkadaşlar, yarınki gezi iptal oldu, haberiniz olsun."',
    'Şu cümleyi daha resmî bir dille yeniden yaz: "Bu fiyata alınmaz abi, biraz indirim yapsanız olur mu?"',
    'Şu cümleyi sade ve kısa hale getir: "Mevcut durumda gerçekleştirilmekte olan çalışmaların tamamlanması için ilave süreye ihtiyaç duyulmaktadır."',
    'Şu cümleyi sade ve kısa hale getir: "Söz konusu hizmetin sunumu esnasında yaşanan aksaklıklardan dolayı özür dileriz."',
    'Şu cümleyi sade ve kısa hale getir: "Başvuru sahiplerinin belgelerini eksiksiz biçimde ibraz etmeleri gerekmektedir."',
    'Şu cümledeki yazım ve anlatım hatalarını düzelt: "Hafta sonu ailemle birlikte denize gitdik ama hava çok soguktu yuzemedik."',
    'Şu cümledeki yazım ve anlatım hatalarını düzelt: "Yarın sabah erken kalkmam lazım çünkü toplantiya geç kalırsam müdür kızıcak."',
    'Şu cümledeki yazım ve anlatım hatalarını düzelt: "Kütüphaneden aldığım kitabı bugün iade etmeliyim yoksa ceza ödiyeceğim."',
    'Şu paragrafı daha akıcı hale getir: "Sabah uyandım. Kahvaltı yaptım. Okula gittim. Okulda arkadaşlarımı gördüm. Ders başladı."',
    'Şu paragrafı daha akıcı hale getir: "Akşam oldu. Hava karardı. Sokak lambaları yandı. Biz eve döndük. Eve girdik."',
    'Şu cümleyi daha samimi bir dille yeniden yaz: "Toplantıya katılımınız rica olunur."',
    'Şu cümleyi anlamını koruyarak kısalt: "Bugün hava durumunun yağışlı olması nedeniyle açık hava etkinliğinin ertelenmesine karar verilmiştir."',
    'Şu cümleyi daha resmî bir dille yeniden yaz: "Hocam yarın sınava giremeyeceğim, rapor aldım."',
]
TRANSLATE = [
    'Please send me the updated report by the end of the day.',
    'The new library opens next Monday and will stay open until midnight.',
    "I would like to book a table for four people at eight o'clock.",
    'Our flight was delayed by two hours because of heavy snow.',
    'The company has decided to extend the free trial period to thirty days.',
    'Could you tell me how to get to the nearest train station?',
    'She has been learning to play the piano since she was six years old.',
    'The doctor advised him to drink more water and sleep at least seven hours.',
    'We apologize for the inconvenience and will fix the problem as soon as possible.',
    'Many students prefer studying in the library because it is quiet.',
    'The festival will take place in the city park, and entry is free for children.',
    'If the package does not arrive by Friday, please contact our support team.',
    'He forgot his umbrella at the office, so he got completely wet on the way home.',
    'Learning a second language can improve memory and open new career opportunities.',
]
TRANSLATE_FORMS = ['Şu cümleyi Türkçeye çevir: "{}"', 'Aşağıdaki cümleyi doğal bir Türkçeyle çevir: "{}"',
                   'Bu İngilizce cümlenin Türkçesini yaz: "{}"']
CREATIVE = [
    'Sonbaharda bir parkı anlatan, dört cümlelik kısa bir paragraf yaz.',
    'Bir fırıncının sabah işe başlayışını anlatan, üç cümlelik kısa bir hikâye yaz.',
    'Deniz kenarında bir akşamı anlatan dört dizelik bir şiir yaz.',
    'Yeni açılan bir çiçekçi için iki cümlelik, akılda kalıcı bir tanıtım yazısı yaz.',
    'İlk kez kar gören bir çocuğun heyecanını anlatan kısa bir paragraf yaz.',
    'Bir köpeğin sahibini beklediği bir günü anlatan üç cümlelik kısa bir hikâye yaz.',
    'Kütüphanede geçen sessiz bir öğleden sonrayı anlatan beş cümlelik bir paragraf yaz.',
    'Ankara\'da bir kış sabahını anlatan kısa bir şiir yaz.',
    'Yeni açılan bir spor salonu için tek cümlelik bir slogan yaz.',
    'Bir mahalle bakkalının müşterileriyle sohbetini anlatan kısa bir paragraf yaz.',
    'Dağ yürüyüşünün sonunda zirveye ulaşan birini anlatan üç cümle yaz.',
    'Yağmurdan sonra çıkan gökkuşağını anlatan dört dizelik bir şiir yaz.',
]
# (prompt, check spec in the format of the writing probe: max_words, exact_sentences, bullets, must_include)
CONSTRAINT = [
    ('Uyku düzeni için tam dört öneriyi madde işaretleriyle yaz.', dict(bullets=4)),
    ('İzmir hakkında tam iki cümle yaz.', dict(exact_sentences=2)),
    ('İçinde "sabır" kelimesi geçen, üç cümlelik kısa bir nasihat metni yaz.', dict(exact_sentences=3, must_include=['sabır'])),
    ('Bursa\'yı ziyaret edecek biri için en fazla kırk kelimelik bir tavsiye yaz.', dict(max_words=40)),
    ('Bir öğrencinin ders çalışma planı için beş maddelik bir liste öner.', dict(bullets=5)),
    ('Spor yapmanın faydalarını en fazla otuz kelimeyle anlat.', dict(max_words=30)),
    ('Kitap okuma alışkanlığı kazanmak için üç öneriyi madde işaretleriyle yaz.', dict(bullets=3)),
    ('Antalya hakkında tam üç cümle yaz.', dict(exact_sentences=3)),
    ('İçinde "umut" kelimesi geçen tek cümlelik bir dilek yaz.', dict(exact_sentences=1, must_include=['umut'])),
    ('Evde enerji tasarrufu için en fazla elli kelimelik bir paragraf yaz.', dict(max_words=50)),
    ('Yeni bir hobi edinmenin avantajlarını tam dört madde olarak sırala.', dict(bullets=4)),
    ('Mutlu bir gün için iki cümlelik bir dilek yaz.', dict(exact_sentences=2)),
    ('Kahvaltının önemini en fazla kırk beş kelimeyle açıkla.', dict(max_words=45)),
    ('Trabzon hakkında tam dört cümle yaz.', dict(exact_sentences=4)),
]


def read_jsonl(path):
    """One JSON row per newline (str.splitlines would also split on U+2028 inside strings)."""
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def norm(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^\wçğıöşüÇĞİÖŞÜ ]', ' ', text.lower().replace('İ', 'i').replace('I', 'ı'))).strip()


def shingles(text, n=4):
    words = norm(text).split()
    return {' '.join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))}


def jaccard(a, b):
    return len(a & b) / max(1, len(a | b))


def template_rows():
    rows = []
    for kind, items in (('explain', EXPLAIN), ('email', EMAIL), ('rewrite', REWRITE), ('creative', CREATIVE)):
        rows += [dict(kind=kind, prompt=p, check=None) for p in items]
    rows += [dict(kind='translate', prompt=TRANSLATE_FORMS[i % 3].format(s), check=None) for i, s in enumerate(TRANSLATE)]
    rows += [dict(kind='constraint', prompt=p, check=spec) for p, spec in CONSTRAINT]
    for i, row in enumerate(rows):
        row.update(id=f'dpo-tpl-{i:03d}', source='template')
    return rows


def atlas_rows():
    trained = {r['core_id'] for r in read_jsonl(EXP021_TRAIN) if r['category'] == 'tr_general'}
    rows = []
    for row in read_jsonl(ATLAS_RENDER):
        if row['category'] != 'tr_general' or row['core_id'] in trained:
            continue
        assert len(row['messages']) == 1 and row['messages'][0]['role'] == 'user', row['id']
        prompt = row['messages'][0]['content']
        check = row['check'] if row['check'] and row['check'].get('items') else None
        kind = 'atlas_constraint' if check else ('atlas_context' if len(prompt) > 500 else 'atlas_plain')
        rows.append(dict(id='dpo-' + row['core_id'], source='atlas', kind=kind, prompt=prompt, check=check,
                         atlas_core_id=row['core_id']))
    return rows, len(trained)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', choices=['build'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--near-duplicate', type=float, default=0.7, help='4-gram Jaccard above which a prompt counts as a probe duplicate (same style suffix is expected, same topic is not)')
    args = parser.parse_args()

    probe = read_jsonl(PROBE)
    probe_norm = {norm(p['prompt']) for p in probe}
    probe_sh = [(p['id'], shingles(p['prompt'])) for p in probe]
    atlas, trained = atlas_rows()
    rows = template_rows() + atlas
    assert len({r['prompt'] for r in rows}) == len(rows), 'duplicate prompts'
    worst = (0.0, None, None)
    for row in rows:
        if norm(row['prompt']) in probe_norm:
            sys.exit(f"{row['id']} equals a writing-probe prompt")
        sh = shingles(row['prompt'])
        for pid, psh in probe_sh:
            score = jaccard(sh, psh)
            if score > worst[0]:
                worst = (score, row['id'], pid)
            if score > args.near_duplicate:
                sys.exit(f"{row['id']} is a near duplicate of probe prompt {pid} (Jaccard {score:.2f})")
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / 'prompts-tr-dpo.jsonl'
    text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    path.write_text(text, encoding='utf-8', newline='\n')
    kinds = {}
    for r in rows:
        kinds[r['kind']] = kinds.get(r['kind'], 0) + 1
    manifest = dict(rows=len(rows), by_kind=kinds, atlas_unseen=len(atlas), atlas_trained_excluded=trained,
                    probe_prompts_checked=len(probe), max_probe_overlap=dict(jaccard=round(worst[0], 3), prompt=worst[1], probe=worst[2]),
                    sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
    (args.out / 'prompts-tr-dpo.manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
