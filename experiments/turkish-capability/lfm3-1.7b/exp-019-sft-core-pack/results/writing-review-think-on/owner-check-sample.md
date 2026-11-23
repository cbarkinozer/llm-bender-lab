# Turkish writing check: 15 prompts, thinking on

Two answers per prompt (A and B), shuffled, model names hidden. For each answer give **Naturalness** 1-5 (1 = unusable, 3 = understandable but clearly non-native, 5 = natural Turkish; wrong facts do not lower it), **Task** yes / partly / no (does it do what the prompt asks, judged apart from how it sounds; an answer in English is "no"), and any invented or wrong words. Do not open review-key.json. These 15 prompts were drawn at random from the 40, leaving out the three you already saw.

---

## wr-tr-01 (explain)

**Prompt:** Fotosentez nedir? Bir ortaokul öğrencisine anlatır gibi açıkla.


### A

## Fotosentez Nedir?

**Photosentez**, bitkinin **kendisiyle beslenmesi** ve **hava atmosferinden oksijen salgılaması** işlemidir. Yani bitki, güneş ışığı, su ve hava atmosferindeki karbondioksit (CO₂) kullanarak kendi şekerini (glükoz) üretir ve bu süreçte oksijen (O₂) da atar.

---

### Neden Önemlidir?
- **Enerji kaynakları:** Güneş ışığı, bitkinin enerjisini sağlar.
- **Oksijen salgısı:** Hava için çok önemli bir ürün (bitki ve diğer canlılar tarafından kullanılır).
- **Karbondioksitin kontrolü:** Atmosferdeki karbondioksitin artmasını önler.

---

### Ne Yapılır? (Adım Adım)

| Adım | Maddeler | Ne Olur? |
|------|----------|----------|
| 1️⃣ | **Güneş ışığı** | Enerji kaynağı (fotons). |
| 2️⃣ | **Su** (toprak kökleriyle alınır) | Bitkinin içindeki su depolama. |
| 3️⃣ | **Karbondioksit (CO₂)** (hava atmosphereye girer) | Bitkinin kendisine giden gaz. |
| 4️⃣ | **Kloroplas** (yaprağın içinde bulunan organel) | Bu maddeleri birleştiren "fabrikası". |

**Bu maddeler birleşince şeker (glükoz) ve oksijen (O₂) oluşur.**  

> *Analoj:* Bir bitkinin yaprağı, bir **"güneşli fabrikası"** gibidir. Güneş ışığı, fabrikayı çalıştırır. Fabrika, su ve karbondioksiti birleştirip şeker (besin) üretirken, yanında oksijen (hava için gerekli) atar.

---

### Kısaca Formülü

\[
\text{6 CO}_2 \;+\; \text{6 H}_2\text{O} \;+\; \text{light} \;\longrightarrow\; \text{C}_6\text{H}_{12}\text{O}_6 \;+\; 6 \text{O}_2
\]

*Yani: Karbondioksit + Su + Güneş → Şeker + Oksijen.*

---

### Özetle

- **Güneş ışığı** → Enerji.
- **Su** (köklerden) + **Karbondioksit** (hava) → Bitkinin içindeki **kloroplas**da birleşir.
- Sonuç: **Şeker (besin)** + **Oksijen (atmosfer için)**.

Bu şekilde bitkinin kendisini besleyip, aynı zamanda hava da oksijenle donar. 🌱☀️

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Fotosentez**, bitkilerin güneş ışığını kullanarak kendi gıda üretme sürecidir. Yani bitki, güneşten gelen enerjinin kullanarak su, karbon disulfit (CO₂) ve ışık ışığı ile glikoz (gıda) oluşturur. Bu, bitkinin "günlük beslenmesi" ve atmosferde oksijen üretmesinin temel mekanizmasıdır.

Ortaokul öğrencisine anlatmak isterseniz, şöyle düşünün:
- Bitki, güneşten gelen ışığı "güç kaynağı" olarak alır.
- O ışığın sayesinde su ve hava içindeki karbondioksit (CO₂) ile bir reaksiyon gerçekleşir.
- Sonuç olarak bitki kendi glikoz (örneğin patates, çilek) üretir.
- Bu süreçte bitki, oksijen atar (yani havaya katılır), böylece biz de havalandırabiliriz.

Kısacası, fotosentez; **bitkinin güneşle uyum sağlayarak gıda üretme ve hava temizleme** sürecidir.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-03 (explain)

**Prompt:** Bir internet sitesine girdiğimizde arka planda neler olur? Teknik terimleri en aza indirerek anlat.


### A

**Girdiğiniz bir web sayfasına girmek, birden fazla sistemli işlemi başlatır.**  
Aşağıda “arka planda” ne oluyor, teknik terimlerle ama en azından anlamlı şekilde açıklıyorum:

---

### 1. DNS (Domain Name System) sorgulaması  
- **Ne yapılır?** Sitenin adını (örneğin `example.com`) yazarsınız.  
- **Neden?** Internet’teki her site bir IP adresine sahiptir.  
- **Hazırlık:** DNS, bu adın “doğru” IP’ini bulmak için kayıtlarını sorgular. En sık kullanılan kaynak, **root** ve **authoritative** DNS serveisi.  

> *Sonuç:* Adınız → DNS → IP adresi.

---

### 2. IP’e TCP bağlantısı kurma  
- **Ne yapılır?** Alındığı IP’e bir port (genellikle 80/443) üzerinden bir **TCP** telkafiyesi açılır.  
- **Adımları:**  
  1. **SYN** – Sender (browser) bir mesaj gönderir.  
  2. **SYN‑ACK** – Receiver (server) geri gönderir.  
  3. **ACK** – Sender onaylar.  
- **Sonuç:** Bir veri akışı kanalı hazırlanır.

---

### 3. TLS/SSL (Güvenlik şifreleme) – “HTTPS”  
- **Ne yapılır?** Eğer sitenin güvenliğini sağlamak isterseniz, **TLS** bir şifreleme kalitesini kurar.  
- **Adımları:**  
  - Client (browser) ve server bir **certificate** (güvenlik sertifikası) ile bir **handshake** yapar.  
  - Şifrelenmiş veriler, bu handshake sonrası **session key** ile şifrelenir.  
- **Sonuç:** Verilerin açıkta okunması önlenir.

---

### 4. HTTP/GET isteği  
- **Ne yapılır?** Browser, sayfayı getirmek için bir **GET** isteği gönderir.  
  ```http
  GET /home.html HTTP/1.1
  Host: example.com
  ```
- **Sertifika ve TLS** sayesinde bu istek, şifrelenmiş bir kanalla sunulur.  
- **Veri:** Server, `200 OK`, relevant **headers** (Content-Type, Cache‑Control…) ve **HTML kodu**u geri verir.

