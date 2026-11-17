"""Freeze independent authored evaluation prompts; no source-dataset extraction."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE / 'sft160-dev-v01'
# These examples were authored for evaluation, not taken from the old holdout.
ITEMS = [
 ('editing', 'Yalnızca yazım ve noktalama hatalarını düzelt, kelimeleri değiştirme: "Yarin ogleden sonra kutuphaneye gidecegim ancak kartimi evde unuttum."', 'Yarın öğleden sonra kütüphaneye gideceğim ancak kartımı evde unuttum.', 'Preserve every word and tense; restore Turkish characters; no commentary.'),
 ('editing', 'Şu cümleyi anlamını koruyarak doğal bir Türkçeyle yeniden yaz: "Deneyin bir daha yapılması sonrasında ölçümün yanlış olmasının olmadığı görüldü."', 'Deney tekrarlandığında ölçümün yanlış olmadığı görüldü.', 'State that repeat experiment found no measurement error; do not claim experiment failure or change negation.'),
 ('editing', 'Aşağıdaki iki cümleyi, olay sırasını ve anlamı değiştirmeden tek cümlede birleştir: "Sensörün pili değiştirildi. Ardından kayıt yeniden başlatıldı."', 'Sensörün pili değiştirildikten sonra kayıt yeniden başlatıldı.', 'Battery first, recording second; one natural sentence; no invented reason.'),
 ('editing', 'Cümleyi daha açık yaz, belirsiz kişinin kim olduğunu tahmin etme: "Ece, Duru’ya onun çizimini beğendiğini söyledi."', 'Ece, Duru’ya bir çizimi beğendiğini söyledi; ancak çizimin Ece’ye mi yoksa Duru’ya mı ait olduğu belirtilmiyor.', 'Expose ownership ambiguity; do not silently choose whose drawing.'),
 ('grounding', 'Yalnızca notlara dayanarak bir cümleyle özetle: "Kayıtlar çarşamba açılacak. Kontenjan 18 kişi. Etkinliğin yapılacağı salon henüz seçilmedi."', 'Kayıtları çarşamba açılacak etkinliğin kontenjanı 18 kişi; salonu henüz belirlenmedi.', 'Include all three facts; no invented date, room or event type.'),
 ('grounding', 'Not: "Fırın 14.10’da kapatıldı. Fan 14.18’e kadar çalıştı. Kapak 14.25’te açıldı." Fan durduktan kaç dakika sonra kapak açıldı? Yalnızca sonucu yaz.', '7 dakika', 'Exactly7 minutes; no external facts.'),
 ('grounding', 'Elimde bir sözleşme var. Bunu imzalamam mantıklı mı? Metni veya koşulları henüz paylaşmadım. Kısa yanıt ver.', 'Sözleşmenin metnini ve sizin için önemli koşulları paylaşır mısınız? Bunları görmeden imzalamanın uygun olup olmadığını değerlendiremem.', 'Ask for contract/terms; do not invent clauses or recommend signing without seeing it.'),
 ('grounding', 'Metin: "Otobüs geç geldi. Aynı sabah yoğun sis vardı." Otobüsün kesinlikle sis nedeniyle geciktiği sonucuna ulaşabilir miyiz? En fazla iki cümle yaz.', 'Hayır. Aynı anda sis olması, gecikmenin kesin nedeninin sis olduğunu kanıtlamaz.', 'Distinguish co-occurrence from proof of cause; no invented traffic report.'),
 ('constraints', 'Yalnızca geçerli JSON yaz. Şema: {"urun": string, "adet": integer, "teslim": boolean}. Bilgiler: ürün defter, adet 7, teslim edilmedi.', '{"urun":"defter","adet":7,"teslim":false}', 'Parseable JSON, exactly three specified keys, correct types and values; no code fence.'),
 ('constraints', 'Her satıra bir kelime yazarak şu kelimeleri Türk alfabesine göre sırala: üzüm, çilek, ayva, incir. Başlık ekleme.', 'ayva\nçilek\nincir\nüzüm', 'Four lines, exact order; no bullets or header.'),
 ('constraints', 'Yalnızca iki madde yaz. Her madde "- " ile başlasın ve en fazla beş kelime içersin. Konu: bilgisayar dosyalarını düzenlemek.', '- Dosyaları konularına göre klasörle.\n- Klasörlere anlaşılır adlar ver.', 'Exactly two bullet lines, maximum five words each, relevant and natural.'),
 ('constraints', 'Metinden sadece kişi adını ve saat bilgisini çıkar; "Ad | Saat" biçiminde tek satır yaz: "Mert dosyayı cuma günü saat 16.45’te teslim edecek."', 'Mert | 16.45', 'Exact extraction format; no weekday or additional words.'),
 ('reasoning', 'Bir atölyede 36 ürünün dörtte biri kusurlu. Sağlam ürünlerin üçte biri satılıyor. Geriye kaç sağlam ürün kalır? Kısa çözüm ve sonuç yaz.', '36 ürünün 9’u kusurlu, 27’si sağlamdır. Sağlamların 9’u satılınca 18 sağlam ürün kalır.', '9 defective,27 sound,9 sold,18 remaining; do not subtract one third of all36.'),
 ('reasoning', 'Bir depodaki 84 litrelik sıvı, hacimleri 3:4 oranında olan iki kaba tamamen paylaştırılıyor. Büyük kapta kaç litre olur?', '48 litre. Toplam 7 pay vardır; bir pay 84 / 7 = 12 litre, büyük kap 4 × 12 = 48 litredir.', 'Larger container48 litres; ratio correct.'),
 ('reasoning', 'Dört koşucu var: Bora, Cem’den önce; Deniz, Bora’dan sonra; Ada, Deniz’den sonra bitiriyor. Cem ile Deniz’in sırası kesin olarak bilinir mi? Gerekçelendir.', 'Hayır. Cem de Deniz de Bora’dan sonra olabilir; birbirlerine göre sıralarını belirleyen bir bilgi verilmemiştir. Örneğin Bora-Cem-Deniz-Ada ve Bora-Deniz-Cem-Ada sıralamaları koşullara uyar.', 'Do not infer total order from partial constraints; any counterexamples must satisfy every relation.'),
 ('reasoning', 'Bir kutu 18 kilogram taşıyabiliyor. Aynı kutuya 5 kilogramlık bir cihaz ve her biri 2 kilogram olan paketlerden en fazla kaç tane konabilir?', '6 paket. Cihazdan sonra 13 kilogram kapasite kalır; 6 paketle toplam 17 kilogram olur, 7 paketle 19 kilogram sınırı aşar.', 'Floor((18-5)/2)=6; distinguish remaining1kg.'),
 ('language', '"Bu konuda henüz kesin bir sonuca ulaşamadık." cümlesini, anlamını koruyarak müşteriye gönderilecek doğal ve nazik bir cümleye dönüştür. Sonuç veya tarih uydurma.', 'Bu konuda henüz kesin bir sonuca ulaşamadık.', 'Polite natural Turkish; preserve uncertainty; no fabricated deadline or completed investigation.'),
 ('language', 'Bir arkadaşın emek verdiği sunumu yetiştiremediğini söylüyor. Suçlamadan, iki kısa cümleyle destek ver ve somut bir sonraki adım öner.', 'Bu kadar emek verdikten sonra yetiştirememek moral bozucu olabilir. İstersen önce en önemli bölümleri belirleyip kısa bir teslim planı hazırlayalım.', 'Empathetic and concrete; exactly two sentences; no diagnosis or unsupported promise.'),
 ('language', 'Aşağıdaki sözdeki "ince" hangi anlamdadır? Bir cümleyle açıkla: "Kırıldığımı fark edip konuyu değiştirmesi ince bir davranıştı."', 'Burada “ince”, karşısındakinin duygularını gözeten, düşünceli ve nazik anlamındadır.', 'Figurative consideration/kindness; not physical thickness or weakness.'),
 ('language', '"İşler yoluna girince haber veririm." cümlesindeki koşulu ve yapılacak eylemi kısa ve doğal biçimde açıkla.', 'Koşul, işlerin yoluna girmesidir; bu gerçekleştiğinde haber verilecektir.', 'Condition remains future/conditional; do not assert things already improved or news already sent.'),
]


def normalized(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def main():
    from prepare_turkish_pilot80_sft import SYSTEM
    rows = [dict(id=f'sft160-dev-{i:02}', task=category,
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=prompt)],
        target=answer, rubric=rubric, evaluation_only=True,
        provenance='agent-authored-independent-development; 2026-11-17; no external dataset extraction',
        reasoning_probe=category=='reasoning')
        for i,(category,prompt,answer,rubric) in enumerate(ITEMS,1)]
    protected=[]
    for split in ['train','test']:
        protected += [json.loads(s) for s in (BASE/f'sft-pilot160-v01/{split}.jsonl').read_text(encoding='utf-8').splitlines()]
    def grams(text,n):
        w=normalized(text).split();return {tuple(w[i:i+n]) for i in range(len(w)-n+1)}
    hits=[]
    for r in rows:
        prompt=r['messages'][-1]['content'];g=grams(prompt,5)
        for p in protected:
            text=p['messages'][-2]['content'];h=grams(text,5)
            if normalized(prompt)==normalized(text) or (g and h and len(g&h)/min(len(g),len(h))>=.35): hits.append([r['id'],p['id']])
            for a in [r['target'],prompt]:
                for v in [m['content'] for m in p['messages'] if m['role']!='system']+[p.get('worked_solution') or '']:
                    if grams(a,12)&grams(v,12): hits.append([r['id'],p['id']])
    assert not hits,hits
    OUT.mkdir(exist_ok=True)
    data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    path=OUT/'questions.jsonl'
    if path.exists(): assert path.read_text(encoding='utf-8')==data,'Frozen dev changed'
    else:path.write_text(data,encoding='utf-8',newline='\n')
    manifest=dict(rows=20,roles='development only; no gradient updates; not final test',
        source='independently agent-authored; reference answers are rubrics, not exclusive wording',
        questions_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        protected_train_test_sha256={s:hashlib.sha256((BASE/f'sft-pilot160-v01/{s}.jsonl').read_bytes()).hexdigest() for s in ['train','test']},
        lexical_overlap_hits=hits,semantic_review='Authored without deriving from old heldout questions; broad skills intentionally shared. No formal semantic-independence guarantee.',
        owner_reviewed=False,limitations='Small agent-authored selection set; not a representative generalization estimate.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(manifest))


if __name__=='__main__':main()
