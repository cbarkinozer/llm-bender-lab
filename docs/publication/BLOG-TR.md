# Türkçe küçük dil modeline daha az konuşmayı öğretmek: Qwen3.5-4B ile LoRA yolculuğumuz

Bir modelin iyi cevap vermesiyle çok şey söylemesi aynı şey değil. Bu çalışmaya
başlarken karşılaştığımız sorun tam da buydu: Türkçe cevaplar çoğu zaman uzun,
başlıklı, kalın yazılı ve bazen emojiliydi. Asıl cevabı bulmak için açıklamaların
arasından geçmek gerekiyordu. Daha önemlisi, eklenen açıklamalar bazen olmayan
bir neden, yanlış bir dil bilgisi kuralı veya kullanıcı adına verilmiş bir duygu
yorumuyla cevabı bozuyordu.

Amacımız yeni bir Türkçe temel model eğitmek değildi. Qwen3.5-4B'nin mevcut
yeteneklerini olabildiğince koruyarak daha doğrudan, doğal ve ölçülü cevaplar
veren bir LoRA adaptörü geliştirmekti. Geldiğimiz noktada kullanılabilir bir
üslup adaptasyonumuz var. Bunun her alanda daha akıllı veya hatasız bir model
olduğu iddiasında değiliz. Özellikle özetleme sadakati konusunda sonuçlarımız
karışık; bunu anlatının sonunda saklamadan ele alacağız.

> Yayın notu: Bu bir blog taslağıdır. Model, veri seti ve GitHub bağlantıları
> yayımlandıktan sonra aşağıdaki kaynak bölümüne sabit revizyonlarla eklenecek.

## Önce neyi değiştirmek istediğimizi anlamamız gerekti

İlk veri envanterimiz binlerce sentetik Türkçe kayıttan oluşuyordu. İçinde biçim
takibi, bilgi çıkarma, özetleme, açıklama, belirsizlik, Türkçe sözcük/ek ayrımları
ve modelin kendisine insani deneyimler yakıştırmaması gibi farklı hedefler vardı.
Örneğin doktor ile doktora aynı görevde yakın görünse de anlamı ciddi biçimde
değiştirebilir. “Vergi oranı değişmedi, veri paylaşım kuralları güncellendi”
cümlesinde de yakın bir sözcüğü seçmek cevap vermek değildir.

Davranış hedeflerini netleştirdik: Gereksiz giriş yapmadan cevap vermek; istenen
biçimi izlemek; olumsuzluğu, koşulu ve belirsizliği korumak; eksik bilgi gerçekten
kararı engelliyorsa soru sormak; kullanıcı o bilgiyi verdiğinde tekrar soru sorma
döngüsüne girmemek. Duygusal bir paylaşımda da modelin “gurur duyuyorum” gibi
yaşamadığı bir duyguyu sahiplenmesi veya hemen uzun tavsiyeler vermesi gerekmiyor.

Burada önemli bir ayrım vardı: “Kısa cevap ver” ile “gereksiz şeyi çıkar ama
gerekli düşünceyi koru” aynı eğitim hedefi değil. Bir karar sorusunda tek cümlelik
boş bir cevap da başarısızdır. İyi hedef, öneriyi ve nedenini koruyan cevaptır.

## Daha çok kayıt her zaman daha iyi hedef anlamına gelmedi

Erken deneylerde daha geniş sentetik havuzlar kullandık. exp006 için kullanıcı
izlenimi, bazı davranışların öğrenildiği fakat genelleme ve Türkçe doğallığın
istenen yerde olmadığı yönündeydi. exp008 ise yalnızca100 ek örnekle yapılan
tanısal bir denemeydi. Başta bu küçük eğitimin proje hedefinin tamamına yetip
yetmeyeceğini sorguladık. İlginç biçimde, kullanıcı bazı cevaplarının Türkçesini
önceki deneylerden daha iyi buldu; buna karşılık gereksiz soru sorma döngüsü
gibi sorunlar vardı.

