# Correction report: the 15 medium-severity flagged originals

Nothing is applied. Exact before/after text is shown for every proposed edit; "RETAIN" items have no edit. Verification used the official Constitution PDF where marked VERIFIED; other web checks used secondary sources only.

## g153 · P1 · **FIX** · `cot:train.jsonl:4066`

Prompt: Van Gölü'nün iki ayrı tabakasından (yüzey ve dip) alınan su örneklerinin yoğunlukları 1,012 g/cm³ ve 1,025 g/cm³'tür. Her iki tabakadaki toplam kütlenin hacimce ağırlıklı ortalama yoğunluğu, yüzey tabakasının yoğunluğunun 1,007 katı kadardır. Toplam su hacmi 6

**Why:** Prompt is internally inconsistent (stated mean density 1.012x1.007=1.019084 vs 1.019583 implied by the 1:1.4 volumes; recomputed). The reviewed reasoning says the inconsistency must be mentioned but the answer omits it.

**Edit 1 (assistant) - before:**

```text
- Dip tabakası: 607 × 1,4 ÷ 2,4 ≈ 354,08 km³

```

**after:**

```text
- Dip tabakası: 607 × 1,4 ÷ 2,4 ≈ 354,08 km³

Not: Verilen ortalama yoğunluk koşulu (1,012 × 1,007 = 1,019084 g/cm³) hacim oranından hesaplanan değerle (≈ 1,019583 g/cm³) tutarsızdır; sonuç hacim oranına göre verilmiştir.

```

## g028 · P1 · **FIX** · `cot:train.jsonl:223`

Prompt: Ankara’dan yola çıkan bir satıcı Mersin’de bitirecektir; güzergâh Ankara → Konya (260 km) → Antalya (300 km) → Mersin (480 km). Aracın deposu 50 litre (dolu başlıyor), tüketim sabit 6 litre/100 km, yakıt 45 TL/litre. Konya’da istasyonda 10 dakika kuyruk ve %4

**Why:** Ambiguous constraint: if the 1100 TL limit covered the whole 62.4 L trip (~2,808 TL) it would be infeasible; the answer silently treats it as the cost of refuelled fuel (535.68 TL).

**Edit 1 (user) - before:**

```text
toplam yakıt maliyetinin 1100 TL’yi aşmaması
```

**after:**

```text
ikmal edilen yakıtın toplam maliyetinin 1100 TL’yi aşmaması
```

## g035 · P1 · **RETAIN** · `cot:train.jsonl:3510`

Prompt: Bir atölyede 6 işçi (Ali, Veli, Hüseyin, Ayşe, Fatma, Zeynep) 3 vardiyaya (gündüz, akşam, gece) dağıtılacaktır. Her vardiyada en az 1, en fazla 3 işçi olacak; Ali ile Veli aynı vardiyada çalışamaz; Fatma yalnızca gündüz vardiyasında çalışabilir; toplam çalışan

**Why:** Shift length is missing, but the reviewed answer opens by naming this gap and states its assumption (4 h shifts, all six assigned), which is the behaviour the system prompt asks for ("Belirsizliği belirt"). Fixing the prompt would make that answer redundant (larger rewrite). Alternative: DROP if you prefer well-posed tasks only.

**Edit 1 (user) - before:**

```text
toplam çalışan-saat 24'ü geçmemelidir
```

**after:**

```text
her vardiya 4 saat sürer ve toplam çalışan-saat 24'ü geçmemelidir   [only if FIX; answer paragraphs 1 and 4 would then need shortening]
```

## g068 · P1 · **FIX** · `sft:TR-part1-261025_v1-fixed.jsonl:227`

Prompt: Bir deltada sediman tutulumunun artışı ile su kuşu habitat uygunluğu arasındaki takası sayısallaştırmak için nasıl bir çerçeve kurulur?

**Why:** Objective typos: "taka" should be "takas" (trade-off); "Takayı" should be "Takası".

**Edit 1 (assistant) - before:**

```text
Buradaki taka, su kuşlarının
```

**after:**

```text
Buradaki takas, su kuşlarının
```

**Edit 2 (assistant) - before:**

