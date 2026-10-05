# F adaptörü: paylaşım rehberi (2026-10-04)

Bu SFT aşaması kapandı. Seçilen aday `exp-016-diverse-coverage-sft`, son adım40.
Yeni eğitim veya GPU işi planlanmıyor. Agentic RL ayrı, ertelenmiş araştırma hattı.
Bu giriş2026-10-04 kapanış durumunu anlatıyordu.2026-10-05 tarihinde adaptör/veri
seti yüklendi ve indirilen dosya hashleri doğrulandı; daha sonra iki depo public
gözlendi. Güncel kanıt: [yayın notları](PRIVATE-UPLOAD-20261005.md). Public olmak,
tamamlanmış kaynak/sağlayıcı koşulu kontrolü anlamına gelmez. Güncel kartlar
`OCCAM-MODEL-CARD.md` / `OCCAM-DATASET-CARD.md`; blog hâlâ taslak.

## Nerede ne paylaşılmalı?

| Yer | İçerik | Önerilen ad |
| --- | --- | --- |
| Hugging Face Model Hub | PEFT adaptörü, model kartı, eğitim ayarları, sonuç özeti, hashler | `NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1` |
| Hugging Face Dataset Hub | Temiz104 eğitim +20 geliştirme kaydı, veri kartı, kaynak/split manifesti | `NAMESPACE/turkish-direct-response-sft-v1` |
| GitHub | Kod, deney günlüğü, yapılandırmalar, değerlendirme betikleri ve küçük sonuç özetleri | Mevcut `llm-bender-lab` |
| Blog | Türkçe süreç, başarısız denemeler, kararlar ve dürüst sonuçlar | Bu klasördeki `BLOG-TR.md` |

Model ve veri kartlarını İngilizce tutmak keşfedilmeyi kolaylaştırır; Türkçe özeti
ve blogu bağlantılandır. Blog için kişisel site veya Medium kullanılabilir.
Hugging Face blogu da doğrudan model/veri setiyle bağlantı kurar; kontrol edilen
güncel kurallarda onaylı e-posta yanında PRO aboneliği veya yetkili Team/Enterprise
üyeliği gerekiyor. Bu koşul yoksa GitHub'daki blog Markdown'ı ücretsiz kaynak metin
olarak kalabilir. LinkedIn kısa duyuruya uygun; kalıcı teknik kanıtın yeri değildir.
GPU isteyen canlı demo/Space ilk sürüm için gerekli değil.

## Yüklemeden önce gereken kararlar

1. HF kullanıcı adı ve iki depo adı.
2. Model lisansı: sabitlenmiş başlangıç modelinin kartı Apache-2.0 gösteriyor;
   adaptör için Apache-2.0 makul bir öneri, henüz kullanıcı adına seçilmedi.
3. Veri lisansı: CC-BY-4.0 bir seçenek, fakat yalnızca gerekli haklar doğrulanırsa.
   Projenin Apache kod lisansı veri üzerindeki tüm hakları otomatik çözmez.
4. Kişisel asistanla yapılan hedef düzenlemelerinde kullanılan sağlayıcı/model,
   mümkünse sürüm/tarih ve geçerli çıktı-eğitim/yayın koşulları tamamlanmalı.
   Tarihsel sentetik soruların kaynakları da gözden geçirilmeli. Bilinmeyenleri
   uydurarak doldurma. Kaynak dökümü taslak pakette `source-origins.json`.
5. Temiz dosyalarda kişisel bilgi, istemeden kopyalanmış üçüncü taraf metin ve
   değerlendirme kriterlerinin eğitim mesajına karışması gözden geçirilmeli.

Kaynak/koşul doğrulaması bitene kadar paket özel/taslak tutulmalı. Bu bir hukuki
hak garantisi değil, yayın öncesi kontrol listesi. CETVEL kaynak metinleri veya
referansları bu SFT veri setine EKLENMEZ; onların ayrı lisansları var.

## Yerel paket oluşturma

Repo kökünde:

```powershell
python docs/publication/build_release.py --adapter-dir "C:/Users/cbark/Documents/llm-bender-artifacts/exp-015-016-paired/essential-extracted/exp015-exp016-runs/F/sft-v1/adapter" --output-dir "C:/Users/cbark/Documents/llm-bender-artifacts/publication/F-v1-draft"
```