Bu gözlemler, veri sayısından önce hedef kalitesini düşünmemizi sağladı. Bunlar
kontrollü genel yetenek ölçümleri değil, sonraki hipotezleri şekillendiren kullanıcı
gözlemleriydi. “100 örnek yeterlidir” veya “fazla veri Türkçeyi bozar” gibi genel
bir sonuca varmadık.

Yeni aşamada önce100 soru seçtik;80 eğitim,20 geliştirme. Önce temel modelin
cevaplarını uzun çıktı bütçesiyle aldık, sonra bu cevapları insan denetimiyle
düzelttik. Amaç baştan tamamen başka bir ses yazmak değil, mümkün olduğunda iyi
ifadeleri koruyup gereksiz uzunluğu, yanlış çıkarımları ve yapay dili gidermekti.

Başlangıç sezgimiz “kelime dağılımını benzer tutarsak unutmayı azaltabiliriz”
şeklindeydi. Zamanla bunu daha dikkatli ifade ettik: Benzer sözcükleri kullanmak
tek başına katastrofik unutmayı önlemez. Görev karışımı, doğru hedefler, güncelleme
şiddeti ve değiştirmek istemediğimiz yetenekleri gerçekten ölçmek daha önemlidir.
Minimal düzenleme bir veri hazırlama yaklaşımıdır, matematiksel koruma garantisi değil.

## Model üslubu öğrenirken cevabın düşüncesini kaybedebiliyor

exp009 kullanıcı değerlendirmesinde başarısız bulundu: Hâlâ uzun ve süslü cevaplar,
Türkçe sorunları ve istenmeyen davranışlar vardı. exp010'da aynı veriyle öğrenme
oranını5e-5'ten1e-4'e çıkardık. Bir miktar kısalma gördük, fakat bu tek başına
cevabın içeriğini iyileştirmedi.

En öğretici örneklerden biri küçük bir evde çalışma ve dinlenme alanının
karışmasıydı. İstenen cevap, sorunun eksik bir çalışma yüzeyi mi yoksa belirsiz
bir alan sınırı mı olduğunu ayırt etmeli; yeni masa almadan önce yerleşim ve
ışığı denemeyi somutlaştırmalıydı. Bazı adaptör cevapları daha kısa görünürken
maliyet mantığını ters çevirdi veya kararı kullanıcıya geri bıraktı. Demek ki
“istenen uzunluğa yaklaştı” ile “istenen muhakemeyi korudu” ayrı ölçülerdi.

Sonraki turları ikili deneyler halinde yürüttük:

| Deney çifti | Sorduğumuz soru |
| --- | --- |
| exp011 / exp012, A / B | Daha uzun eğitim mi, bazı eğitim hedeflerini/senaryolarını değiştirmek mi daha faydalı? |
| exp013 / exp014, C / D | Aynı düzeltilmiş80 örnekte dört yerine altı epoch kazanım getiriyor mu? |
| exp015 / exp016, E / F | Hedefleri onarılan80 örneğe24 yeni senaryo eklemek, aynı40 güncellemede aktarımı iyileştiriyor mu? |

A'nın Türkçesi ve cevaplarının “akıllı” hissi kullanıcı tarafından beğenildi;
B bazı kısa bilgi çıkarma görevlerinde daha iyi bulundu. Bu, iki adaptörün iyi
taraflarını otomatik birleştirebileceğimiz anlamına gelmiyordu. C/D karşılaştırması
da daha fazla epoch'un her sorunu çözmediğini gösterdi: Daha düşük eğitim kaybı,
daha iyi insan değerlendirmesi demek değildi.

Son çiftte E'nin80 sorusunu koruyup gerekli hedef onarımlarını yaptık. F aynı
çekirdeğe24 farklı, insan denetimli senaryo ekledi. İki model de eski adaptörden
devam etmek yerine aynı sabitlenmiş temel modelden başlatıldı. Öğrenme oranı,
LoRA ayarları ve40 optimizer adımı aynı tutuldu. Ancak bunu saf bir “çeşitlilik
deneyi” diye sunmuyoruz:104 kayıt, görev karışımını ve örnek başına görülme
sayısını da değiştiriyor.