```text
Takayı görünür kılan adım
```

**after:**

```text
Takası görünür kılan adım
```

## g030 · P2 · **FIX** · `cot:train.jsonl:2583`

Prompt: Bir belediyenin temizlik işleri müdürlüğü, çöp toplama ihalesini en düşük teklifi veren firmaya vermiş ama firmanın çevre yönetmeliklerine uyup uymadığını denetlememiştir. Firma dereye kaçak boşaltım yapmış ve çevre kirliliği oluşmuştur. Belediye yetkilisi “bi

**Why:** Wrong attribution. VERIFIED against the official Constitution text (mevzuat.gov.tr/mevzuatmetin/1.5.2709.pdf): Art. 56 says preventing pollution is "Devletin ve vatandaşların ödevidir".

**Edit 1 (assistant) - before:**

```text
çevre kirlenmesini önlemeyi doğrudan devletin ödevi sayar
```

**after:**

```text
çevre kirlenmesini önlemeyi devletin ve vatandaşların ödevi sayar
```

## g139 · P2 · **FIX** · `sft:TR-part1-261025_v1-fixed.jsonl:2118`

Prompt: Sosyal devlet ilkesi, barınma hakkı krizlerinde devlete hangi somut ödevleri yükler?

**Why:** Misquote. VERIFIED against the official text: Art. 65 reads "malî kaynaklarının yeterliliği ölçüsünde". (My earlier concern about the Art. 57 comma was wrong: the official text has a comma; no change there.)

**Edit 1 (assistant) - before:**

```text
“mali kaynakların yeterliliği ölçüsünde”
```

**after:**

```text
“mali kaynaklarının yeterliliği ölçüsünde”
```

## g012 · P2 · **FIX** · `atlas:train.chat.jsonl:234323`

Prompt: Şu cümledeki “ki” kullanımını ve yazım hatalarını düzeltir misin: “İş ortaklığı mektubun daki maddeler onaylandı ki bunlar çok kritik. Proje yöneticisi ki bu kişi çok tecrübeli, süreci yönetiyor ki ekip başarılı olsun.”

**Why:** Inconsistent rule: the first two conjunction "ki" get commas, the third is said never to; a comma before purpose-result "ki" is optional, not forbidden.

**Edit 1 (assistant) - before:**

```text
ve kendisinden önce virgül konmaz, tıpkı
```

**after:**

```text
ve önünde virgül zorunlu değildir, tıpkı
```

## g095 · P2 · **FIX** · `sft:TR-part1-261025_v1-fixed.jsonl:1750`

Prompt: Taraflar arasındaki sözleşmede tahkim şartı bulunmasına rağmen karşı taraf uyuşmazlığı devlet mahkemesine taşıdı. Bu davada tahkim itirazını (ilk itiraz) nasıl ileri sürmeliyim ve dilekçeyi nasıl yazmalıyım?

**Why:** Incomplete citation (secondary sources): HMK 116/1-b and 117 are right; the arbitration objection is also governed by HMK 413.

**Edit 1 (assistant) - before:**

```text
cevap süresi içinde ileri sürülmek zorundadır (HMK m. 117)
```

**after:**

```text
cevap süresi içinde ileri sürülmek zorundadır (HMK m. 117 ve 413)
```

## g075 · P3 · **FIX** · `sft:TR-part1-261025_v1-fixed.jsonl:3840`

Prompt: Evde kendi akıllı ev sistemimi kurmak istiyorum (örneğin ışıkları ve prizleri sesle kontrol etmek). Apple HomeKit, Google Home ve Amazon Alexa ekosistemlerinin birbirlerine göre avantajları ve gizlilik politikaları nelerdir?

**Why:** Time-sensitive product/privacy-policy claims (Alexa has no Turkish; 2025 Amazon cloud processing; Google retention options) will go stale.

**Edit 1 (assistant) - before:**

```text
ancak kurulumu daha fazla teknik bilgi ister.

```

**after:**

```text
ancak kurulumu daha fazla teknik bilgi ister.

Not: Ürün özellikleri ve gizlilik politikaları sık değişir; karar vermeden önce güncel resmî sayfaları kontrol edin.

```

