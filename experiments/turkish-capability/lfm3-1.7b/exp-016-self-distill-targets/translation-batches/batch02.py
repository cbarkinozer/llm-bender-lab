T = {}
T['g022'] = """En makul neden **B**'dir – 600 kg'lık kiriş, 1,8 saniyelik düşüş sırasında önemli bir hız kazandığı için büyük miktarda kinetik enerji taşır. Yere çarptığında bu enerji hızla ses, titreşim ve şekil değişikliğine aktarılır; bu da aynı yükseklikten düşen daha hafif bir cisme kıyasla daha gürültülü, “daha ağır” bir ses çıkarır. Diğer seçenekler gerçekçi olmayan ısınmaya, manyetik etkilere, değişken yerçekimine ya da psikolojik abartıya başvururken, çarpma anında kinetik enerjinin hızla dönüşmesi standart dinamikle iyi açıklanır."""
T['g023'] = """Saat yönünde 90° dönme matrisi

\\[
R_{90^\\circ(\\text{saat yönü})}= \\begin{pmatrix} 0 & 1 \\\\ -1 & 0 \\end{pmatrix},
\\]

çünkü \\((x,y)\\mapsto (y,-x)\\).
Bu matrisin karesini alırsak:

\\[
R_{90^\\circ}^2 = \\begin{pmatrix} 0 & 1 \\\\ -1 & 0 \\end{pmatrix}
               \\begin{pmatrix} 0 & 1 \\\\ -1 & 0 \\end{pmatrix}
            = \\begin{pmatrix} -1 & 0 \\\\ 0 & -1 \\end{pmatrix}
            = -I.
\\]

Böylece karesi, **180° dönmeyi** (veya orijine göre nokta yansımasını) temsil eden negatif birim matrise eşittir. Koordinatlarda bu dönüşüm

\\[
(x,y) \\longmapsto (-x,\\,-y).
\\]

\\((3,7)\\) noktasına uygulandığında:

\\[
(3,7) \\xrightarrow{\\;(-x,-y)\\;} (-3,-7).
\\]

**Cevap:** Eşdeğer dönüşüm 180°'lik bir dönmedir (matris \\(-I\\)) ve \\((3,7)\\) noktası \\((-3,-7)\\) noktasına taşınır."""
T['g024'] = """Hasta her gün

- 4 hareket
- hareket başına 3 set
- set başına 12 tekrar → \\(4 \\times 3 \\times 12 = 144\\) tekrar/gün yapar

Bir tekrar \\(5,4\\) sn sürdüğüne göre günlük etkin (dinlenme dışı) süre

\\[
144 \\text{ tekrar} \\times 5,4\\ \\text{sn/tekrar}=777,6\\ \\text{sn}=12,96\\ \\text{dk}.
\\]

Fizyoterapist programı haftada 3 gün uyguladığına göre haftalık etkin çalışma süresi

\\[
3 \\text{ gün} \\times 12,96\\ \\text{dk/gün}=38,88\\ \\text{dk}.
\\]

\\[
\\boxed{38,88\\ \\text{dakika/hafta}}
\\]"""
T['g025'] = """Antrenman **43,5 dakika** sürer (yani 43 dakika 30 saniye).

*Hesaplama*
- Hareket başına tekrar: 5 set × 10 tekrar = 50 tekrar.
- Tekrar süresi: 50 tekrar × 4,2 sn = 210 sn.
- Bir hareket içinde setler arası dinlenme: 4 aralık × 60 sn = 240 sn.
- Bir hareketin süresi (tekrarlar + set dinlenmeleri) = 210 sn + 240 sn = 450 sn.
- Beş hareket: 5 × 450 sn = 2250 sn.
- Hareketler arası geçişler: 4 geçiş × 90 sn = 360 sn.
- Toplam = 2250 sn + 360 sn = 2610 sn.
- Dakikaya çevirme: 2610 sn ÷ 60 sn/dk = **43,5 dk**."""
T['g026'] = """**Cevap: Yanlış.**

**Neden?**
“Yeni açılan spor salonları arttıkça ortalama tansiyon düşüyor” gözlemi yalnızca bir *korelasyondur*. Epidemiyolojide ve psikolojide korelasyon tek başına şunları **göstermez**:

1. **Değişime hangi değişkenin yol açtığını.** Hem spor salonu açılışlarını hem de tansiyonu etkileyen birçok kafa karıştırıcı etken olabilir (ör. daha sağlıklı beslenme, azalan stres, sosyoekonomik değişimler, sağlık hizmetlerine artan erişim veya eşzamanlı sağlığı geliştirme kampanyaları).
2. **Diyet danışmanlığı senaryosunun nedenselliğini.** Spor salonlarının tansiyon üzerinde doğrudan fizyolojik etkisi olmadığını varsaysak bile, *diyet danışmanlığının* tek başına aynı düşüşü sağlayıp sağlamayacağı hakkında bilgimiz yoktur. Hiçbir etkisi olmayabilir ya da olabilir; ancak diyet danışmanlığını yalıtan randomize bir deney veya kontrollü bir gözlemsel çalışma olmadan bunu bilemeyiz.

Dolayısıyla spor salonları açıldığında tansiyonun düşmüş olması, salon açmanın nedenin kendisi olduğunu çıkarmak ya da farklı bir programın (yalnızca diyet danışmanlığı) sonucunu tahmin etmek için **kullanılamaz**. “Yalnızca diyet danışmanlığı yaygınlaşsaydı ne olurdu?” karşı-olgusal sorusunu değerlendirmek için diğer değişkenleri kontrol eden deneysel veya boylamsal verilere, yani basit bir korelasyonun çok ötesinde bir şeye ihtiyaç duyarız. Sonuç olarak yalnızca verilen korelasyona dayanarak önerme desteklenmez; **yanlıştır** (ya da en iyi ihtimalle belirsizdir)."""
T['g028'] = """**B) Çelişki (tutarsızlık)**

İki ifade doğrudan birbiriyle çelişir: biri, hükümetin bütçe açığını azaltmak için yeni vergi kalemleri *eklemeyi planladığını* (yani vergileri artırmayı veya ek yükümlülükler getirmeyi) söylerken diğeri vatandaşların satın alma gücünü korumak için *vergi indirimi* yapacağını iddia ediyor. Aynı mali önlem için hem vergi artışının hem de vergi indiriminin önerilmesi mantıksal olarak tutarsızdır; ek bir açıklama olmadan aynı anda doğru olamaz. Bu tutarsızlık, birleşim yanılgısı, döngüsellik, belirsizlik veya nedensel yanlış atıf yerine bir çelişki oluşturur.

Dolayısıyla yalnızca verilen metne göre değerlendirildiğinde, parça bir **çelişki** içermektedir."""
T['g029'] = """Gözetim görevi savunmayı geçersiz kılar, çünkü sözleşmeyi verme eylemi başlı başına kamusal hesap verebilirliğe ve düzenleyici incelemeye tabidir. Bir kamu kurumu (temizlik müdürlüğü) çöp toplama gibi bir kamu hizmeti için yüklenici seçmek gibi satın alma kararları verdiğinde, seçilen firmanın çevre düzenlemeleri dâhil geçerli tüm yasalara uymasını sağlama sorumluluğunu üstlenir. Uygunluğu doğrulamadan ihaleyi yalnızca en düşük teklife göre vererek yetkili, firmanın yasalara uygun mu yoksa yasa dışı mı davrandığı (ör. izinsiz boşaltma) konusundaki denetimi fiilen terk etmiştir. Bu, usule uygunluk açısından bir başarısızlık yaratır: Kamunun, kararın adil ve yasal biçimde verildiğini doğrulayacak bağımsız bir mekanizması yoktur. Dahası, firmanın çevre mevzuatını ihlal ettiği sonradan ortaya çıkarsa belediye ihmal veya güven yükümlülüğünün ihlali nedeniyle sorumlu tutulabilir. Dolayısıyla yetkili “yalnızca ihaleyi yürüttüğünü” iddia etse de, kamu kaynaklarının sorumlu biçimde yönetilmesini ve sözleşmelerin yasaya uygun olmasını güvence altına alan daha geniş gözetim görevi, böyle bir kararın denetimsiz ilerlemesine izin verilerek ihlal edilmiştir.

**Kısacası:** Savunma başarısız olur, çünkü seçim süreci, hükümetin yüklenicileri denetleme ve düzenleme konusundaki yasal yükümlülüğünün bir parçasıdır; uygunluk kontrollerini atlamak hesap verebilirliği zayıflatır ve belediyeyi kendi eylemleri nedeniyle hukuki sorumluluğa maruz bırakır."""
T['g030'] = """Elma (\\(x\\)) ve armutun (\\(y\\)) kilogram fiyatlarını bulmak için verilen iki durumu bir doğrusal denklem sistemi olarak yazalım:

1. Ali 3 kg elma ve 2 kg armut aldı ve 50 TL ödedi:
   \\[
   3x + 2y = 50 \\tag{1}
   \\]

2. Ayşe 2 kg elma ve 4 kg armut aldı ve 70 TL ödedi:
   \\[
   2x + 4y = 70 \\tag{2}
   \\]

---

### Adım 1: (2) numaralı denklemi sadeleştirin

(2) numaralı denklemi 2'ye bölün:

\\[
x + 2y = 35 \\tag{3}
\\]

Şimdi daha basit sistemimiz var:

\\[
\\begin{cases}
3x + 2y = 50 \\quad &(1)\\\\
x + 2y = 35 \\quad &(3)
\\end{cases}
\\]

---

### Adım 2: Çıkarma ile \\(y\\)'yi yok edin

(1) numaralı denklemden (3) numaralı denklemi çıkarın:

\\[
(3x + 2y) - (x + 2y) = 50 - 35
\\]

\\[
3x + 2y - x - 2y = 15
\\]

\\[
2x = 15
\\]

\\[
x = \\frac{15}{2} = 7,5
\\]

Yani elmanın fiyatı **kilogram başına 7,5 TL**'dir.

---

### Adım 3: (3) numaralı denklemi kullanarak \\(y\\)'yi çözün

\\(x = 7,5\\) değerini \\(x + 2y = 35\\) denkleminde yerine koyun:

\\[
7,5 + 2y = 35
\\]

\\[
2y = 35 - 7,5 = 27,5
\\]

\\[
y = \\frac{27,5}{2} = 13,75
\\]

Böylece armudun fiyatı **kilogram başına 13,75 TL**'dir.

---

### Kontrol

- Ali'nin alışverişi: \\(3(7,5) + 2(13,75) = 22,5 + 27,5 = 50\\) TL ✔️
- Ayşe'nin alışverişi: \\(2(7,5) + 4(13,75) = 15 + 55 = 70\\) TL ✔️

Her iki denklem de sağlanıyor.

**Sonuç:**
- Elma: \\(x = 7,5\\) TL/kg
- Armut: \\(y = 13,75\\) TL/kg"""
T['g031'] = """Yeni hiçbir bilgi **katmayan** ipucu **III**'tür: “Ceren, Doruk'un seçtiğinden farklı bir tür seçti.”
Herhangi bir birebir (ikili) eşleştirmede iki farklı öğrenciye aynı tür atanamaz; dolayısıyla türleri otomatik olarak farklıdır. Bu bilgi eşleştirmenin doğası gereği doğrudur ve bu nedenle ek bir kısıt sağlamaz.

**Cevap: C) Yalnızca III**."""
T['g033'] = """Kurala göre, **çünkü** bağlacı iki bağımsız yargıyı birleştirdiğinde **bileşik cümle** oluşturur."""
T['g034'] = """**Vardiya planı (vardiya başına bir çalışan, her çalışan tam olarak bir vardiyaya atanmış)**

| Vardiya   | Atanan çalışanlar |
|---------|-------------------|
| **Gündüz** | Fatma, Hüseyin |
| **Akşam** | Ali, Zeynep |
| **Gece** | Veli, Ayşe |

**Bu neden işe yarıyor**

1. **Vardiya başına en az 1, en fazla 3 çalışan** – her vardiyada tam olarak 2 çalışan var; bu da 1 ile 3 arasındadır.
2. **Ali ve Veli birlikte değil** – Ali Akşam vardiyasında, Veli ise Gece vardiyasında çalışıyor; farklı vardiyalardalar.
3. **Fatma yalnızca Gündüz vardiyasında çalışıyor** – Fatma yalnızca “Gündüz” altında listelenmiştir.
4. **Toplam çalışan-saat ≤ 24** – 6 çalışan var ve her çalışan bir “saat” iş olarak sayılsa bile 6 ≤ 24. (Her vardiya 8 saatlik tam bir gün olsa bile 6 × 8 = 48 saat en fazla olurdu; yalnızca tek günlük çalışmada toplam 6 saattir ve 24'ün çok altındadır.)

Böylece yukarıdaki atama verilen tüm koşulları sağlar."""
T['g035'] = """Toplamda 90 çocuk var.

- %30'unun kilo artışı beklenen düzeyin **üzerinde** idi.
- %50'sinin kilo artışı beklenen aralığın **içinde** idi.

Kilo artışı beklenen düzeyin **altında** olan kalan yüzde:

\\(100\\% - 30\\% - 50\\% = 20\\%\\).

90 çocuğun %20'si = \\(0,20 \\times 90 = 18\\).

Bu nedenle, **18 çocuğun** kilo artışı beklenen düzeyin altındaydı."""
T['g037'] = """1000 eleman için özgün süre \\(0,012\\) saniyedir.
Eleman sayısı 8 ile çarpıldığında (yani 1000'den 8000'e), süre yaklaşık \\(8^2 = 64\\) kat artar (çünkü \\(64 = 8 \\times 8\\)).

Dolayısıyla 8000 eleman için süre:

\\[
0,012 \\text{ sn} \\times 64 = 0,768 \\text{ sn}.
\\]

Böylece algoritma 8000 elemanı sıralamak için yaklaşık **0,768 saniye** harcar.

**Cevap: C) 0,768**"""
T['g038'] = """Evet – bir dikdörtgen hem yatay hem de dikey orta çizgilerine göre simetriktir; bu nedenle dikey orta çizgi boyunca katlamak da iki yarıyı üst üste getirir."""
T['g040'] = """Siz bu tekniği nerede öğrendim?"""
T['g041'] = """Hayır, yalnızca bu ayrıntılara dayanarak kabloyu değiştirmenin sorunu çözeceğini kesin olarak söyleyemezsiniz. Nedeni şu:

- **Işığın yanması**, projektöre (görüntü kartına) güç ulaştığı anlamına gelir, ancak görüntü sinyalinin doğru gönderildiğini garanti etmez.
- Özellikle mevcut kablo eskiyse, hasarlıysa veya yanlış takılmışsa, arızalı bir kablo aralıklı bağlantılara, sinyal kaybına veya parazite yol açabilir.
- Bununla birlikte başka olası nedenler de vardır: bitmiş bir pil, arızalı bir HDMI/DisplayPort girişi, bir sürücü sorunu ya da projektörün kendisinin girişi alamaması.

Kablonun suçlu olup olmadığını doğrulamak için şunları yapmalısınız:
1. Farklı bir kablo deneyin (tercihen sağlam olduğu bilinen bir tane).
2. Sorunun sürüp sürmediğini görmek için aynı kabloyla bağlı başka bir cihazla test edin.
3. Projektörün ayarlarını kontrol edin ve doğru kaynağın ve giriş modunun seçili olduğundan emin olun.

O zamana kadar, bu alternatifler elenmeden yalnızca kabloyu değiştirmek sorunu çözeceğini garanti etmez."""
T['g042'] = """Yedek pilin çalışma süresi: 55 dakika."""
T['g043'] = """Derya lisansüstü eğitime (doktora programı) başvuruyor, Kerem ise doktor olarak çalışmaya başlıyor. Bu nedenle lisansüstü eğitime başvuran kişi Derya'dır.

**Cevap:** Derya."""
T['g045'] = """Yönetim, üretimin **75 bin adet** düzeyinde tutulmasını öneriyor. 90 bin adetlik rakam 2027 satış tahminine işaret ediyor; önerilen üretim düzeyi ise bu tahminden düşük. Dolayısıyla üretim yönetiminin önerdiği adet sayısı 75.000'dir."""
T['g046'] = """Akınspor, Erzurum'da oynanan deplasman maçında Kuzey Birlik'i 4–2 yendi. Belirleyici gol 67. dakikada geldi ve bu galibiyet Akınspor'u lig tablosunda ikinci sıraya yükseltti.

**Özet:** Akınspor, Erzurum'daki deplasman maçında 67. dakikada attığı golün de katkısıyla Kuzey Birlik'i 4–2 yendi ve ikinci sıraya yükseldi."""
T['g047'] = """Galeri tabloyu yalnızca sigorta belgesi teslim edilirse ve nakliye tarihi yazılı olarak onaylanırsa gönderecek; aksi hâlde göndermeyecektir."""
T['g048'] = """Küçük eşyaları (düğme, boncuk, madeni para veya küçük süs eşyaları gibi) seri üretilmiş toplu alımlara başvurmadan bulmak için şu daha sürdürülebilir yaklaşımları deneyebilirsiniz:

1. Önceki sezonlardan veya hediyelerden unutulmuş parçalar için **dolaplarınıza ve çekmecelerinize bakın**.
2. “Küçük buluntular” veya “mikro dekorasyonlar” için eBay, Etsy gibi **çevrim içi pazar yerlerinde** ya da yerel ikinci el mağazalarında arama yapın.
3. **Dijital arşivleri kullanın**: Kaybetmiş veya bağışlamış olabileceğiniz eşyalara dair ipuçları için eski fotoğraflara, e-postalara veya fişlere göz atın.
4. **Mevcut malzemeleri yeniden değerlendirin**: Artan kumaş parçalarınız, cam kavanozlarınız veya eski düğmeleriniz varsa, yenisini almak yerine dekoratif aksesuarlara dönüşebilirler.

Anahtar nokta, büyük mağazaların peşinden koşmak yerine çevrenizdeki mevcut olanı bularak talebi azaltmaktır. Bu, ambalaj atığını azaltır ve mevcut eşyaların döngüsel kullanımını destekler."""
T['g049'] = """Evet, teslimat adresi olarak iş yerinizi seçmelisiniz. Gün içinde evde kimse olmadığı ve iş yerinizin resepsiyonu akşama kadar açık olduğu için, kargoyu sizin adınıza teslim alıp saklayabilirler. Bu, kapınızda birinin bulunmasına gerek kalmadan paketin güvenle ulaşmasını sağlar. İsterseniz, paketi bir meslektaşınıza bırakmalarını veya akşam bir komşunuzun alması için ayarlama yapmalarını da isteyebilirsiniz."""
T['g050'] = """Leke için kullanılan sözcük **kir**'dir."""