Betik seçilen ağırlık/config ve veri hashlerini doğrular. Çıktı sadece yeni bir
klasöre yazılır; var olan klasörü ezmez. Ağırlıklar Git'e eklenmez. Temiz veri
aynı istem/hedefleri korur; orijinal cevaplar, Argilla kullanıcı/yanıt kimlikleri,
notlar ve değerlendirme kriterleri yayımlanacak mesajlara dahil edilmez.
104/20 son dağılımı %80/%20 DEĞİLDİR: ilk80/20 ayrımına24 eğitim kaydı eklendi.
20 kayıt tekrar tekrar kullanılan geliştirme setidir, bağımsız final test değil.
12 ayrı kontrol SFT yayın paketinde yoktur; deney deposunda kalır.

Yayın kararları tamamlanınca **yeni** bir çıktı klasörü seçerek çalıştır:

```powershell
python docs/publication/build_release.py --adapter-dir "ADAPTER_PATH" --output-dir "NEW_RELEASE_PATH" --model-id "NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1" --dataset-id "NAMESPACE/turkish-direct-response-sft-v1" --model-license apache-2.0 --dataset-license cc-by-4.0 --rights-reviewed
```

Bu bayrak senin kontrol beyanındır, betik lisans doğrulaması yapmış sayılmaz.
Kartların TODO alanlarını bitir, seçilen lisansların tam metinlerini ilgili
depolara ekle; upstream atıf/NOTICE yükümlülüklerini kontrol et. Eğitim ve CETVEL
çalışma ortamları farklıdır; config + orijinal ortam kanıtını birlikte kullan.

## Hugging Face'e yükleme

Önce web arayüzünden iki **private** depo oluştur. Güncel `hf` CLI ile:

```powershell
hf auth login
hf upload NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1 "NEW_RELEASE_PATH/model" . --repo-type model
hf upload NAMESPACE/turkish-direct-response-sft-v1 "NEW_RELEASE_PATH/dataset" . --repo-type dataset
```

Tokenı kaynak koda, komuta veya bloga yazma; oturum açma akışını kullan.
Model deposunda `adapter_model.safetensors`, `adapter_config.json`, `README.md`,
eğitim configi ve manifest; veri deposunda `data/train.jsonl`,
`data/validation.jsonl`, `README.md`, manifest ve kaynak dökümü bulunmalı.
85MB adaptör bağımsız4B model değildir; başlangıç ağırlıkları ayrıca indirilir.

İndirilen ağırlık hashini yeniden doğrula, veri görüntüleyicide104/20 satırı
kontrol et. Taze ortamda karttaki yükleme örneğini doğrula (bu aşamada yeni GPU
kiralanmadı). Ardından depoları public yap, yayımlanan **commit/revision**
kimliklerini kartlara ve bloga yaz; GitHub commitine sabit bağlantı ekle.
Bir HF Collection altında model/veri/blogu bir araya getirmek isteğe bağlıdır.
GitHub push da ayrıca yapılmalı; bu görev yalnızca yerel commit oluşturur.

## Kullanılabilecek duyuru cümlesi

“Qwen3.5-4B için104 insan denetimli Türkçe örnekle eğittiğimiz bir LoRA adaptörünü
paylaşıyoruz. Amaç daha kısa, doğrudan ve daha az süslü cevaplar. Beş görevden
oluşan500 soruluk yerel CETVEL kaynaklı değerlendirmede ve30 kör insan incelemesinde
üslup/tercih kazanımı gördük; özetleme sadakati hâlâ sınırlı. Genel Türkçe veya
akıl yürütme yeteneğinin her görevde arttığını iddia etmiyoruz.”

## Güncel birincil kaynaklar

- [Model kartları](https://huggingface.co/docs/hub/model-cards)
- [PEFT adaptör paylaşımı](https://huggingface.co/docs/hub/peft)
- [Veri kartları](https://huggingface.co/docs/hub/datasets-cards)
- [CLI ile yükleme](https://huggingface.co/docs/huggingface_hub/guides/upload)
- [HF blog erişim koşulları](https://huggingface.co/docs/hub/blog-articles)
- [Sabit başlangıç model kartı/lisans](https://huggingface.co/unsloth/Qwen3.5-4B/blob/3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636/README.md)

Kaynaklar2026-10-04 tarihinde kontrol edildi. Platform koşulları değişebilir.