## g154 · P3 · **FIX** · `sft:TR-part1-261025_v1-fixed.jsonl:1078`

Prompt: Nazım Hikmet’in şiirlerindeki toplumcu gerçekçilik unsurlarını, doğru künyeli şiir örnekleriyle açıklayınız.

**Why:** "Doğru künyeli" examples were requested. The Kuvâyi Milliye line was VERIFIED (Book 8 of Kuvâyi Milliye per secondary sources). "Açların Gözbebekleri" exists (written in Moscow, first free-verse poem) but its content description is unverified, so the minimal fix keeps only the verified Salkımsöğüt description.

**Edit 1 (assistant) - before:**

```text
“Açların Gözbebekleri” açlık çeken yığınları, “Salkımsöğüt” vurulup suya düşen bir Kızıl süvariyi anlatır.
```

**after:**

```text
“Salkımsöğüt” vurulup suya düşen bir Kızıl süvariyi anlatır.
```

## g066 · P3 · **RETAIN** · `sft:TR-part1-261025_v1-fixed.jsonl:2144`

Prompt: Şahsın korunmasına ilişkin tedbir kararlarında basın özgürlüğüyle denge nasıl kurulmalıdır?

**Why:** No error found. Von Hannover (No. 2) / Axel Springer criteria and Art. 17/28, ECHR 8/10 are real; Law 5651 blanket-block case law not verified. Optional lawyer check.

(no text change proposed)

## g067 · P3 · **RETAIN** · `sft:TR-part1-261025_v1-fixed.jsonl:2236`

Prompt: Anonim şirkette yönetim kurulu üyelerinin özen borcunu ihlal etmesi durumunda tazminat nasıl hesaplanır?

**Why:** No error found; TTK 369/553/555/557, TBK 50-51, Law 3095 not independently verified. Optional lawyer check.

(no text change proposed)

## g102 · P3 · **RETAIN** · `cot:train.jsonl:4314`

Prompt: İş mahkemesi, mobbing iddiasıyla açılan davada tanık dinlemeden karar vermiş ve davayı reddetmiştir. Bu yargılama eksikliği, adalete duyulan güveni nasıl sarsar ve ileride benzer davaları nasıl etkiler?

**Why:** No error found; HMK 27, Const. 36, ECHR 6 plausible/standard; "Yargıtay bozma sebebidir" not verified. Optional lawyer check.

(no text change proposed)

## g112 · P3 · **RETAIN** · `sft:TR-part1-261025_v1-fixed.jsonl:2244`

Prompt: Çapraz teminat uygulamalarında şirket yöneticilerinin sadakat borcu nasıl sınanır?

**Why:** TTK 393 (participation ban) confirmed by secondary sources; TTK 202, 369, 553 unverified but plausible. Optional lawyer check.

(no text change proposed)

## g159 · P3 · **RETAIN** · `sft:TR-part1-261025_v1-fixed.jsonl:2194`

Prompt: Suçta ve cezada kanunilik ilkesine aykırı belirsiz normların ceza hâkimi tarafından doldurulması meşru mudur?

**Why:** Const. 38/152, TCK 2 and 2/3, ECHR 7, Kokkinakis v. Greece are standard; not independently verified. Optional lawyer check.

(no text change proposed)

## What "apply recommended" would change

- FIX 9 groups: g153, g028, g068, g030, g139, g012, g095, g075, g154. RETAIN 6: g035, g066, g067, g102, g112, g159. DROP 0.
- Prompt edits: g028 (all four direction rows of the group change: TR prompt and its EN translation). Answer edits: g153, g068, g030, g139, g012, g095, g075, g154.
- Every fixed group needs its EN text updated (small edits to the matching `translations/part-*.txt` entries); TR rows change only at the quoted spans; group counts stay 160/640.
- Consequences: new dataset revision (new hashes in build-manifest, token plan and exp configs recalculated; the supervised-token totals shift by a few dozen tokens), `source-originals.jsonl` keeps the unedited reviewed text and gains a `correction` record. The frozen eval is unaffected.
