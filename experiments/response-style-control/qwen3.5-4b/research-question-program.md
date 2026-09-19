# 4B Model Research Question Program

Bu dosya, Qwen3.5-4B ile yürütülecek uzun vadeli deney programının soru
havuzudur. Amaç rastgele fine-tuning yapmak değil; her soruyu ölçülebilir bir
hipoteze, kontrollü bir deneye ve yayınlanabilir bir bulguya dönüştürmektir.

## Program fikri

Her döngüde tek bir araştırma sorusu seçilecek. Soru için:

1. İlgili makaleler ve mevcut bulgular okunacak.
2. Falsifiable bir hipotez yazılacak.
3. 4B modelinde mümkün olan en küçük kontrollü deney tasarlanacak.
4. Base model, uygun baseline ve yeni yöntem aynı protokolle ölçülecek.
5. Ham çıktılar, konfigürasyon, GPU/çalışma maliyeti ve metrikler saklanacak.
6. Sonuçlar literatürle karşılaştırılacak.
7. Yaklaşık üç günde bir soru için ilk sonuç alınacak; büyük sorular birkaç
   küçük alt deneye bölünecek.

Üç günlük süre, nihai makale sonucu değil, ilk güvenilir sinyal hedefidir.
Belirsiz veya olumlu sonuç veren sorular daha uzun deneylere taşınabilir.

## Her soru için kayıt şablonu

```markdown
## Q-XXX — Başlık

- Status: backlog | active | completed | deferred
- Scope: 3-day pilot | multi-week project | long-term
- Hypothesis:
- Null hypothesis:
- Model and revision:
- Baselines:
- Training change:
- Evaluation set and metric:
- Confounds and controls:
- Expected cost/time:
- Literature to read:
- Result:
- Monthly/quarterly synthesis:
```

## Deney kuralları

- Her deney tek ana değişkeni değiştirmeli.
- Benchmark soruları eğitim verisine sızmamalı.
- Aynı prompt, seed, decoding ve veri revizyonu kaydedilmeli.
- Base model ve aday model aynı koşullarda karşılaştırılmalı.
- Sadece loss düşüşü başarı sayılmamalı; görev metriği ve hata analizi gerekli.
- Olumsuz sonuçlar da saklanmalı; başarısız hipotezler silinmemeli.
- 4B model kapasitesi, eğitim süresi ve test-time compute açıkça raporlanmalı.
- Her ay kısa, üç ayda bir kapsamlı sentez yapılmalı.
- Birleştirilebilen ve güçlü bulgu üreten deneyler daha sonra makale taslağına
  dönüştürülebilir.

## Öncelikli kısa deneyler

Bu sorular 4B modelinde küçük veri, sınırlı compute ve mevcut benchmark altyapısı
ile birkaç günlük pilotlara bölünebilir.

### Q-001 — Thinking Türkçe performansını iyileştiriyor mu?

**Soru:** Thinking destekli 4B Qwen3.5, thinking kapalı moda göre Türkçe
doğruluk, doğal ifade ve görev tamamlama açısından daha iyi mi?

Karşılaştırma: aynı promptların thinking açık/kapalı sürümleri. Ayrı olarak
Türkçe doğruluk, doğallık, gereksiz uzunluk ve halüsinasyon ölçülmeli. Thinking
token'ları görünür cevap puanına karıştırılmamalı.

### Q-002 — Dışsal görev tahtası uzun görevleri iyileştirir mi?

**Soru:**

> Can a 4B coding model, trained to manage an explicit external task board,
> perform asymmetric verification, and coordinate file-level work through
> sandboxed execution and output leases, reliably outperform a similarly sized
> single-agent ReAct baseline on long-horizon multi-file software engineering
> tasks—and how much of any gain comes from the coordination structure itself
> rather than simply increased test-time compute?

İlk pilotta yalnızca küçük, çok dosyalı görevler kullanılmalı. Baseline aynı
   test-time token/araç bütçesine sahip olmalı; aksi halde coordination ile
   compute artışı birbirine karışır.

