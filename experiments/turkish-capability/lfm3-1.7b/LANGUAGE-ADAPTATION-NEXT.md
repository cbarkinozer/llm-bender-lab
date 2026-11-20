# LFM3'e Türkçe kazandırma: mevcut iş listesi

2026-11-20 akşam güncellemesi: GPU kapatılabilir; eğitim yarına bırakıldı.
Resmî cookbook ile karşılaştırma ve 640 satırın yeni prompt/completion sürümü
CPU üzerinde hazırlandı. Boş reasoning, boş düşünme çıktısını öğretme talimatı
değildi; önceki yorum düzeltildi. Gerçek TRL loss-mask kontrolü ve GPU smoke
henüz yapılmadı. İki deneyin kapsamı ve yarınki adımlar:
[cookbook hazırlığı](cookbook-sft-v01/README.md).

Hedef: Türkçeyi anlayıp doğru ve doğal Türkçe cevap üretebilmek; İngilizce,
aritmetik ve muhakemede çalışan becerileri mümkün olduğunca korumak.
Dil başına ayrı parametre bölmesi varsayılmıyor. Başka modele geçmek bu
çalışmanın hedefi değil. Üslup tercihi ve kısa cevap, yetenek kazanımı sayılmıyor.

- [x] Mevcut640 SFT satırının yapı, dört yön eşleşmesi, ayrı düşünme alanı ve
  token uzunluklarını yerelde denetle.
- [x]32 görev grubunun sayısal referanslarını yeniden hesapla; sayısal değerlerin
  bulunmasını tüm açıklamanın doğruluğu gibi yorumlama. g104'teki dört işaretin
  zorunlu olmayan18000/yıl hesabından kaynaklandığını incele; veriyi değiştirme.
- [x] Aynı zinciri sabitle: orijinal base -> yayımlanmış CPT -> CPT+bilingual69.
- [x] Dört dil yönünü, sembolik aritmetiği ve ayrı görülen-eğitim örneklerini seç.
- [x] Üretim ayarlarını, model/adapter SHA'larını ve264 çıktılık kapsamı dondur.
- [x] Yalnız inference çalıştırıcısını, yeni pod adresi alan aktarım aracını ve
  checksum doğrulamalı yerel yedeklemeyi hazırla.
- [x] CPU üzerinde iş sayısı, tekrar çalıştırma, thinking modu ayrımı, paket
  sınırları ve yedekleme doğrulamasını test et; shell sözdizimini kontrol et.
- [x] Yeni GPU SSH adresini al; tanı çalışması tamamlandı (2026-11-20 İstanbul).
- [x] GPU sürücüsü/BF16, model yükleme, native şablon/EOT, merge-reload ve smoke
  kontrollerini geç. Bunlar CPU testleriyle geçmiş sayılmıyor.
- [x] Üç modeli aynı koşullarda çalıştır; hiçbir eğitim başlatma.
- [x]264 ham çıktıyı, logları ve manifestleri indir; tam ağırlıkları indirme.
- [x] Yerel yedek doğrulandıktan sonra podun kapatılabileceğini bildir.
- [ ] Türkçe kazanımını ve diğer becerilerde kaybı aşama bazında değerlendir;
  görülen12 eğitim örneğini genel başarı puanına katma.
- [ ] Sonuca göre CPT karışımı/süresi, SFT güncelleme şiddeti veya eğitim
  hedefleri üzerine tek değişkenli bir deney seç. Şimdi LR deneyi başlatılmadı.
- [ ] Bir aday seçildikten sonra yeni, bağımsız nihai holdout kullan. Mevcut
  paket tüketilmiş tanı verisidir; eğitim verisine eklenmez. DPO daha sonra.

Çalıştırma komutları, paket SHA'ları ve ayrıntılar:
[hazırlık ve GPU devri](stage-diagnostic-v01/README.md).

GPU çalışması ve doğrulanmış yedek tamamlandı. Pod kapatılabilir.
[Sembolik aritmetik incelemesi ve kalan değerlendirme](STAGE-DIAGNOSTIC-RESULTS.md).
CPT doğru hesabı üretip uzatabiliyor; otomatik son-sayı kontrolündeki0/8
aritmetiğin silindiği anlamına gelmiyor. SFT sonrası bu8 kontrolde gerçek
yanlış yanıtlar ve thinking bölümünü hemen kapatma görüldü.