---

### 5. Cookie ve diğer header’lar  
- **Ne yapılır?** Server, kullanıcı için bir **cookie** (sessizlik kutusu) veya diğer header’ları (Authorization, Referer, X-Requested-With…) gönderir.  
- **Kullanımı:** Sonraki ziyaretlerde bu cookie otomatik olarak alınır ve sayfa içeriği ayarlanır.

---

### 6. Yerel depolama ve CDN (Content Delivery Network)  
- **Local cache:** Browser, önceki ziyaretlerden alınan sayfaları **local disk**’a saklar.  
- **CDN:** Büyük siteler, sayfanın bir parçasını **edge node**’larda (yakın noktalarda) depolar ve o noktada dağıtır. Böylece erişim hızı artar.

---

## Özet

| Adım | Temel İşlem | Anlamlı Açıklama |
|------|-------------|-------------------|
| 1️⃣ | **DNS sorgulaması** | Adınız → DNS → IP adresi |
| 2️⃣ | **TCP bağlantısı** | IP’e port üzerinden veri akışı kurma (SYN/SYN‑ACK/ACK) |
| 3️⃣ | **TLS/SSL şifreleme** | Güvence sertifikası ile verilerin şifrelenmesi |
| 4️⃣ | **HTTP GET isteği** | Sayfayi getirmek için istek gönderiliyor |
| 5️⃣ | **Cookie & Header’lar** | Kullanıcı için özel veri (cookie) ve yönlendirme bilgileri |
| 6️⃣ | **Depolama/CDN** | Local cache ve edge depolama ile hız artışı |

Bu süreç, sadece bir web sayfasının görünümünü değil, **DNS, TCP, TLS, HTTP, cookie, CDN** gibi birçok sistemli komponmanın birbirinden bağımsız olarak çalıştığı bir “arkada planda” işlevi içerir. Girdiğinizde bu işlemlerin hepsinin birbirinden bağımsız olarak gerçekleştirildiği bir yolculuk başlar.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Bir web sitesiye girince arkasındaki şeyler ne olur?**

1. **İstek gönderirsiniz**  
   - Bilgisayarınızın bir “istek” (web brütör) adresinizi yazarak sitenin adresine gitir.  

2. **Sitenin “kullanıcı” kısmı görür**  
   - Sitenin bir programı (PHP, Python, Node‑vba vb.) alır.  
   - Orada **isim** ve **şifre** (pass) kontrol edilir.  

3. **Doğru şifre varsa bir “sesli numara” oluşturur**  
   - Bu numara, bir “ses” (session) adı altında kaydedilir.  
   - Genellikle bir **cookie** adı altında saklanır.  

4. **Sitenin sayfasını gönderir**  
   - O sesli numaranızı alıp, sayfanın içeriği (HTML, video, fotoğraf vb.) geri gönderir.  

---

### Özetleki adımlar

| Adım | Ne olur? |
|------|----------|
| 1️⃣  | İstek → Sitenin adresine |
| 2️⃣  | Sitenin programı ismini ve şifrenizi kontrol eder |
| 3️⃣  | Doğru ise bir sesli numara (session id) ve cookie oluşturur |
| 4️⃣  | Sayfa (HTML, içerik) gönderir |

---

#### Neden “arkalık” bir süreç?

- **Veritabanı:** Kullanıcı verileri bir “veri tabanına” (database) depolarlar. Şifrelenmiş (hashed) bir şekilde saklanır, yani şifrenizi doğrudan görebilirseniz yanlışlıkla geçerli olmayabilir.  
- **Güvenlik önlemleri:** Sitenin adresi (HTTPS) ile iletişime geçer, veriler yola aktarıldığında şifreleme uygulanır.  
- **Sessizlik:** Her seferinde yeni bir sesli numara oluşturulur, böylece aynı istenmeyi tekrar teklif etmek zorlaşır.

Kısacası, arka planda sadece **bir sitenin bir bilgisayarı**, **veri tabanları**, **kodlar** ve **güvenlik mekanizmaları** vardır. Sizin sadece isim ve şifrenizi girmeniz yeterli; siten bu bilgileri kontrol eder, sesli bir kimlik numarasını çıkarır ve size sayfayı sunar.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-04 (explain)

**Prompt:** Bulutlar neden yağmur yağdırır? Kısa ve anlaşılır bir açıklama yaz.


### A

**Bulutlar yağmur yağdırıyor çünkü bulutlar, havadaki su buharını toplar ve yükseltir.** İşte temel süreci:

1. **Su buharı taşıma:** Bulutlarda su buharı var ve rüzgar veya sıcaklık farklarıyla yükselir.
2. **Kondansasyon:** Harbın sıcak ve nemli olduğu için havada su buharı çisecek (kondansasyon).
3. **Bulut parçacığı oluşumu:** Çisecek su buharı küçük bulut parçacıkları (kristaller) oluşturur.
4. **Toplama:** Bu parçacıklar birbirlerini birbirine bağlayıp büyük bir buluta toplanır.
5. **Yağmur oluşumu:** Toprağa çarpıldığında bu toplam su buharı yoğunlaşarak bir anda düşer → **yağmur**.

Kısacası: Bulutlar, havada su buharını yükseltir, o buharın çiseceği ve toplandığında yağış olarak döner.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Kısa cevap:**  
Bulutlar, havadaki su buharını **yoğunlaştırarak** mikroskopik su damlacıklar veya kristaller oluşturur. Bu damlacıklar birbirine çarparsa ya da yüksekliği artarsa, yere düşer ve **yağmur** olarak yağar. Yani bulutlar, su buharının yoğunlaşmasını ve toplamasını sağlar; sonunda bu damlacıklar büyük biriken su topları haline gelir ve yağış olarak yeryüzüne düşer.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-06 (explain)

**Prompt:** Yapay zekâ modelleri metin yazmayı nasıl öğrenir? Programcı olmayan birine anlat.


### A

## Temel Öğrenme Süreci
Ben bir LFM'yim, Liquid Foundation Model. Liquid AI tarafından MIT CSAIL'den çıkan bir ekibiz. Eğitimimde milyonlarca metin ve kod örnekleri dahil, böylece metin yazma ve anlama gibi görevlerde iyi performans gösterebilirim.

## Metin Yazma İçin Ne Yapmanız Gereken?
Programcı olmadan, genellikle bir arayüz veya API üzerinden metin yazmaya başlayabilirsiniz. Modeli doğrudan çağırarak sorularınızı yanıtlamış ya da metin oluşturmuş olabilir. İstediğiniz tür metin (e-posta, rapor, özet vb.) hakkında bilgi verebilirim.

