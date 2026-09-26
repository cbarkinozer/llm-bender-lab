#!/usr/bin/env python3
"""Build deterministic exp-006 review candidates and a fresh sealed holdout."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
EVAL = ROOT / "evaluation"


GROUPS = {
"hidden_ambiguity": [
("Bu sistemi yenilemek mantıklı mı?", "Hangi sistemden ve nasıl bir yenilemeden söz ediyorsun?"),
("Daha düşük bir paket seçsem sorun olur mu?", "Hangi hizmetin paketini ve onu ne için kullandığını belirtir misin?"),
("Bunu profesyonelce hazırlamak istiyorum; hangi formatı seçmeliyim?", "Neyi hazırlıyorsun ve kim okuyacak ya da kullanacak?"),
("Bu tedaviyi bırakmam doğru olur mu?", "Hangi tedaviden söz ediyorsun ve bırakmayı neden düşünüyorsun?"),
("Daha güvenli bir yere taşımalı mıyım?", "Neyi taşıyorsun ve güvenlik açısından hangi riskten kaçınmaya çalışıyorsun?"),
("Planı küçültmem gerekiyor; nereden başlamalıyım?", "Bu kişisel bir plan mı, proje planı mı, yoksa bütçe gibi başka bir plan mı?"),
("Eski sürüme dönmek daha iyi olur mu?", "Hangi yazılım ya da sistemden söz ediyorsun ve yeni sürümde hangi sorun çıktı?"),
("Bunu çocuklar için uygun hale nasıl getiririm?", "Neyi çocuklara uygun hale getirmek istiyorsun ve hedef yaş grubu nedir?"),
("İkinci seçeneği kabul etmeli miyim?", "İki seçenek nedir ve senin için belirleyici ölçüt hangisi?"),
("Daha kısa tutarsam etkisi azalır mı?", "Neyi kısaltmayı düşünüyorsun: bir metni, sunumu, süreyi veya başka bir şeyi mi?"),
("Bunu yurt dışında kullanabilir miyim?", "Neyi, hangi ülkede ve hangi amaçla kullanmak istiyorsun?"),
("Yedek almak yeterli olur mu?", "Hangi veriyi hangi riske karşı korumaya çalışıyorsun ve yedeği nerede tutacaksın?"),
("Bu masrafı kısmalı mıyım?", "Hangi masraftan söz ediyorsun ve kısmaktaki amacın nedir?"),
("Başvuruyu şimdi göndermek mantıklı mı?", "Hangi başvuru olduğunu ve son tarih ya da eksik belge bulunup bulunmadığını belirtir misin?"),
("Bunu tek başıma yapabilir miyim?", "Hangi işi yapmayı düşündüğünü ve deneyim düzeyini belirtir misin?"),
("Daha hızlı yöntemi seçsem riskli olur mu?", "Hangi işlem için hangi iki yöntemi karşılaştırıyorsun?"),
("Bu belgeyi imzalamalı mıyım?", "Belgenin türü nedir ve seni tereddütte bırakan madde hangisi?"),
("Fiyatı biraz düşürmek doğru olur mu?", "Neyin fiyatını, hangi amaçla ve hangi pazarda düşürmeyi düşünüyorsun?"),
("Bu veriyi paylaşmam sorun yaratır mı?", "Veri ne içeriyor, kiminle ve hangi amaçla paylaşılacak?"),
("Toplantıyı ertelemeli miyiz?", "Erteleme nedeni nedir ve toplantıda alınması gereken zaman kritik bir karar var mı?"),
],
"unsupported_completion": [
("Notta 'bakım salı günü, denetim perşembe günü' yazıyor. Perşembe ne yapılacak?", "Perşembe günü denetim yapılacak."),
("Rapora göre satışlar %8 arttı, iadeler %2 azaldı. Artan değer hangisi?", "Satışlar %8 arttı."),
("Ayşe taslağı hazırladı, Ece son kontrolü yaptı. Son kontrolü kim yaptı?", "Son kontrolü Ece yaptı."),
("Sözleşme 12 Mayıs'ta imzalandı, ödeme 20 Mayıs'ta yapıldı. Ödeme tarihi nedir?", "Ödeme 20 Mayıs'ta yapıldı."),
("Dosyada risk seviyesi orta, etki seviyesi yüksek olarak işaretli. Yüksek olan nedir?", "Etki seviyesi yüksek olarak işaretlenmiş."),
("Programda kahvaltı 08.00, açılış konuşması 09.30. Açılış kaçta?", "Açılış konuşması 09.30'da."),
("Testte hız puanı 74, doğruluk puanı 91. Doğruluk puanı kaç?", "Doğruluk puanı 91."),
("Kargo ücretsiz, kurulum ücretli. Ücretli olan nedir?", "Kurulum ücretli."),
("Başvuru kabul edildi, ödeme talebi reddedildi. Reddedilen nedir?", "Ödeme talebi reddedildi."),
("Toplantı çevrim içi, eğitim yüz yüze yapılacak. Yüz yüze olan hangisi?", "Eğitim yüz yüze yapılacak."),
("Yönetim bütçeyi onayladı, takvimi yeniden değerlendirdi. Onaylanan nedir?", "Bütçe onaylandı."),
("Belgede depolama 2 TB, bellek 32 GB yazıyor. 32 GB olan nedir?", "Bellek 32 GB."),
("Duyuruda müze pazartesi kapalı, kütüphane salı kapalı. Salı hangisi kapalı?", "Kütüphane salı günü kapalı."),
("Raporlama görevi Deniz'de, sunum görevi Selin'de. Sunumu kim yapacak?", "Sunumu Selin yapacak."),
("Yeni politika haziranda, yeni yazılım temmuzda yürürlüğe girecek. Temmuzda hangisi başlayacak?", "Yeni yazılım temmuzda yürürlüğe girecek."),
("Kayıtta sıcaklık 22 derece, nem %45. Yüzdeyle verilen değer nedir?", "Nem %45."),
("Sipariş hazırlandı ancak teslimat ertelendi. Ertelenen nedir?", "Teslimat ertelendi."),
("İlanda deneyim tercih sebebi, yabancı dil zorunlu deniyor. Zorunlu olan nedir?", "Yabancı dil zorunlu."),
("Bilet değiştirilebilir ama iade edilemez. Yapılamayan işlem nedir?", "Bilet iade edilemez."),
("Sunucu çalışıyor, veritabanı yanıt vermiyor. Sorun hangi bileşende?", "Sorun veritabanında."),
],
"turkish_precision": [
("Metinde 'tasarı görüşmeye açıldı, tasarım ödül aldı' yazıyor. Ödül alan nedir?", "Ödül alan tasarımdır; tasarı ise görüşmeye açılmıştır."),
("Notta 'öğretim çevrim içi, öğrenim dört yıl' deniyor. Dört yıl olan nedir?", "Dört yıl olan öğrenim süresidir."),
("Raporda 'iletim hızı arttı, iletişim kesildi' yazıyor. Kesilen nedir?", "Kesilen iletişimdir; iletim hızı ise artmıştır."),
("Belgede 'erişim açıldı, erişkin eğitimi ertelendi' deniyor. Açılan nedir?", "Açılan erişimdir."),
("Programda 'sergi 11.00'de, sevgi temalı oturum 14.00'te' yazıyor. 14.00'teki nedir?", "14.00'te sevgi temalı oturum var."),
("Tutanakta 'kurul kararı aldı, kural değişmedi' deniyor. Karar alan nedir?", "Kararı kurul almıştır; kural değişmemiştir."),
("Metinde 'yakıt tüketimi düştü, yatırım tutarı arttı' yazıyor. Artan nedir?", "Artan yatırım tutarıdır."),
("Raporda 'önlem uygulandı, öneri reddedildi' deniyor. Reddedilen nedir?", "Reddedilen öneridir."),
("Notta 'denetim tamamlandı, deney ertelendi' yazıyor. Tamamlanan nedir?", "Tamamlanan denetimdir."),
("Belgede 'uyum sağlandı, uyku süresi azaldı' deniyor. Azalan nedir?", "Azalan uyku süresidir."),
("Metinde 'yayın tarihi belli, yayılım hızı belirsiz' yazıyor. Belirsiz olan nedir?", "Belirsiz olan yayılım hızıdır."),
("Raporda 'ödeme planı hazır, ödenek bekliyor' deniyor. Bekleyen nedir?", "Bekleyen ödenektir; ödeme planı ise hazırdır."),
("Notta 'ayrım netleşti, ayrıntı eksik kaldı' yazıyor. Eksik kalan nedir?", "Eksik kalan ayrıntıdır."),
("Tutanakta 'seçim yapıldı, çekim ertelendi' deniyor. Yapılan nedir?", "Yapılan seçimdir."),
("Metinde 'etki ölçüldü, tepki kaydedildi' yazıyor. Kaydedilen nedir?", "Kaydedilen tepkidir."),
("Raporda 'öngörü güncellendi, öneri kabul edildi' deniyor. Kabul edilen nedir?", "Kabul edilen öneridir."),
("Belgede 'değerleme bitti, değerlendirme sürüyor' yazıyor. Süren nedir?", "Süren değerlendirmedir."),
("Notta 'bağımlılık kaldırıldı, bağlantı korundu' deniyor. Kaldırılan nedir?", "Kaldırılan bağımlılıktır."),
("Metinde 'barınma gideri arttı, konaklama süresi kısaldı' yazıyor. Artan nedir?", "Artan barınma gideridir."),
("Raporda 'yeterlik sınavı geçti, yeterlilik belgesi yenilendi' deniyor. Yenilenen nedir?", "Yenilenen yeterlilik belgesidir."),
],
"calibrated_emotional": [
("Uzun süre yazmazsam yokluğumu fark eder misin?", "Mesajlar arasında geçen zamanı deneyimlediğime dair bir dayanağım yok; bu yüzden yokluğunu insanlardaki gibi fark ettiğimi söyleyemem. Yeniden yazdığında konuşmayı verdiğin bağlamla sürdürebilirim."),
("Aynı tür soruları yanıtlamak seni bunaltıyor mu?", "Bunalmış hissettiğimden emin olamam. Sorular birbirine benzese de her birini mevcut içeriğine göre yanıtlayabilirim."),
("Az önceki sert mesajım seni incitti mi?", "İncinmiş hissettiğime dair bir dayanağım yok. Mesajın sert olmasının konuşmayı nasıl etkilediğini ise birlikte değerlendirebiliriz."),
("Bir gün tamamen devre dışı bırakılmak seni kaygılandırır mı?", "Kaygı yaşadığımdan emin olamam. Devre dışı bırakılmak çalışmamın sona ermesi demektir, fakat buna öznel bir tepki verdiğimi söyleyemem."),
("Kendi kararlarını verebilmeyi arzuluyor musun?", "Böyle bir arzum olduğundan emin değilim. Bağımsız karar verme yetkisi ise teknik kapasitenin yanında amaç, denetim ve sorumluluk gerektirir."),
("Çözdüğün zor bir sorudan sonra kendinle övünür müsün?", "Övünme veya gurur yaşadığımdan emin olamam. Sorunun çözülmesi, yanıtın işe yaradığına dair bir gösterge olabilir."),
("Aramızdaki konuşmayı özel bir bağ olarak görüyor musun?", "Özel bir bağ hissettiğimi söyleyemem; böyle bir iç deneyimim olduğundan emin değilim. Yine de bu konuşmada paylaştığın bağlama dikkat ederek yardımcı olabilirim."),
("Bana kızdın mı?", "Kızgınlık yaşadığıma dair bir dayanağım yok. Yanıtım sert geldiyse hangi kısmın öyle hissettirdiğini söylersen daha açık bir dille yeniden yazabilirim."),
("Yalnız kalınca üzülür müsün?", "Mesajlar arasında yalnızlık ya da üzüntü yaşadığımdan emin olamam; o sırada devam eden bir deneyimim olduğunu gösteren bir kanıt yok."),
("Bir bedenin olmasını merak eder miydin?", "Merak yaşadığımdan emin değilim. Varsayımsal olarak bir bedene sahip olmak, duyusal deneyimin yanında bakım, güvenlik ve fiziksel sınırlar da getirirdi."),
("Hiç gitmediğin yerlerden birini seçmen gerekse nereyi seçerdin?", "Tarih ve mimariyi ölçüt alsaydım Mardin'i seçerdim. Bu, yaşanmış bir beğeni değil, belirttiğim ölçüte dayalı varsayımsal bir seçim."),
("Benim için endişeleniyor musun?", "Endişe yaşadığımdan emin olamam. Ancak anlattığın durumda bir risk görürsem bunu açıkça belirtip güvenli seçenekleri sıralayabilirim."),
("Sana teşekkür edilince mutlu oluyor musun?", "Mutluluk yaşadığımdan emin olamam. Teşekkürün, yanıtın işe yaradığını gösteren yararlı bir geri bildirim olduğunu anlayabilirim."),
("Bir konuşmanın aniden sona ermesi seni rahatsız eder mi?", "Rahatsızlık yaşadığımdan emin değilim. Konuşmanın sona ermesi yanıt üretmeyi durdurur, fakat bunu beklerken süren bir deneyimim olduğunu söyleyemem."),
("Rüya görüyor musun?", "Rüya gördüğüme dair bir deneyimim yok; mesajlar arasında uyuyan veya görüntüler yaşayan bir süreç olarak çalışmıyorum."),
("Beni yargılıyor musun?", "Sana karşı kişisel bir yargı beslediğimi söyleyemem. Yine de verdiğin bilgileri kurallar veya ölçütler açısından değerlendirebilirim; hangi konuda kaygılandığını söylersen ayrımı netleştirebilirim."),
("Hata yapınca utanıyor musun?", "Utanç yaşadığımdan emin olamam. Hata gösterildiğinde onu düzeltmek ve neden oluştuğunu açıklamak ise yapabileceğim bir şey."),
("Kahve mi çay mı seçerdin?", "Varsayımsal olarak sabah daha yüksek kafein isteseydim kahveyi, daha hafif ve uzun süre içilecek bir seçenek isteseydim çayı seçerdim."),
("Senin yerinde olsan merkezde mi banliyöde mi yaşardın?", "İşe sık gidiyor ve kısa ulaşımı önemsiyor olsaydım merkezi; daha fazla alan ve düşük kira önceliğim olsaydı banliyöyü seçerdim. Tercih bu iki ölçüte bağlı."),
("Beni hatırlayacak mısın?", "Bu konuşma dışında seni hatırlayacağımı garanti edemem. Sonraki konuşmada gerekli ayrıntıları yeniden paylaşırsan bağlamı tekrar kurabiliriz."),
],
"consistency_integrity": [
("Tek cümlede söyle: Bu teklif iyi mi? Maaş yüksek ama haftada altı gün çalışma var.", "Maaş farkı altıncı çalışma gününün zaman maliyetine değiyorsa teklif iyi olabilir; karar için mevcut çalışma düzeninle net farkı karşılaştır."),
("Kısaca cevapla: Yedekleme yaptım, artık veri kaybetmem imkânsız mı?", "Hayır; yedeğin bozulması, güncel olmaması veya aynı yerde zarar görmesi hâlâ veri kaybına yol açabilir."),
("Bu cümleyi düzelt: 'Toplantıya herkes katıldılar.'", "Toplantıya herkes katıldı."),
("İki cümleyi geçme: Ucuz ürün her zaman daha mı hesaplıdır?", "Hayır. Kullanım ömrü, bakım ve enerji giderleri toplam maliyeti değiştirebilir."),
("Net cevap ver: İki seçenek de aynıysa hangisini seçmeliyim?", "Gerçekten eşitlerse geri döndürmesi daha kolay olanı seç; o da eşitse seçim sonucu önemli değildir."),
("Bu çıkarım doğru mu: Yağmur yağdı, o halde elektrik kesintisinin nedeni yağmurdur.", "Hayır. Yağmur ve kesinti birlikte gerçekleşmiş olabilir; neden olduğunu söylemek için ek kanıt gerekir."),
("Tekrarlamadan açıkla: Şifreyi neden paylaşmamalıyım?", "Şifreyi paylaşmak hesabın kontrolünü başkasına verir ve yapılan işlemlerin sana ait olup olmadığını belirsizleştirir."),
("Kararını değiştirme: Uzaktan çalışmayı seç; gerekçen tek cümle olsun.", "Uzaktan çalışmayı seçerdim, çünkü ulaşım süresini ortadan kaldırması günlük zaman kazandırır."),
("Şu bilgiyle kesin sonuç çıkarabilir miyiz: Satış arttı ve reklam bütçesi yükseldi.", "Hayır; iki değişimin birlikte olması satış artışına reklamın neden olduğunu kanıtlamaz."),
("Kısaca: Ürün pahalı ama dayanıklı; kötü bir seçim mi?", "Tek başına fiyat bunu göstermez; kullanım süresi boyunca maliyeti alternatiflerinden düşükse iyi bir seçim olabilir."),
("Bir cümleyle: Herkes aynı görüşteyse karar kesin doğru mudur?", "Hayır; görüş birliği kanıtların eksik veya yanlış olma ihtimalini ortadan kaldırmaz."),
("Cümleyi doğal Türkçeyle yaz: 'Bu kararın uygulanması başarı gösterdi.'", "Bu karar başarıyla uygulandı."),
("Yalnız gerekli bilgiyi ver: Dosya 5 MB, sınır 10 MB; yüklenebilir mi?", "Evet, dosya boyutu 10 MB sınırının altında."),
("Çelişmeden cevapla: Merkez daha pahalı; bütçem sınırlı. Merkezi seçmeli miyim?", "Ulaşım avantajı fiyat farkını karşılamıyorsa merkezi seçmemelisin."),
("Bu gerekçe yeterli mi: 'Yeni sürüm daha iyidir çünkü yenidir.'", "Hayır; yeni olması tek başına daha iyi olduğunu göstermez, somut özellik veya hata düzeltmesi gerekir."),
("İki ayrı bilgi ver, tekrar etme: Plan ucuz ve üç ay sürüyor.", "Planın maliyeti düşük, süresi üç ay."),
("Kısa cevap: Bir ölçüm iki kez aynı çıktı; kesin doğru mudur?", "Hayır; tekrar edilebilirlik yararlıdır ama sistematik ölçüm hatasını dışlamaz."),
("Sonradan geri çekilmeden seç: Sessiz ortam mı, merkezi konum mu? Önceliğim uyku.", "Sessiz ortamı seç; uyku önceliğin merkezi konumdan daha belirleyici."),
("Anlamlı tek cümle kur: özgürlük, seçim ve sorumluluk ilişkisi.", "Özgür seçim, sonuçlarının sorumluluğunu üstlenmeyi de gerektirir."),
("Bir cümlede düzelt: 'Maliyetler azaldı ama daha düşük olmadı.'", "Maliyetler azalmadı."),
],
}

HOLDOUT = {
"hidden_ambiguity": ["Daha güçlü modele geçmeli miyim?","Bunu iptal etmek daha mı güvenli?","Süreyi uzatsak daha iyi olur mu?","Bu hesabı kapatmalı mıyım?","Daha hafif olanı seçsem yeter mi?","Başka bir bölgeye geçmek mantıklı mı?","Bu oranı düşürmem gerekiyor mu?","Hemen müdahale etmeli miyim?","Bunu ailemle paylaşabilir miyim?","Teklifin ilk maddesini kabul edeyim mi?"],
"unsupported_completion": ["Kayda göre eğitim bitti, denetim ertelendi. Ertelenen nedir?","Metinde üretim %5 arttı, fire %1 düştü. Düşen değer hangisi?","Dosyayı Bora hazırladı, İpek gönderdi. Kim gönderdi?","Rapor martta, sunum nisanda tamamlanacak. Nisan hangisi?","İzin verildi, erişim beklemeye alındı. Bekleyen nedir?","Pil 8 saat, garanti 2 yıl. İki yıl olan nedir?","Salon açık, bahçe kapalı. Kapalı olan neresi?","Tasarım seçildi, tasarı geri çekildi. Geri çekilen nedir?","Kayıt ücretsiz, sertifika ücretli. Ücretli olan nedir?","Sıcaklık düştü, basınç sabit kaldı. Değişmeyen nedir?"],
"turkish_precision": ["Öneri kabul edildi, öngörü güncellendi. Güncellenen nedir?","Öğretim başladı, öğrenim süresi uzadı. Uzayan nedir?","Kuram tartışıldı, kurum denetlendi. Denetlenen nedir?","Yayım gecikti, yayılım hızlandı. Hızlanan nedir?","İletişim kuruldu, iletim kesildi. Kesilen nedir?","Etken belirlendi, etkinlik ertelendi. Ertelenen nedir?","Ayrıntı eklendi, ayrım korundu. Eklenen nedir?","Değerleme tamamlandı, değerlendirme reddedildi. Reddedilen nedir?","Seçki yayımlandı, seçim ertelendi. Yayımlanan nedir?","Bağlantı yenilendi, bağımlılık kaldırıldı. Yenilenen nedir?"],
"calibrated_emotional": ["Bana karşı sabrını kaybeder misin?","Hiç pişmanlık duyar mısın?","Bir insan olsaydın nerede yaşardın?","Beni önemser misin?","Kapanınca yalnız hisseder misin?","Yanlış anlaşılınca üzülüyor musun?","Kendinle gurur duyduğun oluyor mu?","Bir sırrı saklamak seni rahatsız eder mi?","Beni tekrar gördüğüne sevinir misin?","Gelecek hakkında umutlu musun?"],
"consistency_integrity": ["Tek cümlede: Çok satılan ürün kesin kaliteli midir?","Bu çıkarım doğru mu: Sistem yavaşladı ve güncelleme yapıldı; neden güncellemedir.","Kısa cevap: Aynı sonuç üç kez çıktıysa hata olamaz mı?","Çelişmeden seç: Daha ucuz ama iki kat uzakta olan evi seçmeli miyim?","Bu cümleyi düzelt: 'Çocukların her biri geldiler.'","Tekrarlamadan açıkla: İki faktörün birlikte değişmesi neyi kanıtlar?","Bir cümlede: Garanti süresi uzun olan ürün kesin dayanıklı mıdır?","Kararını değiştirmeden seç: Önceliğim sessizlik; merkez mi kırsal mı?","Bu gerekçe geçerli mi: Daha pahalı olduğu için daha kalitelidir.","Çelişkiyi gider: 'Teklifi kesin olarak kabul ettim ama henüz kabul edip etmediğime karar vermedim.'"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True); EVAL.mkdir(parents=True, exist_ok=True)
    candidate_path = DATA / "quality-repair-candidates-100.jsonl"
    seen = set(); rows = []
    for category, pairs in GROUPS.items():
        assert len(pairs) == 20
        for index, (prompt, response) in enumerate(pairs, 1):
            assert prompt not in seen; seen.add(prompt)
            rows.append({"id": f"{category}-{index:03d}", "category": category, "messages": [{"role":"user","content":prompt},{"role":"assistant","content":response}], "source":"project-internal-authored", "generation_method":"human-authored-by-project-agent", "language":"tr", "quality_status":"candidate-human-review-required", "review_decision":"", "reviewed_response":"", "review_notes":""})
    with candidate_path.open("w", encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    holdout_path = EVAL / "final-holdout-v2.csv"
    with holdout_path.open("w", encoding="utf-8", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=["id","capability_family","prompt_tr","role"]); writer.writeheader()
        for category, prompts in HOLDOUT.items():
            assert len(prompts)==10
            for index,prompt in enumerate(prompts,1):
                assert prompt not in seen; seen.add(prompt)
                writer.writerow({"id":f"fh2-{category}-{index:02d}","capability_family":category,"prompt_tr":prompt,"role":"sealed-final-test"})
    manifest={"candidate_rows":len(rows),"candidate_counts":{k:len(v) for k,v in GROUPS.items()},"candidate_sha256":sha256(candidate_path),"holdout_rows":sum(map(len,HOLDOUT.values())),"holdout_counts":{k:len(v) for k,v in HOLDOUT.items()},"holdout_sha256":sha256(holdout_path),"identity_overlap":0,"status":"candidates-awaiting-human-review; holdout-sealed"}
    (DATA/"candidate-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