### Q-003 — Runtime state machine, ağırlıkları değiştirmeden güvenilirliği artırır mı?

**Soru:**

> Can a 4B coding model with frozen weights become substantially more reliable
> on long-horizon software engineering tasks by externalizing execution state
> into an agent-driven state machine, refreshing phase-local context, and
> enforcing independently verified transition contracts—and how much of the
> improvement comes from the runtime structure itself rather than task-specific
> runbook instructions?

Bu soru Q-002 ile birleştirilmemeli: burada ağırlıklar dondurulmuş runtime
   etkisi ölçülür. Runbook-only, state-machine-only ve birleşik ablation gerekir.

### Q-004 — Birkaç örnekten görülmemiş program dönüşümleri öğrenilebilir mi?

**Soru:**

> Can a 4B coding model learn previously unseen program transformations from a
> few demonstrations at inference time and solve them through recurrent latent
> computation—without chain-of-thought tokens, weight updates, or a growing KV
> cache—and where do extrapolation and composition begin to break down?

Bu ileri seviye bir pilot sorusudur. Önce sentetik, doğrulanabilir program
   dönüşümleriyle compositional generalization benchmarkı gerekir.

## Eğitim ve mimari soruları

### Q-005 — MoE fine-tuning için en güvenli yöntem nedir?

Karşılaştırılacak değişkenler: bf16 LoRA, full fine-tuning, router katmanlarını
   dondurma/açma, expert-only adapter ve farklı expert yük dengesi. Ölçümler:
   görev başarısı, router/load balance, VRAM, throughput ve catastrophic
   forgetting.

### Q-006 — Text-diffusion model nasıl fine-tune edilir?

Önce modelin hedef objective'i, masking/noising prosedürü ve decoding protokolü
   sabitlenmeli. Autoregressive modelle doğrudan loss karşılaştırması yeterli
   değildir; kalite, iterasyon sayısı, latency, controllability ve uzun metin
   tutarlılığı ayrı raporlanmalı.

### Q-007 — Vision encoder'lı ve text-only Qwen3.5-4B farkı

**Soru:** Image desteği korunmuş Qwen3.5-4B ile vision encoder'ı çıkarılmış
text-only varyant, aynı text görevlerinde kalite, VRAM, throughput ve fine-tuning
stabilitesi açısından nasıl ayrılır?

Kontrol: aynı language weights, aynı tokenizer, aynı context ve aynı decoding.
Vision encoder'ı çıkarmanın model config, processor ve checkpoint uyumluluğuna
etkisi ayrıca belgelenmeli. Bu yalnızca performans sorusu değil, mimari değişim
ve dağıtım sorusudur.

## Uzun vadeli araştırma soruları

### Q-008 — Self-teacher ile disagreement-only distillation

**Soru:**

> By conditioning a 4B self-teacher on majority-voted reasoning traces and
> distilling only into disagreeing rollouts, can we match or outperform ground
> truth distillation on coding tasks?

Gerekli kontroller: ordinary self-distillation, ground-truth distillation,
majority-vote without distillation, disagreement selection ablation ve aynı
   toplam teacher-token bütçesi.

Bu soru üç günlük tek deney değil; önce küçük coding görevleriyle feasibility
   pilotu yapılmalı.

### Q-009 — TDD-first fine-tuning ile kod doğruluğu ve süreç güvenilirliği

**Soru:** Bir 4B coding modeline, kullanıcı açıkça istemese bile önce
gereksinimleri netleştirmeyi, bu gereksinimleri doğrulayan unit testleri yazmayı,
sonra implementasyon yapmayı ve testleri çalıştırarak sonucu doğrulamayı öğreten
SFT; aynı görevlerde doğrudan kod yazan bir baseline'a göre test geçme oranını,
gereksinim kapsamını ve hata ayıklama başarısını artırır mı?