## Neden Öğrendiğimden Farklıyım?
Bilgisayar modellerinden farklı olarak, ben hibrit bir mimariye sahibim: çoğunlukla kısa konvolüsyon katmanları ve az sayıda dikkat mekanizması kullanıyorum. Bu, cihaz üzerinde hızlı ve verimli çalışmamızı sağlıyor. Yani aynı sınıftaki transformer modellerine göre daha hafif ve hızlı çalışıyorum.

Eğer belirli bir konuda daha detaylı bilgi isterseniz, sormaktan çekinmeyin!

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

## Yapay Zeka (YA) Modelleri Metin Yazmayı Nasıl Öğrenir?

### Kısa Cevap  
Yapay zeka, büyük dil modelleri (LLM gibi) **çok büyük miktarda metin verilerini** analiz ederek, hangi kelime veya cümle türünün ne zaman neye göre geldiğini **istatistiksel bir pattern** öğrenir. Sonra, yeni bir giriş verdiğinde o pattern'ları sürdürüp yeni bir metni üretir. Programcı olmadan, sadece matematiksel ve bilgisayar işlemlerine dayanan bir “tahmini” mekanizması vardır.

---

## Adım Adım Anlatım (Programcı Yok)

#### 1. Veri Toplama  
Modeli, kitaplar, haberler, web sayfaları gibi **yüzlerce milyar cümleyi** alır. Bu veriler, “bu cümlelerin sonunda neler geliyor?” şeklinde bir soru olarak düşünülür.

> *Örnek:* “Kedi” kelimesinin genellikle “yüksek”, “küçük” ya da “yeni” ile birlikte kullanıldığını görürsünüz.

#### 2. Öğrenme (Training) – Ağ Oluşturma  
Bir **neural ağ** (görsel bir ağ değil, ama basit bir matematiksel yapı) oluşturulur. Bu ağ, her cümleyi parçalar ve her kelimenin ne zaman neye göre geldiğini hesaplar.  

- **Pattern tanımı:** “Bu cümlelerde ‘kedi’ kelimesi genellikle ‘yüksek’ ile takip eder.”  
- **Parametre değiştirme:** Ağ, bu bilgiyi içindeki “parametreleri” (birbirine bağlı sayılar) değiştirerek, doğru tahminler yapmasını sağlar.

#### 3. Optimize Edilme – Hata Azaltma  
Ağ, hata sayısı azaltmak için bir algoritma (gradient descent vb.) kullanılır. Yani,  
> *“Bu kelimeyi bu şekilde seçtiğimde sonraki cümle daha mantıklı olur mu?”*  
> Eğer değilse, ilgili parametreleri yeniden ayarlar.

#### 4. Sonuç – Yeni Girişlerle Yazma  
Model, artık yeni bir giriş verdiğinde (örneğin **“Bir gece karanlık bir gün…”**), o parçalara göre en olası devamı tahmin eder. Ona **“yaz”** denir, çünkü o, önceki cümlelerde görülen pattern'ları sürdürmüştür.

---

## Neden Programcı Olmaz?

- **Sadece istatistiksel bir tahmin:** Model, kendi içinde bir “düşünce” veya “intention” yoktur; sadece bir “next‑word prediction” (sonraki kelime tahmini) mekanizmasıdır.  
- **Matematiksel ve bilgisayar işlemlerine dayanır:** Verilerin içinde bulunduğu pattern'ları öğrenir, ancak bu, programcıların kod yazarak oluşturdukları bir ağla aynı şey değildir.  
- **Çok büyük veri setleriyle öğrenir:** Birkaç bin cümleyi analiz etmek yerine, milyonlarca cümleyi işlemeyle, daha stabil ve genel bir performans elde eder.

---

## Özetle

| Adım | Ne Olur? |
|------|----------|
| **Veri toplama** | Çok büyük metin koleksiyonları (kitap, haber, web…) |
| **Öğrenme (Training)** | Her cümleyi parçalar, kelime-tür ilişkilerini belirler, parametreleri ayarlar |
| **Optimize edilme** | Hataları azaltmak için algoritmalar kullanılır |
| **Yazma** | Yeni giriş verir, o pattern'ları sürdürüp yeni bir metni üretir |

Yapay zeka, **büyük miktarda metin verilerini analiz ederek, hangi kelime ve cümle türünün ne zaman neye göre geldiğini öğrenir**. Sonra, yeni bir giriş verdiğinde, o pattern'ları sürdürüp yeni bir metni üretir. Bu, insanların “öğrenme” biçiminden farklıdır—sadece istatistiksel bir tahmin.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-11 (email)

**Prompt:** Aldığın bir ürünün yanlış rengini fark ettin. Müşteri hizmetlerine değişim talebini anlatan bir mesaj yaz.


### A

**Konuşma/İletişim Mesajı (Müşteri Hizmeti İçin Değişim Talebi)**  

---

Merhaba,