F'nin eğitiminde BF16 LoRA, rank16/alpha16,1e-4 öğrenme oranı, cosine schedule,
mikro batch1 ve8 gradient accumulation kullandık. Kayıp sadece son asistan
cevabında hesaplandı; önceki konuşma turları maskelendi.40 adım,104 kayıt için
yaklaşık3,08 epoch'a karşılık geldi. Son adaptörü önceden seçtiğimiz40. adımda
aldık; değerlendirmeye bakıp gizlice başka bir checkpoint seçmedik.

## Kendi sorularımızdan dış değerlendirmeye geçiş

Projenin32 maddelik geliştirme karşılaştırmasında F26, temel model17 geçer not
aldı. Bu umut vericiydi, ama sürekli dönüp baktığımız soruları başarı öyküsünün
tek kanıtı yapmak istemedik. Harici CETVEL kaynaklarını kullandık: yazım/dil
bilgisi düzeltme, iki kaynağa dayalı soru-cevap görevi, İngilizceden Türkçeye
çeviri ve Türkçe özetleme.

Önce100 soruluk bir pilot, ardından her görevden100 olmak üzere500 yeni soru
çalıştırdık. Yeni500, önceki100'ün üzerine400 eklemek değildi. Tarihsel700 kayıt
ve pilotun kaynak grupları dışlandı; sabit kaynak revizyonlarıyla farklı gruplar
seçildi. Bu beş görevlik yerel örneklem, tüm CETVEL'i temsil eden resmi skor değildir.
Kaynak grubu temelli seçim de düz satır rastgele örneklemesiyle aynı değildir.

Temel model ve F aynı istemler, şablon, çıktı bütçesi ve çözümleme ayarlarıyla
çalıştırıldı. vLLM kullandık;4096 çıktı tokenı ve8192 bağlam bütçesi vardı.
Tekrarlama cezası1,05'ti. Modelin EOS'u ile tokenizer'ın konuşma bitiş tokenının
farklı olduğunu ayrıca kaydettik. Bu tür küçük görünen uygulama ayrıntıları
karşılaştırmayı değiştirebilir; yalnızca model adı ve sıcaklığı yazmak yetmez.

500 soruda temel modelin496, F'nin499 cevabı protokolde seçilen doğal EOS ile
bitti. Kalan4 ve1 cevap tekrar korumasında durdu; atılmadı, yeniden sorulmadı,
sonuçlara dahil edildi. Medyan çıktı uzunluğu98 token'dan26'ya indi.

## Sonuç: gerçek ama kapsamı sınırlı bir kazanım

Kaynağa dayalı QA token F1 skorları belirgin arttı: TQUAD20,06→64,58;
XQuAD-TR13,68→55,84. Düzeltme tam eşleşmesi0/100→30/100 oldu. Çeviri BLEU'su
16,84→16,81 ile neredeyse aynı kaldı; chrF52,16→52,43 oldu. Özetleme ROUGE-L
18,45→20,93 yükseldi.

Bu sayıları “Türkçe doğruluk patladı” diye okumak yanlış olurdu. Uzun bir cevap
doğru bilgiyi içerirken tam eşleşme ve token F1 düşük çıkabilir. Bu nedenle çıktı
üretilmeden seçilen30 soruyu, her soruda model etiketlerini karıştırarak insan
incelemesine aldık. Tek değerlendiricili bu örneklemde sonuçlar:

- F19 kez, temel model6 kez tercih edildi;2 beraberlik ve3 ikisinin de uygun olmadığı durum vardı.
- Geçer not F23/30, temel model21/30 oldu.
- İncelenen12 QA sorusunda iki model de doğruydu; F12'sinde de tercih edildi.
- Düzeltmede F4/6, temel model0/6 geçer not aldı.
- Çeviride iki model de5/6 geçer not aldı; tercih sonucu dengeliydi.
- Özetlemede temel model4/6, F2/6 geçer not aldı; temel model4, F1 kez tercih edildi.