**Hedef politika:** Model, kod yazmadan önce gereksinimleri çıkarır ve belirsiz
noktaları sorar; ardından test planını ve unit testleri üretir; en son kodu yazar,
testleri çalıştırır ve başarısız test varsa bunu görmezden gelmeden düzeltme
döngüsüne girer. Kullanıcı “test yazma” dese bile model, doğruluk iddiası için
testlerin gerekli olduğunu kısa ve teknik biçimde belirtir.

**Kontrollü deney tasarımı:**

- `direct-code` baseline: aynı görevlerde doğrudan implementasyon.
- `tdd-policy`: requirements → tests → implementation → test execution → fix.
- `requirements-only` ablation: gereksinim çıkarma var, test-first yok.
- `tests-only` ablation: test yazma var, açık requirements adımı yok.
- Her koşulda aynı model revision, görevler, araç bütçesi, seed ve timeout.
- Testlerin doğru ve görevi gerçekten kapsayıp kapsamadığı, gizli evaluator ve
  insan örneklemesiyle ayrıca denetlenmeli; yalnızca modelin kendi testlerini
  geçmesi başarı kabul edilmemeli.

**Bir görevin ideal rollout şeması:**

1. Requirements: kabul kriterleri, varsayımlar ve açık sorular.
2. Tests: başarısız olacak en az bir başlangıç testi, normal durumlar,
   sınır durumları ve hata durumları.
3. Implementation: testleri hedefleyen minimal kod değişikliği.
4. Execution: test komutu, stdout/stderr, exit code ve süre kaydı.
5. Repair: başarısız testler için sınırlı düzeltme döngüsü.
6. Final report: değişen dosyalar, çalıştırılan komutlar ve kalan riskler.

**Birincil metrikler:** gizli test-suite pass rate, ilk denemede pass rate,
nihai pass rate, gereksinim kapsamı, test kalitesi (mutation score veya seeded
bug detection), düzeltme başarısı ve yanlış güven (modelin tüm testler geçmeden
başarılı rapor vermesi). İkincil metrikler token/araç çağrısı, latency, dosya
değişikliği, test başına maliyet ve insan değerlendirmesidir.

**Ana risk:** Modelin zayıf veya eksik testler yazarak kendisini “başarılı”
göstermesi. Bu nedenle değerlendirme testleri eğitim rollout'larından gizli
tutulmalı, test kalitesi bağımsız mutation/hidden-test ölçümüyle raporlanmalı ve
SFT verisinde requirements ile testlerin birbirini sızdırmadığı kontrol edilmelidir.

Bu soru, yalnızca cevap biçimi fine-tune'ı değil, araç kullanan agentik bir
workflow fine-tune'ını gerektirir; ilk pilot küçük Python repository görevleriyle
başlatılmalı ve her rollout'un ham terminal kayıtları saklanmalıdır.

## Aylık ve üç aylık sentez

Her ay:

- tamamlanan pilotlar ve negatif sonuçlar özetlenir,
- aynı değişkeni ölçen deneyler gruplanır,
- tekrarlanması gereken sonuçlar seçilir,
- sonraki ayın tek değişkenli soruları belirlenir.

Her üç ayda:

- yalnızca tekrarlanmış ve kontrol edilmiş bulgular birleştirilir,
- literatürle çelişen veya uyumlu sonuçlar ayrılır,
- compute/maliyet ve sınırlılıklar raporlanır,
- yeterli kanıt varsa makale taslağı hazırlanır.

## İlk çalışma sırası

1. Q-001: thinking açık/kapalı Türkçe karşılaştırması.
2. Q-002 veya Q-003: küçük çok-dosyalı coding pilotu.
3. Q-005: MoE fine-tuning feasibility notu.
4. Q-007: vision/text-only mimari karşılaştırması.
5. Q-004 ve Q-008: gerekli sentetik benchmark ve compute bütçesi hazırlandıktan
   sonra.
