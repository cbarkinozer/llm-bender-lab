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