Son madde, yüksek ROUGE'nin güvenilir özet anlamına gelmediğini gösteriyor.
Özetlerde anlam, atıf, koşul ve kaynak dışı eklemeler insan gözüyle kontrol
edilmeli. Pilotun özetleme incelemesi daha olumlu görünmüştü; yeni örneklemde
tablo değişti. Küçük insan örneklemlerinin belirsizliğini gizlemiyoruz.

Savunabileceğimiz sonuç şu: Türkçe cevapları daha kısa ve doğrudan hale getiren,
incelenen QA örneklerinde doğruluğu koruyan ve bazı düzeltme davranışlarını
iyileştiren bir adaptör elde ettik. Çeviride net bir bozulma sinyali görmedik.
Ancak özetleme sadakati zayıf; genel akıl yürütmenin, tüm Türkçe görevlerinin,
düşünme modunun veya çok modlu yeteneklerin hiç zarar görmediğini kanıtlamadık.

## GPU'dan daha kalıcı olan şey: deney kaydı

Süreç yalnızca model eğitmekten oluşmadı. SSH kimlik doğrulama, bağımlılık/CUDA
uyumu, kopan bağlantılar ve tamamlanmadan açılan dosya aktarımı gibi operasyonel
sorunlar yaşandı. Çözümleri tekrar kullanmak için not aldık; anahtar ve API
anahtarlarını notlara yazmadık. Ağırlıklar, configler, ortam bilgileri, loglar,
ham çıktılar ve hash manifestleri pod kapanmadan yerel diske alındı.

Tekrarlanabilirlik için geçmiş denemeleri “daha düzgün görünmesi” adına
yeniden yazmadık. Başarısız cevaplar, negatif sonuçlar, değiştirilmiş hedefler,
çıktı kesilmeleri ve insan değerlendirmeleri kanıt zincirinin parçası olarak kaldı.
F'yi paylaşırken104 eğitim ve20 geliştirme kaydı, seçilen adaptör ve sınırlılıkları
yazan kartları birlikte sunacağız. Harici benchmark metinlerini eğitim setine
katmayacağız; onların dağıtım hakları ayrı bir konu.

## Bu aşamayı neden burada kapatıyoruz?

Paylaşılabilir bir deneyin kusursuz olması gerekmiyor; neyi yaptığı ve neyi
kanıtlamadığı açık olmalı. F'yi “hatasız Türkçe model” diye değil, belgelenmiş
sonuçları ve açık sınırlılıkları olan bir Türkçe cevap üslubu adaptörü olarak
paylaşmak anlamlı. Gelecekte özetleme sadakati, de/da ve doğru cümleye gereksiz
müdahale için yeni, benchmarktan türetilmemiş eğitim örnekleri düşünülebilir.
Bu değerlendirme gelecekteki eğitimi yönlendirirse geliştirme verisine dönüşür;
sonraki güçlü iddialar için yeni final test gerekir.

Agentic RL ayrıca planlarımız arasında, fakat bu çalışmanın sonucu değil.
Şimdilik yeni GPU işi başlatmıyoruz. Kazandığımız şey yalnızca bir adaptör değil:
üslup, içerik ve ölçümün birbirine karıştığı yerde daha iyi deney tasarlamayı öğrendik.

## Yayın öncesi eklenecek bağlantılar

- Hugging Face adaptör deposu ve sabit revizyonu: TODO
- Hugging Face104/20 veri seti ve sabit revizyonu: TODO
- GitHub deney kodu/günlüğü ve sabit commit: TODO
- Model/veri lisansı ve eksik kişisel-asistan kaynak/koşul bilgileri: TODO

Sayısal kaynaklar: exp015/human-review-v3; CETVEL exp002/human-review-v1;
exp003/results-v1/comparison.json ve human-review-v1/summary.json.
Tarihsel gözlemler: response-style-control EXPERIMENT-JOURNAL.md ve deney README'leri.