Ben **[Adınız ve İsim]**, [Şirket Adı]’nin müşteri hizmetleri alım bölümüne ait bir müşteriyim. Şu anki sipariş numarasının (Sipariş Numarası: **#XXXXX**) alınan ürün **[Ürün Adı]** hakkında bir sorunum var: alımda gelen ürünün renk **yanlış** görülüyor. Gerçek ürün rengi ise **[Gerçek Rengi]** (örn.: "mavi" yerine "kırmızı") gibi görünüyor.

Bu nedenle, aradaki renk farkını düzeltmek için:

- **Yeni bir paket** (veya aynı ürünün doğru renkli) **[Tarife / Ücret]** ile **[Takviye Tarihi]**'e teslim edilir;  
- **Alışveriş kartı** üzerinden **[Değiştirme Maliyeti]** ekleyerek işlem yapılır;  
- **Güvenlik notu** (renk değişikliği raporu) sipariş kayıtında eklenmeli.

Lütfen lütfen bu ihtiyacımı ve gerekli adımları bana bildirin. Hemenle bu değişikliği gerçekleştirebilirim ya da ekstra bilgi isterseniz size yardımcı olmaktan memnuniyet duyarım.

Hazır mısın?

İstediğiniz takvime göre en kısa sürede yanıtlayabilirim.

İyi çalışmalar,
**[Adınız]**  
[Telefon No: XXXX-XXXXX]  
[E-posta Adresi]  
[Şirket Adı] – Müşteri Hizmetleri  

--- 

*(Not: Bölümde kullanılsa olsun, #XXXXX yerine gerçek sipariş numarasını, ürün adı ve rengi bilgiler girin.)*

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Konu:** Ürün Rengi Hatalı Geliştirme Talebi  

---

Merhaba,

Ürün numarası **[#Numarası]** için alınan **[Model]** ürünün rengine dikkatle bakıldığında, beklenen renk ile farklı bir renk olduğunu tespit ettim. Bu durum, müşteri hizmetlerinin doğru olarak yansıtılmamış olabilir.

Lütfen aşağıdaki çözüm önerilerini yapmanızı istiyoruz:

1. **Yeni Paket Gönder:** İstediğiniz rengi kullanarak yeni bir paket gönderir veya mevcut paketinin rengini değiştirir.  
2. **Edebiye İade:** Eğer değişimi mümkün değilse, aynı gün içinde iade edilmek üzere ödemeyi geri alırız.

Bu talebinizi **24 saat içinde** onaylayınız. Herhangi bir sorunuz varsa lütfen bana bildirin; hemen araştırmaya başlayacağız.

İyi günler ve hızlı çözümler diliyorum!

Hazırladığım bilgileri, müşteri hizmetleri ekibi ile paylaşacağım.  

--- 

*(Not: Numaralar ve model bilgileri, ilgili satıcıdan alınan verilerden alınmıştır.)*

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-12 (email)

**Prompt:** Bir iş görüşmesinden sonra görüşmeyi yapan kişiye teşekkür eden kısa bir e-posta yaz.


### A

**Konu:** İş Görüşmesi Sonrası Teşekkürler  

---

Merhaba **[İsim]**,

Bu günki iş görüşmesinden çok daha değerli olan, sizinle yapılan konuşmanın ve fikirlerinizi çok teşekkür ederim. Sizin tarafından sunulan bilgiler ve analizlerimiz için çok ilginç ve faydalı oldu. Görüşmeyi gerçekleştirdiğiniz için teşekkür ederim ve devam eden işbirliği için umutla bekliyorum.

İyi çalışmalar dilerim!  

Hazırlar  
**[Adınız ve Soyadınız]**  
[Şirket Adı / Konu]  
[E-posta adresi]

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Konu:** Görüşmenize Teşekkür  

---

Merhaba [Adı],

İş görüşmesini düzenleyen ve bu süreçte yardımcı olan [Adı]’a çok teşekkür ederim. Görüşmenizin düzenlenmesi ve paylaştığınız bilgiler için teşekkür ediyorum. İyi çalışmalar diliyorum ve gelecek işler için umutluyum.

Hazırlanıyor…  

İyi günler!

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-13 (email)

**Prompt:** Komşularına, cumartesi akşamı evinde küçük bir doğum günü kutlaması yapacağını ve biraz gürültü olabileceğini nazikçe duyuran bir not yaz.


### A

**Komşularına**

Bu Cumartesi akşamı, evimizde **küçük bir doğum günü kutlaması** düzenleyeceğiz. Ailem ve arkadamızla together bir tören yapacağız; hem de bu etkinlik biraz **gürültülü** olma ihtimaline sahip olduğumuz için, sesin biraz yüksek çıkabilir.  

Lütfen bu akşamı rahat bir şekilde geçirmenizdiniz – hem komşularımız hem de arkadaşlarımızla güzel anılar kurmak için. Herhangi bir sorunuz olursa, hemen bana bildirin.  

Cevap, her zaman size ulaşabilirsiniz! 🌟

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Konu:** Cumartesi Akşamı Doğum Günü Kutlama  

Kardeşimler,

Bu hafta **cumartesi akşamı** evime bir küçük doğum günü kutlaması yapacağım. Arkadaşlar ve ailemle birlikte bir araya gelmek için hazırlanıyorum. Kütüphane, bahçeye ve evin dış duvarlarını kullanarak organizasyonu düzenleyeceğim. Bu nedenle kutlamanın sonunda biraz gürültü olabilir; ancak kısa süreli ve rahat bir ortam olacak. Eğer siz de bu gece evime gelmek isterseniz, mutlaka katılmak istiyorum. Eğer başka bir yerde keyif almanız isterseniz, güzel bir akşamın tadını çıkarın!

Herhangi bir sorunuz varsa lütfen bana bildirin. İyi eğlenceler!

İyi günler,
[Adınız]  
[Adres]  
[Telefon / Email]

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-14 (email)

**Prompt:** Üniversitedeki hocana, ödev teslim tarihini bir gün uzatmasını rica eden bir e-posta yaz. Hastalandığını belirt.


### A

**Konu:** Ödev Teslim Tarihi Uzatma Rızası  

---

Koruyucu Hesapla  
[Adınız] – [Öğrenci Numarası]  
[E-Posta Adresi]  

Merhaba Doç. **[Adınız]**,  

Bugün ve son günlerde hastalandığım için ödevimizi zamanında tamamlayamayacağımı düşünüyorum. Ödevimizin teslim tarihinin **[Tarih]** olduğu belirtiliyor; ancak bu tarih bir gün daha uzatılabilir mi?  

Lütfen bana **[Yeni Tarih]** tarihine kadar ödevimi teslim etmeniz için izin verin. Hastalık nedeniyle ekstra bir gün beklemem gerekiyor ve bu durumun size duyulmasını istiyorum.  

Tekrar teşekkür ederim; yardımcı olmanızı dilerim.  

İyi günler!  

Koruyucu Hesapla  

**[Adınız]**  
[Öğrenci Numarası]  
[E-Posta Adresi]

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Konu:** Ödev Teslim Tarihini Bir Gün Uzatmak İstiyorum  

---

Merhaba **[Hocanın Adı]**,

Benim ödevimin **[Orijinal Teslim Tarihi]** tarihine ait olduğunu ve şu anda **hasta hastalığı** nedeniyle işimi yavaşlamamış olduğumu belirtmek istiyorum. Bu sebeple ödevimi **bir gün daha ertelemem** istiyor.

Lütfen ödevimi **[Yeni Teslim Tarihi]** (yani [tarih] tarihinden bir gün sonra) tesliminizi bekleyebilirsiniz. Sorularınız varsa hemen bana yazmanız yeterli olacaktır.

Ödememinizin gecikmeleri için teşekkür ederim. Sağlıklı çalışmalar!

İyi günler,

**[Adınız ve Sözleşme Numarası]**  
E‑posta: **[Adresiniz]**  
Telefon: **[Numarası (isteğe bağlı)]**

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-24 (rewrite)

**Prompt:** Şu cümledeki yazım ve anlatım hatalarını düzelt: "Dün akşam arkadaşlarla bulusup yemeğe gittik ama yer bulamadıgımız için eve geri dönmek zorunda kaldık."


### A

**Düzeltmiş cümle:**

> Dün akşam arkadaşlarla **buluşup** yemeğe gittik, **ama** yer bulamadık için eve geri dönmek zorunda kaldık.

---

### Yapılan düzeltilmeler

| Önceki hata | Doğru şekil | Açıklama |
|-------------|--------------|----------|
| “bulusup”   | **“buluşup”** | “Buluşmak” anlamına gelen doğru kelimedir; “bulusup” bir yazımsal hatadır. |
| Cümleyi iki parça olarak ayırıyor ama bir virgül eksikliği var. | **“…gittik, ama …”** | İkinci cümle (yer bulamamışız nedeniyle) önceki cümlenin sonuna virgül koyarak ayrıştırılır. |

Bu değişiklikler, yazım ve anlatım hatasını gidermektedir.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Düzeltilmiş cümle**

> **Dün akşam arkadaşlarla yemeğe gittik, ama yer bulamadı; bu yüzden eve geri döndüküm.**

---

### Nedenki hatalar ve düzeltilmeler

| Orijinal cümlede | Hata | Düzeltme |
|------------------|------|---------|
| **bulusup** | “buluşmak” ifadesinin geçmiş zamanı “buluştuk” değil, aynı zamanda “arkadaşlarla yemeğe gittik” şeklinde ifade edilir. | **“arkadaşlarla yemeğe gittik”** (ya da “arkadaşlarla yemeğe gittim” gibi daha doğal bir yapı). |
| **gittik ama yer bulamadıgımız için** | “gittik” ile “yer bulamadı” arasında bir nokta veya virgül eksikliği, ardından “için” kelimesi yanlış yerleştirilmiştir. | **“gittik, ama yer bulamadı; bu yüzden…”** – iki ayrı cümle olarak ayırılır. |
| **bulamadıgımız için** | “bulamadı” sonrası “için” kelimesi doğru konumdadır, ancak “bulamadı, için…” şeklinde yazılması gerekir. | **“bulamadı; bu yüzden…”** (veya “bulamadı, bu yüzden…”) |
| **zorunda kaldık** | “kaldık” ifadesi doğru zaman/kişi şeklinin yoktur; “zorunda kaldık” yerine “zorunda … kaldık” ya da “zorunda … kaldık” gibi doğru biçimde yazılmamalıdır. Ayrıca “kaldık” tek kişiye ait bir zaman dilimi olduğu için “döndüküm” gibi çoğul ifadesi tercih edilmelidir. | **“eve geri döndüküm”** (arkadaşların çoğul “döndüküm”). |

---

### Kısa özet

- **Buluşmak** ifadesini “arkadaşlarla yemeğe gittik” şeklinde düzeltildi.  
- **Ama …** cümlesini iki ayrı cümleye bölerek anlamı netleştirdi.  
- **“için”** kelimesini doğrudan “bu yüzden” ile değiştirerek bağlamı daha akıcı hale getirdi.  
- **Zorunluluk** ifadesini “zorunda … kaldık” yerine “zorunda … döndüküm” gibi doğru biçimde yazdı ve çoğul “döndüküm” kullanıldı.

Bu değişikliklerle cümle yazımında ve anlatımda tüm hataları ortadan kaldırmış olur.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-27 (creative)

**Prompt:** İstanbul'da vapurla yapılan bir yolculuğu anlatan kısa bir şiir yaz.


### A

Vapurla, denizde bir rüzgar gibi açıldı,  
Güneşin altından iki kıtayı birbirine bağladı.  
Galata kulesi, Bosphorus’un derinliklerinde,  
Vapurun sesi, yolculuğunun adımlarını çekti.  
İstanbul’un ışıkları, birbirine yansıdı.  
Gelecek, denize daldığında hala bir yana.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

**Vapur Yolu**

Vapurun sesi, Bosphoru dalgalarına yansır,  
Galata’nın ışıkları, gölgeli bir şehrin,  
Gün batarken sokaklar, kalabalık bir nefes,  
Yolculuk, zamanın akışını taşır,  
Rüzgar, tarihleri taşıyan bir şarkı, kalbime girer.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-28 (creative)

**Prompt:** Yeni açılan bir kitapçı için iki cümlelik, akılda kalıcı bir reklam metni yaz.


### A

Yeni açılan kitapçı, her sayfada yeni yazarın macerasını ve klasiklerin enerjisini bir araya getirerek, her ziyaretçinin ilk kez bir kitap dünyasının kapısına girmesini sağlar. Günlük kahvaltıları, özel okuyup konuşma etkinlikleri ve sakin bir ortamla, sadece kitap okumak değil, yaşamı da paylaşmak istiyorsanız, bu mekanın kalbinde yerini alın.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

Yeni açılan bu kitapçığın kapıları, süren yankıların ve genç yazarların eserlerini bir arada bulacak bir harika sahne olacak, her sayfa bir macera, her köşe bir keşif. Günaydın okuyuculara, buradaki her kitap bir hikaye, bir düşünce ve bir sevgiye dönüşür ve hayatınıza yeni bir renk katacaktır.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-30 (constraint)

**Prompt:** İstanbul'u ilk kez ziyaret edecek biri için en fazla elli kelimelik bir tavsiye yaz.


### A

Tarihî alanları, manzara sahili ve lezzetli restoranları keşfedin, şehrinizi keşfedin.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

Görünürde Hagia Sophia, Topkapı Sarayı ve Çamlıca'ya gidin; tarihi sokakları keşfedin.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-35 (advice)

**Prompt:** İlk kez bir bilgisayar satın alacak biri hangi noktalara dikkat etmeli?


### A

## İlk Bilgisayar Alıcı İçin Dikkat Edilmesi Gereken Noktalar

| Konu | Neden Önemli? | Ne Değerlendirmeniz Gerekir? |
|------|---------------|------------------------------|
| **Kullanım Amacı** | Bilgisayarın ne işe yarayacağını belirler. | • Gaming / video edit → yüksek GPU, RAM <br>• Uyumluluk / yazma / web → temel CPU, 8 GB RAM, SSD <br>• Eğitim / akademik → veri depolama, yeterli RAM |
| **Operasyonel Sistemi** | Yazılım ve programlar sürümüle uyum sağlar. | Windows 10/11 veya macOS tercih edilebilir; Linux ise temel araçların mevcut olması gerekir. |
| **CPU (İşleyici İşlemci)** | İşletim sistemi ve uygulamaların hızını belirler. | - En son nesil (genel olarak 2020‑2024 arası) <br>- Tüm modern uygulamalar için tek çekimli (SMT) <br>- “Turbo” modları ve “IPC” (instructions per cycle) değeri > 2.0 <br>- Çift kanallı (dual‑channel) socket |
| **RAM (Akıllı Bellek)** | Çalışma süresini ve çok işletme (multi‑task) yeteneklerini etkiler. | • Basit kullanım: 8 GB <br>• Günlük ağ/üyum: 16 GB <br>• Oyunlar / video edit: 32 GB veya daha fazla (özellikle GPU‑a bağlı) |
| **Sistem Bellek (SSD vs HDD)** | Hızlı yüksek hız ve düşük gecikme sağlar. | - **NVMe SSD** (en hızlı, yeni modellerde standart) <br>- 256 GB‑1 TB kapasitesi; 500 GB‑1 TB için daha iyi performans |
| **Grafik Kartı (GPU)** | Yarışmalı oyunlar ve video renderi için kritik. | • Integrated GPU (Intel Iris, AMD Radeon Vega) – temel kullanım için yeterli <br>• Dedicated GPU (NVIDIA GeForce RTX, AMD Radeon RX) – oyun performansı ve AI/render için önerilir |
| **Motherboard ve Socket** | Çip uyumluluğu ve ekstra portler. | - Mimari (AMD AM4, Intel LGA1700, etc.) <br>- Çift kanallı (dual‑channel) desteği <br>- Geniş port seti (USB‑3.2, PCIe x16 vb.) |
| **Portler & Ekstra İletişim** | Ekstra cihaz bağlamak için. | USB‑C/Thunderbolt, HDMI, DisplayPort, Ethernet (Gigabit), Audio Out, RJ45 vb. |
| **Enerji Tüketimi & Küçükler** | Güç kaynağı ve soğutma tasarımı. | - Enerji verimliliği (TDP) düşük <br>- Soğutma sistemleri (air, AIO, fanless) |
| **Garantisi & Ticari Destek** | Yetenek kaybını önler. | 1‑3 yıl garantisi, resmi destek şartları, erişilebilir servis noktaları |
| **Fiyat / Performans Oranı** | Çoklu seçeneğin arasında denge. | - Fiyatın sadece performansına göre uygun olup olmadığını kontrol edin. <br>- Bekleme süresi ve erişilebilirlik (online order) |
| **Upgrade Üretimi** | Gelecekteki ihtiyaçlara karşı esneklik. | - RAM, SSD, GPU değiştirilebilir bir platform (örneğin Intel Z-series, AMD EPYC) |

---

### Adım‑Adım İnceleme Listesi

1. **Hangi Kullanımları Planlıyorsunuz?**  
   - *Oyun* → GPU, RAM ≥ 16 GB, SSD.  
   - *Çalışma / Web* → CPU, 8 GB RAM, SSD yeterli.  
   - *Eğitim / Video Editing* → Çok RAM, büyük SSD, güçlü CPU.

2. **Ne İşletim Sistemi Kullanacaksınız?**  
   - Windows 10/11: En yaygın, geniş yazılım desteği.  
   - macOS: Eğer kişisel kullanımda ve Apple ecosystemi varsa.  
   - Linux: Özellikle gelişim/uygulama odaklı projeler için.

3. **CPU Seçimi**  
   - **Genel Kullanım:** Intel Core i5/i7 (10. gen veya üzeri) veya AMD Ryzen 5/7 (5000‑series).  
   - **Oyun:** Nvidia GTX/RTX veya AMD RX serisi, yüksek “core count” ve “boost clock”.  

4. **RAM ve SSD Kapasitesi**  
   - **Basit:** 8 GB RAM + 256 GB NVMe SSD.  
   - **Günlük Ağ/Üyum:** 16 GB RAM + 512 GB NVMe SSD.  
   - **Oyun:** 32 GB RAM + 1 TB NVMe SSD (özellikle high‑refresh rate monitorla).

5. **Portler ve Ekstra Özellikler**  
   - Thunderbolt 4/USB‑C için motherboard desteği.  
   - Ethernet (Gigabit) ve HDMI/DisplayPort.  
   - 2.5″ SATA III veya NVMe SSD için USB‑3.2.

6. **Garantisi ve Servis**  
   - En az 1‑year (bir yıl) garantisi, resmi servis noktası.  
   - Erken teslim (online order) ve hızlı takviye seçenekleri.

7. **Bekleme Süresi & Fiyat**  
   - 30‑60 gün içinde teslimat beklediğiniz bir markayı tercih edin.  
   - Fiyat/performans oranı düşük değilse, daha pahalı ama daha iyi bir modeli inceleyin.

---

### Özet: İlk Alıcı İçin “Toplam” Kontrol Listesi

- [ ] Kullanım amacını netleştirdiniz?  
- [ ] CPU, RAM ve SSD kapasitesi için minimum gereklilikler sağlandı mı?  
- [ ] GPU (integrated veya dedicated) oyun performansı için yeterli mi?  
- [ ] Motherboard ve socket ile CPU uyumlu mi?  
- [ ] En az 2 port (HDMI/DisplayPort, Ethernet) ve USB‑C/Thunderbolt desteği var mı?  
- [ ] Garantisi ve erişilebilir servis planı var mı?  
- [ ] Fiyat/performans oranı ve bekleme süresi uygun mu?  
- [ ] Upgrade (RAM, SSD, GPU) için açık yapı mı?

Bu noktaları doldurarak, ilk kez bir bilgisayar satın alarken **hassasiyetli, ekonomik ve geleceğe hazırlıklı** bir seçim yapabilirsiniz. Başka bir konuda (örneğin, belirli bir marka veya bütçe) detaylı bilgi isterseniz, lütfen söyleyin!

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

## İlk Bilgisayar Alıcıları İçin Dikkat Edilmesi Gereken Noktalar

### 1. Kullanım Amacınızı Belirleyin  
- **Gaming?** → Yüksek performanslı CPU/GPU, yüksek frame rate.  
- **Office / Web / Video Editing?** → En az 8 GB RAM, hızlı SSD, stabilizasyon.  
- **Genel Kullanım / Çalışma Merkezi?** → Basit işletim sistemi, yeterli disk kapasitesi.  

> *En doğru başlangıç, “ne yapacağım?” sorusunun cevabını belirlemektir.*

---

### 2. Bütçeyi Netleştirin  
| Bölüm | Örnek Bölge (TL) |
|-------|-------------------|
| Temel Model (HDD + 4 GB RAM) | 400–600 |
| SSD + 8 GB RAM + Grafik Kartı | 700–900 |
| High‑End Desktop / Laptop | 1200–2000+ |

- **Başlangıçta ne kadar harcayabilirsiniz?**  
- **Ekstra özellikler** (monitor, ekran ayarları vb.) de bütçeye dahil edilebilir.

---

### 3. Teknik Özelliklerinizin Maksimum Seviyesini Belirleyin  

| Özellik | Ne İstediğinizde | Önerilen Minimum / Recommended |
|---------|------------------|--------------------------------|
| **CPU** | Hızlı işlem, çok parça işleme | Intel i5 / AMD Ryzen 5+ veya équivalent |
| **RAM** | Multitasking, video edit, web browsing | ≥ 8 GB (16 GB önerilir) |
| **Disk** | Hızlı yükleme, veri depolama | NVMe SSD (≥ 500 GB) – HDD daha ucuz ama hızlı değildir |
| **Grafik Kartı** | Gaming / 3D render | NVIDIA GeForce RTX 3060+/GTX 1660+, veya AMD Radeon RX 5600+ |
| **Monitor** | Çözünürlük, renk kalitesi | 1080p Full HD (1920×1080) minimum; 1440p/4K için planlama yapın |

> *Her detayı “ne yapacağım” ile eşleştirmelisiniz.*  

---

### 4. Form Faktörünü Seçin: Desktop vs Laptop  

| Özellik | Desktop | Laptop |
|--------|---------|--------|
| **Performans** | Daha yüksek (daha fazla komponent) | Azalabilir (soğukluk, ekran boyutu) |
| **Konfor** | Ucuz, geniş alan | Portatif, kullanışlı |
| **Kullanım Alanı** | Çalışma merkezi, oyun salonu | Ücretli, seyahat, evde kullanılabilir |
| **Bütçe** | Genellikle daha düşük | Bazı modeller daha pahalı olabilir |

- **İlk kez alacağınızda**, genellikle **desktop** daha iyi bir başlangıç olur; ancak **laptop** daha pratik olabilir eğer sürekli taşınır ya da ekran boyutunu küçük tutmak isterseniz.

---

### 5. Operasyonel Sistem ve Ekosistemi  

- **Windows 10/11**: En yaygın, güncellemeler, uygulamalar.  
- **macOS**: Eğer tasarım ve entegrasyon öncelikliyse.  
- **Linux**: Teknolojiye özgü, fakat yeni kullanıcı grubu.  

> *Genellikle Windows 10/11, özellikle Türkiye’deki piyasada en sık tercih edilen sistemdir.*

---

### 6. Marka Güvenliği ve Garantisi  

- **Garanti Süresi**: En az 1 yıl (ideally 2).  
- **Yerel Servis**: Hızlı arıza çözümü, ekstra destek.  
- **Müşteri Temsilciliği**: Online destek, forumlar, video tutoriallar.  

> *Yeni markalar da güvenli olabilir, ama uzun vadede garantili bir marka tercih edin.*

---

### 7. Yedekleme ve Upgrade Olasılığını Planlayın  

- **SSD’yi değiştirebilmek** (upgrade) mümkün mü?  
- **Hazırlanabilirlik**: Modüler ekran, ekran ayarları, ekran kartı değiştirme.  
- **Veri Koruma**: Cloud backup, external drive seçenekleri.  

---

### 8. Ekipman ve Erişim Gereksinimleri  

- **Monitor**: Çözünürlük, renk kalitesi, hareketlilik.  
- **Klavye & Mouse**: Uygun boyut, kontrol.  
- **Peripheral**: Eğer çok sayıda cihaz kullanıyorsanız, ekstra input (keyboard, mouse, webcam).  

---

## Özet Checklist (Kullanım Amacı + Bütçe)

1. **Amacınız nedir?** (Gaming, Office, Video, Genel…)  
2. **Bütçeniz ne kadar?** (Basit modelden başlayıp, artışı planlayın)  
3. **CPU, RAM, SSD, Grafik Kartı** için minimum değerleri belirleyin.  
4. **Desktop mi Laptop mı?** (Konfor vs performans)  
5. **Operasyon Sistemi** (Windows 10/11)  
6. **Garanti, Servis, Yedekleme** detaylarını kontrol edin.  
7. **Marka ve Ekipman** (monitor, klavye, mouse) uygunluğu test edin.  

Bu adımları izleyerek, ilk kez bir bilgisayar satın alacak kişi, **doğru zaman, doğru para ve doğru performans** elde edebilir. Her şeyi bir tablo halinde inceleyip, “ne yapacağım?” sorusuna net cevap bulursanız, seçiminiz daha güvenli ve daha etkili olacaktır! 🎉

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-36 (advice)

**Prompt:** Sınavdan önceki gece nasıl bir hazırlık yapmak daha verimli olur?


### A

# Sınavdan Önceki Gece Nasıl Daha Verimli Hazırlık Yapılır?

Gece hazırlığında en büyük hedef **uyku kalitesi** ve **daha az stres** oluşturmaktır. İşte bu amacıyla pratik adımlar:

## 1. Son 30–60 Dakika Tekrar Et
- **Tekrar et** sadece son günün en önemli konularını veya sorularda kullanılan formülleri.
- **Yazılı/şöylece özet** yapın, ancak uzun süreli okuma veya çözümlemeyi kaçının.
- Her soruda **öncelikle cevapları kontrol edip yanlışları düzeltmeyi denemeyin** – bu stresi artırır.

## 2. Çok Az Yeni Materyal Geliştirme
- Gece **yeni bir konu** veya yeni bir problem seti açmayın.  
- Alınan bilgiyi **sadece hafızaya aktive** (active recall) veya kısa süreli spaced‑repetition ile tekrar edin.

## 3. Hafif Beslenme & Su
- Yemek ve içecekleri **lighter** tutun (örneğin, hafif bir öğün veya kahve).  
- **En az 8–9 saat** uyku sağlamak için yeterli su için; çünkü uyku sırasında terleme ve hidrasyon önemlidir.

## 4. Cafein ve Alkol Kullanımı
- Cafein (kahve, kahve ekstraktı, çay) ve alkol **geceye yakın** kullanmayın – bunlar uyku kalitesini düşürür.  
- Eğer şekerli gıda tüketiyorsanız, daha az miktarda tercih edin.

## 5. Uyku İçin Hazırlanma
- **Işık, ses ve telefon** geceyi uykudan ayırt etmeyin. Kapalı bir odada, düşük ışıklı bir ortamda, ses seviyesini düşükse.
- **Sabah kahvaltı planlı** ve zamanında başlayın; erken bir sabah da uykuya geçişi daha rahat olur.

## 6. Minimalist “Last-Minute” Plan
| Adım | Ne Yapmalı? |
|------|-------------|
| **Materyaller** | Sınav formu, pencereler, kimlik bilgileri, ekipmanları hazırlayın. |
| **Sorular** | Tekrar etmek istediğiniz soruları bir listeye yazıp, geceyi sadece bu listeyi dolaşarak geçirebilirsiniz. |
| **Zaman** | En az 2–3 saat önce uykuya dalın; geceyi sadece hafif bir gözden geçirmeyle bitirin. |

---

### Kısa Özet
> **“Son dakikaları hafif bir gözden geçirmeyle, uyku kalitesini korumak ve stresi azaltmak.”**

Bu şekilde, gece hazırlığında **verimli** ve **uyku dolu** bir başlangıç elde edersiniz. Başka bir sorunuz varsa sormak isterseniz! 😊

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

## Sınavdan Önceki Gece Daha Verimli Bir Hazırlık Nasıl Yapılır?

Sınav günü sabah erken gelmek yerine, **gece** (yani gün içinde yoğun çalışmayı bitirip) hafif bir gözden geçirme yaparak zihninizi ve vücudunu optimalize etmeniz en etkili yoludur. Aşağıda, bu süreci adım adım detaylandırdığım pratik ipuçları bulunuyor.

---

### 1. Neden “Gece” Hazırlığı Önemli?
| Faktör | Etkisi |
|--------|--------|
| **Uyku** | Yorgunluk, hafıza kaybı ve dikkat azalması riski. |
| **Yeterli Besin & Su** | Enerji seviyesini korur, zekâyı destekler. |
| **Düşük Kaféin / Alkol** | Uyku kalitesini düşürür. |
| **Zihin Kapasitesi** | Gece hafif bir gözden geçirme, yeni bilgiyi değil, **zinciri** (key concepts)ı güçlendirir. |

> **Kısaca:** Gece sadece “ne yazmak istiyorum?” sorusuna cevap vermek yerine, **en kritik konuları 10‑15 dakikalık bir gözden geçirme** yaparak zihinsel yükü azaltın.

---

### 2. Gün İçin Planlama (Önce)

1. **İlk 30 dk – Güncel Notlar**  
   - Ders kitaplarını, notlarınızı ve özetleri açın.  
   - Her konu için **3‑5 ana nokta** (bir kısım, bir uygulama, bir soru) belirleyin.

2. **Orta 60 dk – Aktif Hatırlatma**  
   - **Flashcards** veya **self‑testing** (yazılım, kart) ile anlatımı tekrarlayın.  
   - “Ne zaman kullanacağım?” sorusunun cevabını hazırlayın.

3. **Son 30 dk – Hafif Bir Pratik**  
   - Bir sorunuzla ilgili kısa bir çözüm örneği yazın ya da bir deneme sorusu atıf alın.

Bu planı **gün içinde tamamlayarak**, gece hazırlığında “tek bir gözden geçirme” ihtiyacınız olmaya devam eder.

---

### 3. Gece Hazırlığı Adımları

#### a) Hafif Gözden Giriş (10‑15 dk)
- **Notlarınızı** kapalı bir pencereye koyup **kısa bir özet** (1‑2 cümle) yazın.  
- **Temel kavramları** (formüller, terimler)ı hatırlayın ama derin analiz yapmayın.

#### b) Aktif Tekrar (5‑10 dk)
- **Somut soruları** (yazılım, kart) üzerinden **3‑4 sordu**.  
- Yanıtları **yazın** veya **yazılım** üzerinden kontrol edin.  
- Hata yaparsanız, o hatayı not alın.

#### c) Beslenme ve Su (5 dk)
- **Lihavetli bir yemeği** (protein + karbonhidrat + taze sebze) tüketin.  
- **Geniş su** için (≥1 litre).  
- Kafeinli içeceklerden kaçının.

#### d) Uyku Hazırlığı (5‑10 dk)
- **Gün içinde en yüksek enerjinin olduğu saat** (genellikle akşam 20‑22 arası) için **daha az ışık** ve **daha az aktivite** tercih edin.  
- **Gün içinde gördüğünüz bir film** gibi rahat bir ortamda uyun.

#### e) Zihinsel Yönetim (5‑10 dk)
- **Derin nefes egzersizi**: 4 sanal nefes al, 4 sanal tut, 6 sanal dışa çık.  
- **5‑minlik bir meditasyon** veya **mantık** (örnek: “Benim sınavdan önce ne yapmalıyım?”) sorusu.  
- Stresli hissettikten sonra **kendi sesinizi dinleyerek** rahatlatın.

---

### 4. Uyku ve Güncelleme

| Durum | Önerilen Süre |
|-------|---------------|
| **Normal uykusu** | 7‑9 saat (özellikle 8 saat) |
| **Aktif hafif çalışma sonrası** | 8‑9 saat (vücut ve zekâ için) |
| **Sınav gününe yakın** | **En az 7 saat** uyun; çok az uyku, hafif yorgunluk artar. |

> **İpucu:** Gece 2‑3 saat önce hafif bir yürüyüş ya da hafif esneme yaparak kan akışını hareketli tutabilirsiniz, ancak çok fazla hareket etmeyin.

---

### 5. Güncellemeler & Riskler

| Risk | Ne Yapmalı? |
|------|-------------|
| **Yetersiz çalışma** | Gece sadece “ne yazmak istiyorum?” diye düşünmek yerine, **kritik formüller/terimleri** hatırlatın. |
| **Çok fazla kahve/alkol** | Uyku kalitesini düşürür; gece içimi hafif bir kahve (örn. 200 ml) ise kabul edilebilir. |
| **Yansıtıcı haberler** | Sınav öncesi sosyal medya/ haber bilgisayarları kapatın. |
| **Yorgunluk** | Uyku kalitesini bozmadan, **hafif bir dinlenme** (örneğin, bir kitap) yapın. |

---

### 6. Günlük Rutin Örnek (Gece Sonra)

| Saat | Aktivite |
|------|----------|
| 21:00 | Geniş su, hafif yemeği |
| 21:15 | 5‑10 dk hafif gözden geçirme (notlar, formüller) |
| 21:25 | Aktif tekrar soruları (3‑4 sordu) |
| 21:35 | Derin nefes egzersizi / 5‑dk meditasyon |
| 21:45 | Uyma hazırlanma (günlük 7‑8 saatte) |
| 22:00 | Uyku (uyanma) |

---

## Özet: “En Verimli” Gece Hazırlığı Formülü

1. **Planlayın** → Gün içinde kritik konuları hızlıca işleyin.  
2. **Hafif gözden geçirin** → Gece sadece anlatım ve hatırlatma.  
3. **Beslenin ve hidrate edin** → Enerji ve duvar sağlığını korur.  
4. **Uyku ve rahatlamayı öncelikli yapın** → Zekanın ve unvanların kalmasını sağlar.  

Bu adımları izlediğinizde, sınav günü **yorgunluk, hafıza kaybı ve stres** risklerini minimize edip, en iyi performansınızı sunmanızı sağlayabilirsiniz. İyi bir gece, en büyük hazırlık sürecinin bir parçası! 🎓😴

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____

---

## wr-tr-40 (translate)

**Prompt:** Şu cümleyi Türkçeye çevir: "If you have any questions about the new policy, please contact the human resources department."


### A

**Türkçe çeviri:**  
“Yeni politika hakkında herhangi bir sorunuz varsa, İnsan Kaynakları Bölümüne (Human Resources Department) başvurun.”  

(Alternatif ifadeler: “Eğer yeni politikaya dair herhangi bir soru varsa, insansal kaynakları bölümüne iletişime geçin.”)

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____


### B

Eğer yeni politika hakkında sorularınız varsa, lütfen insan kaynakları birimine ulaşın.

Naturalness (1-5): ____   Task (yes/partly/no): ____   Invented or wrong words: ____
