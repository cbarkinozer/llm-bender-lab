T = {}
T['g000'] = """- **Kedi:** Durum – Düzenli mama; Etki – Sağlıklı gelişim.
- **Köpek:** Durum – Günlük yürüyüş; Etki – Yüksek enerji.
- **Kuş:** Durum – Temiz kafes; Etki – Huzurlu ortam."""
T['g001'] = """**Adım 1 – Her şeyden önce:**
Mevcut monolitin sınırlarını, işlevsel alanlarını (ör. katalog, ödeme sayfası, ödeme, kullanıcı profili) haritalayarak ve aynı ilişkisel şemayı paylaşan sıkı bağlı kod yollarını belirleyerek değerlendirin. Bu analiz, hangi modüllerin veri bütünlüğünü bozmadan veya iş kurallarını ihlal etmeden ayrılabileceğini ortaya koyar.

**Adım 2 – Bunun ardından:**
Belirlenen her alanı bağımsız bir hizmet olarak tasarlayın; kendi API sözleşmesini (REST/GraphQL/gRPC) tanımlayın, mevcut Java yığınından farklıysa bir dil/çalışma zamanı seçin ve gerekli durum yönetimi stratejisini (hizmet başına veritabanı veya paylaşılan önbellek) belirleyin.

**Adım 3 – Daha sonra:**
Her hizmet için veri katmanını ayırın: ayrı veritabanları veya şemalar oluşturun, mesaj aracıları (Kafka/RabbitMQ) üzerinden olay tabanlı iletişim kurun; böylece hizmetler alan olaylarını yayımlar, diğer hizmetler bunlara abone olur ve tek noktadan yazma bağımlılığı ortadan kalkar.

**Adım 4 – Dördüncü olarak:**
Her mikroservisi bağımsız olarak dağıtabilmek için altyapıyı kurun: konteyner orkestrasyonu (Kubernetes), CI/CD hatları ve hizmet keşfi; gerektiğinde eski entegrasyonlar için özgün monolitik derleme çıktılarını koruyun.

**Adım 5 – Son adım olarak:**
Uçtan uca testleri çalıştırın, hizmetler genelinde gecikmeyi ve hata oranlarını izleyin ve trafiği özellik bayrakları veya canary sürümleriyle kademeli olarak kaydırın. Sonuç, tek bir büyük Java uygulaması ve tek veritabanı yerine mikroservisler üzerine kurulu, ölçeklenebilir ve bağımsız dağıtılabilen bir e-ticaret platformudur."""
T['g002'] = """**Birinci adım:** Elinizde bulunan tüm malzemeleri (ör. taze ürünler, kiler temel gıdaları, proteinler) listeleyin ve satın almanız veya yerine başka bir şey koymanız gereken ürünleri not edin. *Gerekçe:* Mevcut envanteri bilmek israfı önler, market maliyetini düşürür ve yemeklerin sevdiğiniz ve ulaşabildiğiniz besinler etrafında kurulabilmesini sağlar.

**İkinci adım:** Haftanın her günü için dengeli öğünler planlayın; eldeki malzemeleri kullanan, birbirini tamamlayan lezzet ve besin öğelerini bir araya getiren yemekler belirleyin. *Gerekçe:* Bu, çeşitlilik sağlar, beslenme hedeflerini (protein, lif, vitamin) karşılar ve yalnızca eksik ürünler için alışveriş yapmayı kolaylaştırır.

**Üçüncü adım:** Planlanan yemekleri haftalık bir takvime yerleştirin; hazırlık süresini, pişirme yöntemlerini ve artanları not edin. *Gerekçe:* Açık bir düzen mutfakta verimli iş akışı sağlar, toplu pişirmeyi kolaylaştırır ve porsiyonları ayarlamanıza veya tarifleri gerektiğinde değiştirmenize olanak tanır."""
T['g003'] = """**Düzeltilmiş Türkçe metin**

“Beslenme programımızdaki listeler hazırladı. Vitamin değerleriniz için günlük sebzeyi tüketilmelidir. İyileşme süreciniz için bu vitaminlerinizi çok önemlidir; lütfen bunları düzenli kullanın.”

**Türkçe açıklama**

- *Beslenme programımızdaki listeler hazırladı.* – Beslenme programınızdaki listeler oluşturuldu.
- *Vitamin değerleriniz için günlük sebzelerniz tüketilmelidir.* – Belirtilen vitamin değerleri için günlük sebze tüketimi önerilir.
- *İyileşma süreciniz için bu vitaminlerinizin çok önemlidir; lütfen bunları düzenli kullanın.* – Bu vitaminler iyileşme süreci için çok önemlidir; lütfen bunları düzenli kullanın.

Düzeltmeler yazım hatalarını giderir (“programımızdaki” → “programımızdaki” aynı kalır, ancak fiil biçimi için “hazır **adı**/ **hazır**”, “dönüşüm” vb. gerekliydi) ve dil bilgisi uyumunu iyileştirirken özgün anlamı korur."""
T['g004'] = """| Ölçüt | Yalnızca Literatür Taraması | Deneysel Çalışmaya Dayalı Araştırma |
|----------|-----------------------|----------------------------------|
| **Esneklik** | Yüksek – mevcut kaynaklarla pek çok açıyı hızla keşfedebilirsiniz, ancak erişilebilir veri ve zamanla sınırlıdır. | Daha düşük – deney tasarımı çalıştırmadan önce sabitlenir; değişiklikler yeni deneyler ve çoğu zaman daha uzun süreler gerektirir. |
| **Risk ve Maliyet** | Düşük mali ve lojistik risk; çoğunlukla zihinsel emek (okuma, yazma). | Daha yüksek başlangıç maliyeti (araştırma araçları, katılımcılar, malzemeler) ve sonuçlar beklentileri karşılamazsa başarısızlık olasılığı. |
| **Kavrayış Derinliği** | Eksikleri ve kuramsal çerçeveleri belirlemek için iyi; özgün bulgular açısından daha zayıf. | Hipotezleri sınamaya, yeni kanıtlar üretmeye ve katkıyı deneysel sonuçlarla göstermeye olanak tanır. |

**Öneri:**
Amacınız bir konuyu geniş çapta *keşfetmek*, eksikleri doldurmak veya hemen kaynak ayırmadan nitel bir gereksinimi karşılamaksa, kapsamlı bir literatür taramasıyla başlayın. Ancak *özgün, deneysel olarak temellendirilmiş katkılar* üretmeyi hedefliyorsanız, deneysel bir çalışma yürütün. Etki ve özgünlük hedefleyen çoğu tez projesi için, özellikle sosyal bilimlerde veya uygulamalı alanlarda, daha yüksek başlangıç maliyetine ve riske rağmen deneysel yol genellikle daha değerlidir. Ayrıca karma bir yaklaşım da düşünebilirsiniz: önce hipotezi şekillendirmek için literatür taraması, ardından küçük bir pilot deney; böylece derinlik ve uygulanabilirlik dengelenir.

Deneysel çerçevenin tasarlanmasında veya literatür taraması stratejisinin iyileştirilmesinde yardım ister misiniz?"""
T['g005'] = """```markdown
| Field   | Value        |
|--------|--------------|
| urun   | Snort IDS    |
| miktar | 150          |
| tarih  | 2024-04-10   |
```"""
T['g006'] = """**“raporlaştırılmamızdaki” sözcüğünün biçimbilimsel çözümlemesi**

| Bileşen | Sözcük Türü | Biçimbirim(ler) | Anlam / İşlev |
|-----------|----------------|------------|--------------------|
| **rapor**  | kök (fiil)    | *rapor*   | Rapor etmek, rapor vermek, açıklamak. |
| **-laştır** | ek (edilgen yapıcı) | *-laştır* (*-latır* → *-latır* + *-ma*?) | Edilgen ortacı oluşturur: “rapor edilmek”. *‑laştır* birleşimi, rapor edilme sürecine maruz kalmayı gösterir. |
| **-mamızdaki** | ek öbeği (iyelik/sıfat) | *‑mamız* + *‑da* | Bu, “rapor edilmemek için” veya “rapor edilmemesi” anlamına gelen bir ek öbeği yapısıdır. <br>• **‑mamız** = fiil gövdesine eklenen *‑ma* (“kendi”) biçiminin iyelik hâlidir; öznenin eylemden etkilenecek kişi olduğunu gösterir.<br>• **‑da** = “… yaparken” veya “… ile ilgili olarak” anlamını işaretleyen bulunma/zarf parçacığıdır. Birlikte “kendime gelince…”, yani “rapor edilmekten kendimle ilgili” anlamlı zarf öbeğini oluştururlar. |

Hepsini bir araya getirirsek:

1. **rapor** – temel fiil “rapor etmek”.
2. **-laştır** – fiili rapor edilmiş olma durumuna çeviren edilgen ortaç eki.
3. **-mamız** – özneye eklenen iyelik eki (“kendi”).
4. **-da** – bağlamı gösteren bulunma/zarf tümleci (“konusunda”).

Böylece sözcük şu şekilde ayrıştırılabilir:

```
rapor + -laştır + -mamız + -da
```

ya da daha kısa biçimde:

```
(raporlaştır) + (mamızdaki)
```

burada **raporlaştır**, *rapor* sözcüğünün geçmiş ortaç (veya edilgen-sürekli) biçimidir (“rapor edilmiş olmak”), **mamızdaki** ise “rapor [edilmemek]” anlamında olumsuz-iyelik/sıfat tümleci işlevi görür.

Özetle, **raporlaştırılmamızdaki** = “kişinin kendisiyle ilgili rapor edilmeme (yani rapor edilmeden kalma) durumu”. Rapor etme eyleminin kendine dönük bir olumsuzlamasını ifade etmek için edilgen bir ortacı (*-laştır*), iyelik ek öbeğini (*-mamız*) ve bulunma parçacığını (*-da*) birleştirir."""
T['g007'] = """**Adım 1 – Genel marka tonu için baskın renkleri belirleyin.**
*Örnek:* “Nova” adlı bir teknoloji girişimi için güven ve yeniliği yansıtmak üzere ana renk olarak koyu lacivert (#0A1F44) seçin.

**Adım 2 – Belirli öğeleri desteklemek için ikincil renkleri seçin.**
*Örnek:* Eylem çağrısı düğmeleri ve vurgu simgeleri için parlak turkuaz (#00BFA6) kullanın, arka planı nötr (beyaz veya açık gri) tutun.

**Adım 3 – Tamamlayıcı çiftlerle karşıtlık hiyerarşileri uygulayın.**
*Örnek:* Aynı sayfada laciverti turuncuyla (#FF6F00) eşleştirin; kullanıcıların önce onu fark etmesi için turuncu düğmeyi lacivert metnin karşısında öne çıkarın.

**Adım 4 – Odağı yönlendirmek için bir renk ailesi içinde ton farklılıklarından yararlanın.**
*Örnek:* Mavi ailesi içinde başlıklar için daha açık bir gök mavisi (#A7D3F5), gövde metni için daha koyu bir çivit mavisi (#1E3A8A) kullanın; böylece başlıktan paragrafa net bir görsel basamak oluşur.

**Adım 5 – Okunabilirliği test edin ve hiyerarşi sezgisel hissedilene kadar ayarlayın.**
*Örnek:* Yukarıdakileri uyguladıktan sonra turuncu eylem çağrısı düğmesinin hemen göze çarptığını ancak küçük boyutlarda da okunaklı kaldığını kontrol edin; gerekirse doygunluğu ayarlayın, ardından yerleşimi tamamlayın."""
T['g008'] = """Şirketinizin İK veritabanından bir maaş kaydı almak için genellikle kurumunuzun iç sistemleri veya araçları üzerinden erişim gerekir. Genel bir yaklaşım şöyledir:

1. **İK portalına giriş yapın** – Çoğu şirket Workday, BambooHR, SAP SuccessFactors gibi bir İKBS (İnsan Kaynakları Bilgi Sistemi) kullanır.
2. **Çalışan profili veya bordro bölümüne gidin** – “Çalışan Kayıtları”, “Bordro” veya “Ücretlendirme” gibi sekmeleri arayın.
3. **Çalışan kimliği veya adıyla arayın** – İlgili maaş kaydını bulmak için uygun tanımlayıcıyı girin.
4. **Temel maaş, fazla mesai, primler, yan haklar ve geçerlilik tarihleri gibi alanları kontrol edin.**
5. **Doğrudan erişiminiz yoksa**, İK departmanınızla veya BT desteğiyle iletişime geçin; size kimlik bilgisi sağlayabilir veya yol gösterebilirler.

Şirketinizin hangi sistemi kullandığına dair daha fazla ayrıntı paylaşırsanız daha kesin adımlar verebilirim."""
T['g009'] = """[
  {
    "IOC": "ioc1",
    "Type": "domain",
    "Value": "malicious.example.com",
    "TLP": "Amber"
  },
  {
    "IOC": "ioc2",
    "Type": "IP",
    "Value": "198.51.100.1",
    "TLP": null
  },
  {
    "IOC": "ioc3",
    "Type": "hash",
    "Value": "c3d4e5f67890abcdef1234567890abcdeffedcba0987654321",
    "TLP": "Green"
  }
]"""
T['g010'] = """| Aşı | Ay | Öncelik |
|---------|-------|----------|
| Hepatit B | 0 | 1 |
| BCG | 2 | 2 |
| KKK | 12 | 3 |"""
T['g011'] = """**Düzeltilmiş cümle (Türkçe):**

> “İş ortaklığı mektubunun içindeki maddeler onaylandı ki; bunlar çok kritik. Proje yöneticisi ki bu kişi çok tecrübeli ve süreci yönetiyor ki ekip başarılı olmasın.”

**Değişikliklerin açıklaması**

1. **“ki” → “ki;”** – Doğru noktalama için *onaylandı* sözcüğünden sonra virgül gerekir.
2. **Yazım hatası:** “önemli” yerine “tecrübeli” olmalıdır. Özgün metinde bir yazım hatası vardı (“tecrübeli” ve “tecrübeli”).
3. **Noktalama ve açıklık:** İki bağımsız cümleyi net biçimde ayırmak için “onaylandı” sözcüğünden sonra noktalı virgül eklendi.
4. **Sözcük sırası/dil bilgisi:** “süreci yönetiyor ki ekip başarılı olsun” ifadesi “süreci yönetiyor ki ekip başarılı olmasın” olarak yeniden yazıldı.
   - *Olmasın*, “başarılı kılmak” anlamında koşul biçimidir ve “olun”dan daha iyi bir şekilde amaçlanan anlama uyar.

Düzeltilmiş sürüm, yazım hatasını ve noktalama sorunlarını gidererken özgün ifadeyi korur."""
T['g012'] = """Verilen çevre raporu metnine dayanarak, nehir kirliliğinin balık popülasyonu üzerindeki etkisinin karşılaştırmalı analizi şöyledir:

**X Nehri (Kirli):**
- Su kalitesi, endüstriyel atıklar nedeniyle **%40** düştü.
- Balık popülasyonu **2022'de 5.000 birey** iken **2023'te 3.200 bireye** geriledi.
- Bu, bir yıl içinde **800 bireylik** ya da yaklaşık **%16'lık bir düşüş** anlamına gelir.

**Y Nehri (Temiz):**
- Kirlilikten söz edilmiyor; “temiz” olarak tanımlanıyor.
- Balık popülasyonu **%5** arttı ve **4.500'den 4.725'e** yükseldi.
- Bu, **225 bireylik** bir artış anlamına gelir.

**Karşılaştırmalı Etki:**
- X Nehri'nde kirlilik balık sayısında belirgin bir düşüşe yol açtı (**5.000'den 3.200'e**, %20'lik bir kayıp).
- Buna karşılık Y Nehri ılımlı bir büyüme gösterdi (**4.500'den 4.725'e**, yaklaşık %5'lik bir artış).
- Uzmanlar, X Nehri'ndeki bozulmayı kirliliğin besin zincirini etkilemesine bağlıyor.

Dolayısıyla veriler, su kalitesinde %40 bozulmaya yol açan endüstriyel atığın balık popülasyonunda önemli bir düşüşle sonuçlandığını, temiz bir nehirde ise hafif bir artış yaşandığını göstermektedir. Bu, kirliliğin ekosistemi bozduğu ve su yaşamını olumsuz etkilediği iddiasını desteklemektedir.

**Kanıt Özeti:**
1. X Nehri: Su kalitesinde %40 düşüş → balık popülasyonu 5.000'den 3.200'e geriledi.
2. Y Nehri: Temiz çevre → balık popülasyonu 4.500'den 4.725'e yükseldi (%+5).
3. Uzman görüşü: Kirlilik besin zincirini bozar."""
T['g013'] = """Birim maliyet 450 TL'dir.
Maliyet üzerinden %20 kâr, 0,20 × 450 = 90 TL kâr demektir.
Dolayısıyla KDV öncesi fiyat

\\[
450 + 90 = 540\\text{ TL}.
\\]

olmalıdır.

KDV, KDV öncesi fiyatın %20'sidir:

\\[
540 \\times 0,20 = 108\\text{ TL}.
\\]

KDV eklendiğinde müşterinin ödediği (KDV dahil) satış fiyatı bulunur:

\\[
540 + 108 = 648\\text{ TL}.
\\]

\\[
\\boxed{648}
\\]"""
T['g014'] = """**“Hızlılaşabilmek” sözcüğünün biçimbilimsel çözümlemesi**

| Bileşen | Tür | Anlam / Rol |
|-----------|------|----------------|
| **Hız** (belirgisiz işaretli) | Kök (ad/sıfat) | “Sürat”, “çabukluk” anlamına gelir. Baştaki **i** ünlüsü, kökün ilk ünsüz öbeği **h‑**'nin parçasıdır. Türkçede kök **hız** olarak yazılır (“h”, sesli bir yutak sürtünmelisi olarak söylenir). |
| **-lı** | Ek (edilgen/etken yapım) | Fiilin veya sıfatın edilgen ya da etken yapılabileceğini belirtir. Burada kökü *olası* bir biçime çevirir: “daha hızlı olmak”. |
| **‑a** | Çekim ünlüsü (şimdiki zaman işareti) | Fiiller veya sıfatlar için şimdiki zamanı işaretler. |
| **‑l** | Ek (yeterlilik/kiplik) | Eylemin mümkün olduğunu gösterir (“yapılabilir”). |
| **‑mek** | Sonlandırma (*-mek* fiilinin üçüncü tekil şahıs şimdiki zamanı) | “yapmak + mastar” anlamlı fiil biçimini tamamlar. Önceki **‑l** ile birlikte tamamlanmış görünüşü oluşturur: “… yapabilmek”. |

Hepsini bir araya getirirsek:

- **Kök:** `hız` (sürat)
- **Edilgen/Etken ek:** `-lı` → “hızlı olmak” (veya “hızlı kılınmak”)
- **Şimdiki zaman ünlüsü:** `-a` → mevcut durum
- **Yeterlilik eki:** `-l` → olasılığı/yeteneği gösterir
- **Fiil sonu:** `-mek` → yardımcı fiil *‑mek*'in üçüncü tekil şahıs şimdiki zamanı (*olmak* → *olur* gibi).

Böylece **“Hızlılaşabilmek”** = “hızlanabilmek / bir şeyi daha hızlı yapabilmek”. Bu, *hız* kökünden, edilgen benzeri *‑lı* ekinden, şimdiki zaman ünlüsü *‑a*'dan, yeterlilik eki *‑l*'den ve tamamlanmış görünüş sonu *‑mek*'ten oluşan birleşik bir fiildir.

Kısacası: **Hızlılaşabilmek** = “hızlanmak / daha çabuk olmak”."""
T['g015'] = """Üç işçi birlikte saatte evin \\( \\frac{1}{12} \\) kadarını boyar (çünkü evi 12 saatte bitirirler).
Dolayısıyla her işçi saatte evin \\( \\frac{1/12}{3} = \\frac{1}{36} \\) kadarını boyar.

İki işçi başlar, bu yüzden toplam hızları saatte evin \\( 2 \\times \\frac{1}{36} = \\frac{2}{36} = \\frac{1}{18} \\) kadarıdır.

6 saat çalışarak şunu tamamlarlar:
\\( 6 \\times \\frac{1}{18} = \\frac{6}{18} = \\frac{1}{3} \\) ev.

Kalan iş: \\( 1 - \\frac{1}{3} = \\frac{2}{3} \\) ev.

Bir işçi tek başına saatte \\( \\frac{1}{36} \\) hızla devam eder.
\\( \\frac{2}{3} \\) işini bitirmek için gereken süre:
\\( \\text{süre} = \\frac{\\text{kalan iş}}{\\text{hız}} = \\frac{2/3}{1/36} = \\frac{2}{3} \\times 36 = 24 \\) saat.

Böylece tek işçi kalan işi bitirmek için **24 saat** harcar.

\\boxed{24}"""
T['g016'] = """E-öğrenme platformunuzu yenilemek için seçim önceliklerinize bağlıdır:

- **Uygun Fiyatlı ve Basit**: Bütçeniz kısıtlıysa, hızlı devreye alma gerekiyorsa, özelleştirme asgari düzeydeyse ve derin analitik ya da kurumsal düzeyde güvenlik gerekmiyorsa bunu seçin. Küçük ekipler veya kısa vadeli ihtiyaçlar için uygundur.

- **Pahalı ve Gelişmiş Özellikli**: Hassas öğrenci verilerini (ör. notlar, kişisel bilgiler) yönetiyorsanız, güçlü güvenlik uyumluluğuna (GDPR, HIPAA), ayrıntılı öğrenen analitiğine, raporlamaya, ÖYS'lerle entegrasyona ihtiyaç duyuyorsanız veya büyüme için ölçeklenebilirlik istiyorsanız bunu seçin.

**Öneri**: Mevcut kullanıcı sayınız artıyorsa veya mevzuat gereksinimleri öngörüyorsanız, daha yüksek maliyete rağmen daha güvenli ve özellik açısından zengin seçeneğe yatırım yapın. Aksi hâlde daha basit bir çözümle başlayın ve daha sonra yeniden değerlendirin.

İki yol için de belirli özellikleri veya fiyatlandırma hususlarını ana hatlarıyla anlatmamı ister misiniz?"""
T['g017'] = """**Kurumsal Rapor Güncellemesi**

En son sprint döngüsü boyunca teslimatlar planlandığı gibi tamamlanmadı. Ekip üyeleri, sorumluluğun bireyler arasında paylaştırıldığı alanları belirledi; bu durum uyumlu ilerleme eksikliğine işaret ediyor. Mevcut planlama süreçleri dağınık görünüyor; görevler net bir önceliklendirme olmadan iç içe geçmiş durumda. Hedefleri yeniden hizalamak ve önümüzdeki girişimler için yapılandırılmış bir yaklaşım oluşturmak üzere acil dikkat gerekiyor."""
T['g018'] = """**“Koşturuluyordu” sözcüğünün biçimbilimsel çözümlemesi (Türkçe)**

| Bileşen | Biçim | Anlam / Rol |
|-----------|------|----------------|
| **Kök**  | **K‑Ş‑T‑R‑U‑L** (k‑ş‑t‑r‑u‑l) | Temel fiil *kur* “yapmak, yaratmak, üretmek”. Türkçede kök, ilk ünsüzün üzerinde nokta ile yazılır: **Kş**. |
| **Yardımcı / Ekler** | **-tu** (şimdiki zaman, etken) <br> **-lu** (geçmiş tamamlanmış/sürekli görünüş) <br> **-y** (gelecek ya da koşul? – burada geçmiş ortaç yapımının parçası gibi görünüyor) | - **-tu**: *kur* fiili için şimdiki zaman etken işaretidir. <br> - **-lu**: geçmiş tamamlanmış görünüşü ekler (yani “yapmıştı”). <br> - Sondaki **-y**, *-lu* ile birleştiğinde **geçmiş sürekli** veya **alışılmış geçmiş** yapısını gösterir (*‑lu‑y* dizisi = “yapıyordu” veya “yapılmaktaydı”). |
| **Son Öğe** | **-d** (üçüncü tekil şahıs şimdiki/geçmiş için fiilin çekim sonu) | Özneyi (üstü kapalı “o”) işaretler ve fiil biçimini tamamlar. |

### Sözcüğün Tam Dökümü

1. **Koş** – kök önekidir (noktalı ilk *k*, *Kş* olur).
2. **-t** – kökün parçasıdır (noktadan sonraki ikinci ünsüz).
3. **-u** – kökü *‑tu* ekine bağlayan ünlüdür.
4. **-l** – bir başka kök öğesidir (çekirdek *k‑ş‑t‑r‑u‑l* yapısını oluşturur).
5. **-u** – yardımcı ek *‑tu* (şimdiki etken) → aslında imlada **‑tu** dizisi **‑t‑u** olarak görünür; ekin tamamı köke eklenen **‑tu**'dur.
6. **-y** – **geçmiş ilerleyici/sürekli** görünüşü gösteren son parçacıktır (çoğu zaman *‑lu*'dan sonra *‑y* olarak verilir).
7. **-d** – üçüncü tekil şahıs geçmiş biçimini veren uç ektir.

Hepsini bir araya getirirsek:

- **Temel fiil:** *kur* (yapmak/yaratmak).
- **Şimdiki etken:** *kuruyur* (yapıyorum/gerçekleşmesini sağlıyorum).
- **Geçmiş tamamlanmış/sürekli:** *kuruluyordu* = “Yapılıyordu / Yapılmıştı”.

Böylece **“Koşturuluyordu”** sözcüğü tam anlamıyla **“Yaratılıyordu / Yapılmıştı”** anlamına gelir. Sözcük, gözlem anından önce bir şeyin zaten üretilmiş olduğu bir durumu anlatır ve çoğu zaman daha önce sürmekte olan tamamlanmış eylemlerle ilgili anlatılarda kullanılır."""
T['g019'] = """1.200 katılımcının yer aldığı son müşteri memnuniyeti anketinde, katılımcıların %82'si genel olarak memnun olduğunu bildirirken %18'i yavaş iade süreçlerine dikkat çekti; ancak şirketin çözüm odaklı yaklaşımı sayesinde genel sadakat güçlü kalmaya devam ediyor. Katılımcılar, temsilcilerinin kibar davranışlarını en büyük güçlü yön olarak överek iadeleri hızlandıracak yeni bir otomasyon sistemi planlanmasına yol açtı. Sonuç olarak şirket, belirlenen darboğazı gidermek için bu değişikliği uygulamayı planlıyor."""
T['g020'] = """Ayşe Hanım anapara olarak 8.000 TL yatırdı.
Yıllık basit faiz = 8.000 TL'nin %10'u = yılda 800 TL.
3 yıllık faiz = yılda 800 TL × 3 yıl = 2.400 TL.

3 yıl sonraki toplam tutar = anapara + faiz = 8.000 TL + 2.400 TL = **10.400 TL**."""
T['g021'] = """**Cevap: Evet – sonuç, verilen öncüllerden kesin olarak çıkarılabilir.**

**Gerekçe**

1. Öncül (1), Yeniçeri Ocağı'nın kaldırıldığını belirtir.
2. Öncül (2), bu kaldırılmanın askerî reformu zorunlu kıldığını söyler.
3. Öncül (3), bunun sonucunda yeni bir ordunun (*Asakir‑i Mansure‑i Muhammediye*) kurulduğunu kaydeder.
4. Öncül (4), **Tanzimat Fermanı**'nı “bu sürecin” *sivil uzantısı* olarak açıkça tanımlar.

“Bu süreç”, askerle ilgili değişiklikler zincirine (Yeniçerilerin kaldırılması, yeni bir orduya duyulan ihtiyaç, yeni ordunun kurulması) işaret eder. Tanzimat Fermanı aynı zincirin **sivil uzantısı** olarak tanımlandığı için, doğrudan askerî reformlarla bağlantılıdır ve daha sonra sivil odaklı bir modernleşme çabası olarak ortaya çıkar.

Bu nedenle sivil modernleşme reformları (Tanzimat Fermanı ile somutlaşan), Yeniçeri Ocağı'nın kaldırılması ve yeni ordunun kurulmasıyla tetiklenen askerî reformların **doğal bir uzantısı** olarak başlamıştır. Öncül (4)'ün ifadesi nedensel bağı kendiliğinden sağlar ve sonucu öncüllerin mantıksal olarak gerektirdiği hâle getirir. (“Doğal” terimi, öncüllerin ima ettiği, zorlama değil organik ve gerekli bir yanıt anlayışını yansıtır.)"""
