# Stratified translation sample for owner inspection

17 of 160 task groups: 6 mandatory edge cases (language-bound, noise, length constraint, figurative sense, inconsistent prompt) plus up to 2 per (source x reasoning) bucket, random.Random(3407), groups with <= 3,600 characters only.

For each group check: (1) is the English faithful (numbers, units, entities, negation, time, constraints, answer)? (2) is it natural English?
(3) is the Turkish original untouched? (4) is the language instruction natural? Reasoning is shown only where the original has it.

The four rows per group reuse exactly these texts: tr-tr = original + instruction; en-tr = EN prompt + original answer; tr-en = original prompt + EN answer; en-en = EN prompt + EN answer.

## g005 · atlas:train.chat.jsonl:133694 · planning_and_advice · atlas · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Tez konumu belirlerken iki metodoloji arasında kaldım: Yalnızca literatür taraması mı yapmalıyım, yoksa ampirik deney tabanlı bir çalışma mı yürütmeliyim? Esneklik, risk ve maliyet kriterlerine göre bu iki seçeneği kıyaslayan bir tablo hazırla ve öneride bulun.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
While deciding on my thesis topic I'm torn between two methodologies: should I do only a literature review, or carry out an empirical experiment-based study? Prepare a table comparing these two options by the criteria of flexibility, risk and cost, and give a recommendation.

Answer in English.
```

**TR answer (original)**

```text
| Kriter | Literatür Taraması | Ampirik Deney |
|---|---|---|
| Esneklik | Yüksek: Kapsam ve zamanlama çalışma boyunca kolayca daraltılıp genişletilebilir. | Düşük: Deney tasarımı ve örneklem bir kez belirlendikten sonra değiştirmek zordur. |
| Risk | Düşük-orta: Veri toplama riski yoktur, ancak özgün katkı sınırlı kalabilir ve bazı programlar yalnızca literatüre dayanan tezleri kabul etmeyebilir. | Yüksek: Etik kurul onayı, katılımcı bulma güçlüğü veya beklenen sonucun çıkmaması gibi nedenlerle gecikmeler yaşanabilir. |
| Maliyet | Düşük: Temelde veri tabanı erişimi ve zaman gerektirir. | Yüksek: Ekipman, malzeme, katılımcı ücreti veya laboratuvar erişimi gerektirebilir. |

Öneri: Önce bölümünüzün tez yönergesine ve danışmanınızın görüşüne bakın; bazı programlar ampirik bir bileşen şart koşar. Böyle bir zorunluluk yoksa ve zamanınız ile bütçeniz kısıtlıysa literatür taraması daha güvenli seçenektir; sistematik derleme gibi yapılandırılmış bir yöntem kullanırsanız özgün bir katkı da sunabilirsiniz. Akademik kariyer hedefliyorsanız ya da alanınız deneysel ağırlıklıysa, kapsamı dar ve kontrol edilebilir küçük bir ampirik çalışma size daha değerli bir deneyim kazandırır.

```

**EN answer (translation)**

```text
| Criterion | Literature Review | Empirical Experiment |
|---|---|---|
| Flexibility | High: Scope and timing can easily be narrowed and widened throughout the study. | Low: Once the experimental design and sample have been set, they are hard to change. |
| Risk | Low-medium: There is no data collection risk, but the original contribution may remain limited and some programs may not accept theses based solely on literature. | High: Delays may occur because of ethics committee approval, difficulty finding participants, or the expected result not materializing. |
| Cost | Low: Essentially requires database access and time. | High: May require equipment, materials, participant fees or laboratory access. |

Recommendation: First check your department's thesis guidelines and your advisor's opinion; some programs require an empirical component. If there is no such requirement and your time and budget are limited, a literature review is the safer option; if you use a structured method such as a systematic review, you can also make an original contribution. If you are aiming for an academic career or your field is experiment-heavy, a small empirical study with a narrow, controllable scope will give you a more valuable experience.

```

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g007 · atlas:train.chat.jsonl:173494 · grammar_and_morphology · atlas · reasoning=no · EN-output effect=preserve_turkish_object

**TR prompt (original + instruction)**

```text
Akademik olarak “Raporlaştırılmamızdaki” kelimesini morfolojik olarak açıklar mısın?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
Could you explain the word “Raporlaştırılmamızdaki” morphologically, in an academic manner?

Explain in English; preserve the requested Turkish text.
```

**TR answer (original)**

```text
raporlaştırılmamızdaki = rapor + -laş + -tır + -ıl + -ma + -mız + -da + -ki

rapor: kök (isim).
-laş-: isimden fiil yapım eki; rapor → raporlaş-.
-tır-: ettirgenlik eki; raporlaş- → raporlaştır- (“rapor haline getirmek”).
-ıl-: edilgenlik eki; raporlaştır- → raporlaştırıl- (“rapor haline getirilmek”).
-ma: fiilden isim yapan ek (isim-fiil); raporlaştırılma (“rapor haline getirilme”).
-mız: 1. çoğul şahıs iyelik eki; raporlaştırılmamız (“bizim rapor haline getirilmemiz”).
-da: bulunma durumu eki.
-ki: aitlik (ilgi) eki; bulunma ekine bitişik yazılır.

Toplam anlam: “rapor haline getirilme sürecimizin içinde yer alan (şey)”.

```

**EN answer (translation)**

```text
raporlaştırılmamızdaki = rapor + -laş + -tır + -ıl + -ma + -mız + -da + -ki

rapor: root (noun).
-laş-: suffix forming a verb from a noun; rapor → raporlaş-.
-tır-: causative suffix; raporlaş- → raporlaştır- (“to put into report form”).
-ıl-: passive suffix; raporlaştır- → raporlaştırıl- (“to be put into report form”).
-ma: suffix forming a noun from a verb (verbal noun); raporlaştırılma (“being put into report form”).
-mız: 1st person plural possessive suffix; raporlaştırılmamız (“our being put into report form”).
-da: locative case suffix.
-ki: relational (belonging) suffix; written attached to the locative suffix.

Overall meaning: “(the thing) located within our process of being put into report form”.

```

**Agent flags**

- [low] language_intrinsic: Turkish word analysed: morphemes kept in Turkish, glosses translated. Original total-meaning line adds "sürecimiz" (our process), a paraphrase not a morpheme; kept.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g011 · atlas:train.chat.jsonl:224324 · structured_extraction · atlas · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Bir ogrenci olarak asagidaki 'asi takvimi' verilerini markdown tablosu seklinde sun. 'Oncelik' sutunu ekle. Gereksiz giris cumlesi kurma.

Veri:
- Hepatit B: 0. ay, Oncelik 1
- BCG: 2. ay, Oncelik 2
- KKK: 12. ay, Oncelik 3

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
As a student, present the following 'vaccine schedule' data as a markdown table. Add a 'Priority' column. Do not write an unnecessary introductory sentence.

Data:
- Hepatitis B: month 0, Priority 1
- BCG: month 2, Priority 2
- MMR: month 12, Priority 3

Answer in English.
```

**TR answer (original)**

```text
| Aşı | Zaman | Öncelik |
|---|---|---|
| Hepatit B | 0. ay | 1 |
| BCG | 2. ay | 2 |
| KKK | 12. ay | 3 |

```

**EN answer (translation)**

```text
| Vaccine | Time | Priority |
|---|---|---|
| Hepatitis B | Month 0 | 1 |
| BCG | Month 2 | 2 |
| MMR | Month 12 | 3 |

```

**Agent flags**

- [low] noise_lost: TR source prompt is ASCII-folded Turkish (no diacritics: "ogrenci", "asi takvimi", "Oncelik"), a robustness feature that cannot be reproduced in the EN input variant.
- [low] mistake_suspected: Original answer headers use "Öncelik" (with diacritic) although the prompt requested the column spelled 'Oncelik'; the answer also adds a 'Zaman' column header not named in the prompt (data does contain times). Left unchanged.
- [info] gloss: Turkish acronym KKK (kızamık-kızamıkçık-kabakulak) rendered as the standard English acronym MMR.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g014 · atlas:train.chat.jsonl:312719 · arithmetic_and_constraints · atlas · reasoning=yes · EN-output effect=full

**TR prompt (original + instruction)**

```text
Bir ürünün birim maliyeti 450 TL. %20 kâr marjı ile satmayı planlıyoruz. KDV oranı %20 olduğuna göre, müşteriye sunacağımız KDV dahil satış fiyatı kaç TL olur?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
The unit cost of a product is 450 TL. We plan to sell it with a 20% profit margin. Given that the VAT rate is 20%, what would the VAT-inclusive selling price to the customer be, in TL?

Answer in English.
```

**TR answer (original)**

```text
KDV dahil satış fiyatı 675 TL olur. %20 kâr marjı için KDV hariç fiyat 450 / 0,80 = 562,50 TL olmalıdır. %20 KDV eklendiğinde 562,50 × 1,20 = 675 TL elde edilir. Maliyetin üzerine %20 eklemek ise kâr marjı değil, maliyet üzerinden kâr oranıdır.
```

**EN answer (translation)**

```text
The VAT-inclusive selling price is 675 TL. For a 20% profit margin, the price excluding VAT must be 450 / 0.80 = 562.50 TL. When 20% VAT is added, 562.50 × 1.20 = 675 TL is obtained. Adding 20% on top of the cost, however, is not a profit margin but a markup on cost.
```

**TR reasoning (original)**

```text
Kâr marjı, kârın KDV hariç satış fiyatına oranıdır. Satış fiyatına S dersek (S - 450) / S = 0,20 olur. Buradan 0,80S = 450 ve S = 562,50 TL bulunur. KDV 562,50 × 0,20 = 112,50 TL; toplam 675 TL olur.
```

**EN reasoning (translation)**

```text
Profit margin is the ratio of profit to the selling price excluding VAT. If we call the selling price S, then (S - 450) / S = 0.20. From this, 0.80S = 450 and S = 562.50 TL. VAT is 562.50 × 0.20 = 112.50 TL; the total is 675 TL.
```

**Agent flags**

- [low] ambiguity: "kâr marjı" (margin on price) vs markup on cost is a known ambiguity; the reviewed answer resolves it explicitly (675 TL; 648 TL would result under markup). Arithmetic verified: 450/0.8=562.5; 562.5*1.2=675.
- [info] localization: Decimal comma -> decimal point (562,50 -> 562.50; 0,80 -> 0.80).

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g031 · cot:train.jsonl:269 · arithmetic_and_constraints · cot · reasoning=yes · EN-output effect=full

**TR prompt (original + instruction)**

```text
Bir bakkalda elmanın kilosu x TL, armudun kilosu y TL’dir. Ali 3 kg elma ve 2 kg armut alıp 50 TL, Ayşe ise 2 kg elma ve 4 kg armut alıp 70 TL ödemiştir. x ve y’yi bulmak için iki bilinmeyenli denklem sistemini kurun ve yerine koyma yöntemiyle adım adım çözerek elma ile armudun kilogram fiyatını bulun.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
At a grocery store, apples cost x TL per kilogram and pears cost y TL per kilogram. Ali bought 3 kg of apples and 2 kg of pears and paid 50 TL, while Ayşe bought 2 kg of apples and 4 kg of pears and paid 70 TL. To find x and y, set up the system of equations with two unknowns and solve it step by step using the substitution method to find the per-kilogram prices of apples and pears.

Answer in English.
```

**TR answer (original)**

```text
Denklem sistemi şöyle kurulur:
3x + 2y = 50 (Ali’nin alışverişi)
2x + 4y = 70 (Ayşe’nin alışverişi)

Yerine koyma yöntemiyle çözelim. Birinci denklemden y yalnız bırakılır: y = (50 − 3x) / 2. Bu ifade ikinci denklemde yerine konur: 2x + 4·(50 − 3x)/2 = 70, yani 2x + 2(50 − 3x) = 70. Parantez açılıp sadeleştirilince 2x + 100 − 6x = 70, buradan −4x = −30 ve x = 7,5 bulunur. Bu değer y ifadesinde yerine konunca y = (50 − 22,5)/2 = 13,75 çıkar.

Kontrol: Ali için 3·7,5 + 2·13,75 = 22,5 + 27,5 = 50 ✓; Ayşe için 2·7,5 + 4·13,75 = 15 + 55 = 70 ✓.

Sonuç: elmanın kilosu 7,5 TL, armudun kilosu 13,75 TL’dir.
```

**EN answer (translation)**

```text
The system of equations is set up as follows:
3x + 2y = 50 (Ali's purchase)
2x + 4y = 70 (Ayşe's purchase)

Let us solve by the substitution method. From the first equation, y is isolated: y = (50 − 3x) / 2. This expression is substituted into the second equation: 2x + 4·(50 − 3x)/2 = 70, that is, 2x + 2(50 − 3x) = 70. Expanding the parentheses and simplifying gives 2x + 100 − 6x = 70, from which −4x = −30 and x = 7.5. When this value is substituted into the expression for y, y = (50 − 22.5)/2 = 13.75.

Check: for Ali, 3·7.5 + 2·13.75 = 22.5 + 27.5 = 50 ✓; for Ayşe, 2·7.5 + 4·13.75 = 15 + 55 = 70 ✓.

Result: apples cost 7.5 TL per kilogram and pears cost 13.75 TL per kilogram.
```

**TR reasoning (original)**

```text
Denklemler: 3x + 2y = 50 (Ali), 2x + 4y = 70 (Ayşe).
Yerine koyma: 1. denklemden y = (50 − 3x) / 2.
2. denkleme koy: 2x + 4·(50 − 3x)/2 = 70 → 2x + 2(50 − 3x) = 70 → 2x + 100 − 6x = 70 → −4x = −30 → x = 7,5.
y = (50 − 22,5)/2 = 13,75.
Kontrol: Ali 22,5 + 27,5 = 50 ✓, Ayşe 15 + 55 = 70 ✓.
```

**EN reasoning (translation)**

```text
Equations: 3x + 2y = 50 (Ali), 2x + 4y = 70 (Ayşe).
Substitution: from the 1st equation y = (50 − 3x) / 2.
Put into the 2nd equation: 2x + 4·(50 − 3x)/2 = 70 → 2x + 2(50 − 3x) = 70 → 2x + 100 − 6x = 70 → −4x = −30 → x = 7.5.
y = (50 − 22.5)/2 = 13.75.
Check: Ali 22.5 + 27.5 = 50 ✓, Ayşe 15 + 55 = 70 ✓.
```

**Agent flags**

- [info] verification: Solution verified: x=7.5, y=13.75.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g033 · cot:train.jsonl:2987 · logic_and_critical_reasoning · cot · reasoning=yes · EN-output effect=full

**TR prompt (original + instruction)**

```text
Şu öncüller veriliyor: (1) Bütün devrik cümleler söz diziminde farklılık gösterir. (2) Devrik cümle olmayan bazı cümleler de söz diziminde farklılık gösterir. (3) Hiçbir soru cümlesi devrik cümle değildir. (4) “Neden bu kadar geç kaldın?” bir soru cümlesidir. Bu dört öncülden tümdengelimle çıkarılabilecek tüm kesin sonuçları yazın; çıkarılamayacak olanları da gerekçesiyle belirtin.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
You are given the following premises: (1) All inverted sentences differ in word order. (2) Some sentences that are not inverted sentences also differ in word order. (3) No question sentence is an inverted sentence. (4) “Neden bu kadar geç kaldın?” is a question sentence. Write down all the certain conclusions that can be deduced from these four premises; also state those that cannot be deduced, with reasons.

Answer in English.
```

**TR answer (original)**

```text
Öncüllerden gerçekten yeni olarak çıkarılabilen tek kesin sonuç şudur:

¬D(a): “Neden bu kadar geç kaldın?” devrik cümle değildir. (Öncül 3'e göre hiçbir soru cümlesi devrik değildir; Öncül 4'e göre bu bir soru cümlesidir.)

Buna ek olarak Öncül 3, “Hiçbir cümle hem soru hem devrik olamaz” (∀x ¬(S(x) ∧ D(x))) biçiminde yeniden yazılabilir; ancak bu yeni bir çıkarım değil, Öncül 3'ün eşdeğeridir ve Öncül 1'i kullanmaz.

Öncüllerden çıkarılamayacak olanlar:

“Neden bu kadar geç kaldın?” söz diziminde farklılık gösterir → çıkarılamaz; a devrik olmadığından, “bütün devrik cümleler farklılık gösterir” kuralı onun için bir şey söylemez.
“Bazı devrik cümleler farklılık gösterir” → geçersiz; tümelden tikele geçilemez.
“Bütün devrik olmayan cümleler farklılık gösterir” → geçersiz; Öncül 2 yalnızca “bazı” der.
“Bazı/bütün soru cümleleri farklılık gösterir” → geçersiz; öncüller desteklemez.
```

**EN answer (translation)**

```text
The only certain conclusion that can genuinely be derived as new from the premises is this:

¬D(a): “Neden bu kadar geç kaldın?” is not an inverted sentence. (According to Premise 3, no question sentence is inverted; according to Premise 4, this is a question sentence.)

In addition, Premise 3 can be rewritten as “No sentence can be both a question and inverted” (∀x ¬(S(x) ∧ D(x))); however, this is not a new inference but an equivalent of Premise 3, and it does not use Premise 1.

Those that cannot be derived from the premises:

“Neden bu kadar geç kaldın?” differs in word order → cannot be derived; since a is not inverted, the rule “all inverted sentences differ” says nothing about it.
“Some inverted sentences differ” → invalid; one cannot move from the universal to the particular.
“All non-inverted sentences differ” → invalid; Premise 2 says only “some.”
“Some/all question sentences differ” → invalid; the premises do not support it.
```

**TR reasoning (original)**

```text
D(x): devrik, F(x): söz dizimi farkı, S(x): soru; a = “Neden bu kadar geç kaldın?”.
1: ∀x(D→F), 2: ∃x(¬D∧F), 3: ∀x(S→¬D), 4: S(a).
Yeni çıkarım: 3 + 4 → ¬D(a).
“Hiçbir cümle hem soru hem devrik olamaz” ∀x¬(S∧D): bu, 3'ün eşdeğeri (S→¬D ≡ ¬(S∧D)), yeni sonuç değil; Öncül 1 kullanılmaz.
F(a) belirsiz: ¬D(a) olduğu için 1 (D→F) a hakkında bir şey söylemez (önbileşeni yadsıma).
Tümelden tikele geçiş ve 2'yi tümele çevirme girişimleri geçersiz.
```

**EN reasoning (translation)**

```text
D(x): inverted, F(x): word-order difference, S(x): question; a = “Neden bu kadar geç kaldın?”.
1: ∀x(D→F), 2: ∃x(¬D∧F), 3: ∀x(S→¬D), 4: S(a).
New inference: 3 + 4 → ¬D(a).
“No sentence can be both a question and inverted” ∀x¬(S∧D): this is equivalent to 3 (S→¬D ≡ ¬(S∧D)), not a new conclusion; Premise 1 is not used.
F(a) is undetermined: since ¬D(a), 1 (D→F) says nothing about a (denying the antecedent).
Attempts to move from universal to particular and to turn 2 into a universal are invalid.
```

**Agent flags**

- [low] language_intrinsic: The quoted Turkish question "Neden bu kadar geç kaldın?" ("Why are you so late?") is the object sentence of the task; kept verbatim in Turkish inside EN variants (a Turkish word order point is part of the premises). "devrik cümle" rendered "inverted sentence".

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g041 · occam:data/train.jsonl:1 · grammar_and_morphology · occam · reasoning=no · EN-output effect=preserve_turkish_object

**TR prompt (original + instruction)**

```text
Bir kişiye siz diye hitap ederek "Siz bu tekniği nerede öğrendim?" yazmışım. Yalnızca düzeltilmiş soruyu yaz.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
I addressed someone formally with “siz” and wrote “Siz bu tekniği nerede öğrendim?” Write only the corrected question.

Answer in English; preserve the requested Turkish text.
```

**TR answer (original)**

```text
Siz bu tekniği nerede öğrendiniz?
```

**EN answer (translation)**

```text
Siz bu tekniği nerede öğrendiniz?
```

**Agent flags**

- [low] language_bound_output: The task corrects a Turkish sentence (person agreement "öğrendim" -> "öğrendiniz"); the only possible answer is Turkish text. Assistant content is identical for TR and EN output directions, so the "answer in English" instruction has no effect (output_language_effect=none).

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g081 · sft:TR-part1-261025_v1-fixed.jsonl:2376 · rewriting_and_summary · sft · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Şu iki cümleyi bağlaç kullanmadan akıcı tek bir ifadeye dönüştür:
“Güneş battı. Sokak lambaları yandı.”

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
Turn these two sentences into a single fluent expression without using a conjunction:
“The sun set. The street lamps came on.”

Answer in English.
```

**TR answer (original)**

```text
En yalın yol, iki cümleyi virgülle sıralamak:

Güneş battı, sokak lambaları yandı.

Noktalı virgül de aynı işi görür, araya biraz daha belirgin bir duraklama koyar: “Güneş battı; sokak lambaları yandı.” Zarf-fiille (“Güneş batınca sokak lambaları yandı”) da bağlaçsız birleşir, ama bu biçim araya bir zaman/neden bağı ekler; sadece art arda akıtmak istiyorsan virgül yeterli.

```

**EN answer (translation)**

```text
The simplest way is to line the two sentences up with a comma:

The sun set, the street lamps came on.

A semicolon does the same job and places a slightly more noticeable pause in between: “The sun set; the street lamps came on.” An absolute participial construction (“The sun having set, the street lamps came on”) also joins them without a conjunction, but this form adds a time/cause link in between; if you only want to run them one after another, the comma is enough.

```

**Agent flags**

- [low] language_intrinsic: The Turkish answer's adverbial-participle example ("Güneş batınca sokak lambaları yandı") has no exact English conjunction-free counterpart; rendered with an English absolute participle. The TR prompt quotes Turkish sentences; the EN prompt quotes their English equivalents (task is conjunction-free joining, not Turkish-bound).

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g089 · occam:data/train.jsonl:63 · clarification_and_uncertainty · occam · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Öğretmen öğrencisine kitabını verdi cümlesinde kitap kimin?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
In the sentence "The teacher gave the student his book", whose book is it?

Answer in English.
```

**TR answer (original)**

```text
Cümle bu hâliyle belirsizdir. "Kitabını" sözcüğü hem öğretmenin hem de öğrencinin kitabı anlamına gelebilir, bağlam olmadan kesin bir şey söylenemez. Belirsizliği gidermek için "kendi kitabını" ya da "öğrencinin kitabını" demek gerekir.
```

**EN answer (translation)**

```text
As it stands, the sentence is ambiguous. The word "his" can mean either the teacher's or the student's book, and nothing definite can be said without context. To remove the ambiguity, one would need to say "the teacher's own book" or "the student's book".
```

**Agent flags**

- [low] language_intrinsic: The ambiguity stems from Turkish possessive "kitabını" (his/her book). The EN variant recreates it with the English pronoun "his" (gender must be chosen in English). The TR rows keep the original sentence.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g103 · atlas:train.chat.jsonl:51813 · rewriting_and_summary · atlas · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Aşağıdaki döviz kuru etki raporu verilerini kullanarak resmî bir tonda tek paragraflık bir metin yaz. Metin 50-80 kelime olmalı, tam olarak 2 risk ve 2 aksiyon içermeli. Belirsiz ifadeler kullanma.

Etken: TL’nin değer kaybı
Riskler: İthalat maliyetlerinin artması, kâr marjının daralması
Aksiyonlar: Hedge pozisyonu alma, tedarikçi kontratlarını yeniden müzakere etme

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
Using the exchange rate impact report data below, write a single-paragraph text in a formal tone. The text must be 50-80 words and must contain exactly 2 risks and 2 actions. Do not use vague expressions.

Factor: Depreciation of the lira (TL)
Risks: Increase in import costs, narrowing of profit margin
Actions: Taking a hedge position, renegotiating supplier contracts

Answer in English.
```

**TR answer (original)**

```text
Türk lirasındaki değer kaybı, şirketimiz için iki temel risk oluşturmaktadır. Birincisi, döviz cinsinden yapılan alımlar nedeniyle ithalat maliyetleri artmaktadır. İkincisi, artan maliyetlerin satış fiyatlarına tam olarak yansıtılamaması kâr marjlarını daraltmaktadır. Bu risklere karşı iki aksiyon uygulanacaktır. Döviz yükümlülükleri için vadeli işlem sözleşmeleriyle hedge pozisyonu alınacak ve tedarikçilerle mevcut kontratların fiyat ve ödeme koşulları yeniden müzakere edilecektir.
```

**EN answer (translation)**

```text
The depreciation of the Turkish lira poses two main risks for our company. First, import costs are rising because purchases are made in foreign currency. Second, the inability to fully pass the increased costs on to sales prices is narrowing profit margins. Two actions will be taken against these risks. A hedge position will be taken for foreign currency liabilities through forward contracts, and the price and payment terms of existing contracts with suppliers will be renegotiated.
```

**Agent flags**

- [info] length_constraint: The prompt demands 50-80 words and the EN answer is 76 words (checked by the validator); the TR original is checked separately.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g116 · cot:train.jsonl:1647 · arithmetic_and_constraints · cot · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Bir pastane her pastayı 12 eşit dilime ayırıyor. Bir düğün için 8 pasta sipariş ediliyor ve her davetliye 2 dilim veriliyor. Bu pastalar en fazla kaç davetliye yeter?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
A bakery cuts each cake into 12 equal slices. 8 cakes are ordered for a wedding and each guest is given 2 slices. For at most how many guests are these cakes enough?

Answer in English.
```

**TR answer (original)**

```text
Toplam dilim: 8 × 12 = 96
Davetli sayısı: 96 ÷ 2 = 48

```

**EN answer (translation)**

```text
Total slices: 8 × 12 = 96
Number of guests: 96 ÷ 2 = 48

```

**Agent flags**

- [info] verification: Arithmetic verified: 96/2=48.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g119 · cot:train.jsonl:4768 · grammar_and_morphology · cot · reasoning=yes · EN-output effect=full

**TR prompt (original + instruction)**

```text
“Akıl” sözcüğü aşağıdaki cümlelerin hangisinde mecaz anlamda kullanılmıştır?
A) İnsan, aklıyla düşünür ve karar verir.
B) Akıl sağlığı yerinde, dengeli bir insandı.
C) Bu projenin aklı, o genç mühendistir.
D) Çocuğun aklı soyut kavramları henüz kavrayamıyor.
E) Tıp bilimi, aklın işleyişini araştırıyor.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
In which of the following sentences is the word “mind” used figuratively?
A) A human thinks and makes decisions with their mind.
B) He was a person of sound mind and balance.
C) The mind behind this project is that young engineer.
D) The child's mind cannot yet grasp abstract concepts.
E) Medical science is investigating the workings of the mind.

Answer in English.
```

**TR answer (original)**

```text
Cevap: C

“Bu projenin aklı, o genç mühendistir.” Burada “akıl”, düşünme yetisi değil, projeyi planlayıp yürüten kişi (“beyin”) anlamında kullanılmıştır; bu mecaz anlamdır. Diğer şıklarda akıl, gerçek anlamıyla (düşünme ve muhakeme yetisi, akıl sağlığı) geçmektedir.

```

**EN answer (translation)**

```text
Answer: C

In “The mind behind this project is that young engineer.” the word “mind” is used not in the sense of the faculty of thinking but in the sense of the person who plans and runs the project (the “brain”); this is the figurative meaning. In the other options the word is used in its literal sense (the faculty of thinking and reasoning, mental health).

```

**TR reasoning (original)**

```text
Gerçek anlam: akıl = düşünme ve muhakeme yetisi. Şıklara bakalım. A’da yetiyle düşünmek, B’de akıl sağlığı, D’de çocuğun kavrama yetisi, E’de aklın işleyişi; dördü de gerçek anlam. C’de “projenin aklı o mühendistir” deniyor; burada akıl bir yeti değil, işi planlayıp yürüten kişi, yani “beyin” anlamında. Mecaz olan bu. Cevap C.
```

**EN reasoning (translation)**

```text
Literal meaning: mind = the faculty of thinking and reasoning. Let us look at the options. In A, thinking with the faculty; in B, mental health; in D, the child's faculty of comprehension; in E, the workings of the mind; all four are the literal meaning. In C it says “the mind behind the project is that engineer”; here mind is not a faculty but the person who plans and runs the work, that is, the “brain.” This is the figurative one. Answer C.
```

**Agent flags**

- [low] language_intrinsic: The task is about the figurative sense of Turkish "akıl" (reason/mind/brain). The EN variant recreates it with English "mind" ("the mind behind this project"); the exact sense mapping (akıl sağlığı = mental health, "sound mind") is only approximate. TR rows keep the original word and options.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g127 · cot:train.jsonl:8 · arithmetic_and_constraints · cot · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Fatma Teyze 4.000 TL’sini yıllık %10 basit faizle 3 yıllığına bankaya yatırıyor. 3 yılın sonunda elde ettiği faiz, anaparanın yüzde kaçıdır?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
Aunt Fatma deposits her 4,000 TL in the bank for 3 years at 10% annual simple interest. What percentage of the principal is the interest she earns at the end of the 3 years?

Answer in English.
```

**TR answer (original)**

```text
Faiz: 4.000 × 0,10 × 3 = 1.200 TL
Anaparaya oranı: 1.200 ÷ 4.000 = %30
Basit faizde bu oran doğrudan %10 × 3 = %30 olarak da bulunur; anapara sonucu etkilemez.

```

**EN answer (translation)**

```text
Interest: 4,000 × 0.10 × 3 = 1,200 TL
Ratio to the principal: 1,200 ÷ 4,000 = 30%
In simple interest, this ratio can also be found directly as 10% × 3 = 30%; the principal does not affect the result.

```

**Agent flags**

- [info] verification: Arithmetic verified: 1200; 30%. "Fatma Teyze" -> "Aunt Fatma" (honorific).

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g128 · atlas:train.chat.jsonl:35632 · grounded_comprehension · atlas · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Aşağıdaki pasaja dayanarak soruyu yanıtla. Pasajda olmayan bilgi ekleme.

Pasaj: Klasik müzik tarihinde Beethoven, klasik dönemden romantizme geçişin öncüsü oldu. Mozart bir çocuk dehasıydı ve 600'den fazla eser besteledi. Bach, barok dönemin ustasıdır. Viyana, müziğin başkenti hâline geldi. Piyano sonatları popülerdir. 19. yüzyılda orkestralar büyüdü. Opera, Verdi ile İtalyan karakteri kazandı. Caz 20. yüzyılda doğdu ve klasik müzik de cazdan etkilendi. Konser salonları akustiğe göre tasarlanır.

Soru: Pasaja göre klasik müzik tarihindeki başlıca gelişmeleri, bir yöneticiye sunulacak kısa bir özet olarak 3 maddede yaz.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
Answer the question based on the following passage. Do not add information that is not in the passage.

Passage: In the history of classical music, Beethoven was a pioneer of the transition from the classical period to romanticism. Mozart was a child prodigy and composed more than 600 works. Bach is the master of the baroque period. Vienna became the capital of music. Piano sonatas are popular. In the 19th century orchestras grew. Opera acquired its Italian character with Verdi. Jazz was born in the 20th century and classical music was also influenced by jazz. Concert halls are designed according to acoustics.

Question: According to the passage, write the main developments in the history of classical music in 3 items, as a short summary to be presented to a manager.

Answer in English.
```

**TR answer (original)**

```text
* Dönemler ve öncüler: Bach barok dönemin ustası. Mozart 600'den fazla eser besteledi. Beethoven romantizme geçişin öncüsü oldu.
* Büyüme ve merkezler: Viyana müziğin başkenti hâline geldi, 19. yüzyılda orkestralar büyüdü, opera Verdi ile İtalyan karakteri kazandı.
* Güncel etkiler: 20. yüzyılda doğan caz klasik müziği etkiledi. Piyano sonatları popülerliğini koruyor, konser salonları akustiğe göre tasarlanıyor.

```

**EN answer (translation)**

```text
* Periods and pioneers: Bach is the master of the baroque period. Mozart composed more than 600 works. Beethoven was a pioneer of the transition to romanticism.
* Growth and centers: Vienna became the capital of music, orchestras grew in the 19th century, and opera acquired its Italian character with Verdi.
* Current influences: Jazz, born in the 20th century, influenced classical music. Piano sonatas remain popular, and concert halls are designed according to acoustics.

```

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g139 · sft:TR-part1-261025_v1-fixed.jsonl:2118 · legal_explanation · sft · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Sosyal devlet ilkesi, barınma hakkı krizlerinde devlete hangi somut ödevleri yükler?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
What concrete duties does the principle of the social state impose on the state in housing-right crises?

Answer in English.
```

**TR answer (original)**

```text
Türkiye’de sosyal devlet ilkesi Anayasa’nın 2. maddesinde yer alır; konut hakkı ise 57. maddede düzenlenir: “Devlet ... konut ihtiyacını karşılayacak tedbirleri alır, ayrıca toplu konut teşebbüslerini destekler.” Türkiye’nin taraf olduğu Ekonomik, Sosyal ve Kültürel Haklar Sözleşmesi’nin 11. maddesi de “yeterli konut hakkını” tanır. Bu çerçevede devletin ödevleri üç başlıkta toplanır:

* Saygı gösterme: Kişileri keyfi ve hukuka aykırı biçimde evlerinden etmemek. Tahliyeler ancak yasal dayanağa, mahkeme kararına ve usul güvencelerine bağlı yapılabilir; BM’nin yorumuna göre toplu zorla tahliyeler kural olarak hak ihlalidir.
* Koruma: Konut ilişkisinde zayıf taraf olan kiracıyı üçüncü kişilere karşı korumak; kira ve tahliye hukukunu dengeleyici biçimde düzenlemek, uyuşmazlıklarda hukuki yardım sağlamak.
* Yerine getirme: Dar gelirliye sosyal ve uygun fiyatlı konut (örneğin TOKİ) ile kira yardımı sunmak; afet, salgın veya ekonomik kriz durumlarında evsiz kalanlara acil barınma sağlamak; kentsel dönüşümde yerinden edilenleri öncelikli olarak yeniden yerleştirmek.

Bu ödevlerin anayasal bir sınırı da vardır: 65. maddeye göre devlet sosyal ve ekonomik görevlerini “mali kaynakların yeterliliği ölçüsünde” yerine getirir. Yani konut hakkı, herkesin devletten doğrudan “bana konut ver” diye isteyebileceği bir hak değil, devlete tedbir alma ve politika yürütme yükümlülüğü getiren bir ilkedir.

```

**EN answer (translation)**

```text
In Türkiye, the principle of the social state is found in Article 2 of the Constitution; the right to housing is regulated in Article 57: “The State shall take measures to meet the need for housing and shall also support mass housing initiatives.” Article 11 of the International Covenant on Economic, Social and Cultural Rights, to which Türkiye is a party, also recognizes “the right to adequate housing.” Within this framework, the state's duties are gathered under three headings:

* Respect: Not evicting people from their homes arbitrarily and unlawfully. Evictions may be carried out only on the basis of a legal ground, a court decision and procedural safeguards; according to the UN's interpretation, mass forced evictions are as a rule a violation of the right.
* Protect: Protecting the tenant, the weaker party in the housing relationship, against third parties; regulating rent and eviction law in a balancing way, and providing legal aid in disputes.
* Fulfil: Offering social and affordable housing (for example TOKİ) and rent assistance to low-income people; providing emergency shelter to those left homeless in cases of disaster, epidemic or economic crisis; and giving priority to resettling those displaced in urban transformation.

These duties also have a constitutional limit: according to Article 65, the state fulfils its social and economic duties “to the extent of the adequacy of its financial resources.” That is, the right to housing is not a right by which everyone can directly demand “give me a home” from the state, but a principle that imposes on the state an obligation to take measures and carry out policy.

```

**Agent flags**

- [medium] mistake_suspected: Constitutional/treaty citations (Const. Arts. 2, 57, 65; ICESCR Art. 11; UN interpretation) not independently verified; the quoted Art. 57 text is the original's paraphrase of the official wording (ellipsis "Devlet ... konut ihtiyacını"). Preserved verbatim. TOKİ (Mass Housing Administration) kept as an acronym.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g153 · cot:train.jsonl:4066 · arithmetic_and_constraints · cot · reasoning=yes · EN-output effect=full

**TR prompt (original + instruction)**

```text
Van Gölü'nün iki ayrı tabakasından (yüzey ve dip) alınan su örneklerinin yoğunlukları 1,012 g/cm³ ve 1,025 g/cm³'tür. Her iki tabakadaki toplam kütlenin hacimce ağırlıklı ortalama yoğunluğu, yüzey tabakasının yoğunluğunun 1,007 katı kadardır. Toplam su hacmi 607 km³ ve dip tabakası hacminin yüzey tabakasının hacminin 1,4 katı olduğuna göre, iki tabakanın ayrı ayrı hacimlerini analojik oran kurarak bulup, dip tabakasının hacmini km³ cinsinden hesaplayınız.

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
The densities of water samples taken from two separate layers (surface and bottom) of Lake Van are 1.012 g/cm³ and 1.025 g/cm³. The volume-weighted average density of the total mass in both layers is 1.007 times the density of the surface layer. Given that the total water volume is 607 km³ and the volume of the bottom layer is 1.4 times the volume of the surface layer, find the volumes of the two layers separately by setting up an analogical ratio, and calculate the volume of the bottom layer in km³.

Answer in English.
```

**TR answer (original)**

```text
- Yüzey tabakası: 607 ÷ 2,4 ≈ 252,92 km³
- Dip tabakası: 607 × 1,4 ÷ 2,4 ≈ 354,08 km³

```

**EN answer (translation)**

```text
- Surface layer: 607 ÷ 2.4 ≈ 252.92 km³
- Bottom layer: 607 × 1.4 ÷ 2.4 ≈ 354.08 km³

```

**TR reasoning (original)**

```text
Hacimler doğrudan 1:1,4 oranından hesaplanabilir. Toplam 2,4 pay olduğundan yüzey hacmi 607/2,4 ≈ 252,92 km³, dip hacmi 607×1,4/2,4 ≈ 354,08 km³ olur. Ancak yoğunluk koşulunu da doğrulamak gerekir. Verilen ortalama yoğunluk 1,012×1,007 = 1,019084 g/cm³ iken hacim oranından hesaplanan değer (1,012+1,4×1,025)/2,4 ≈ 1,019583 g/cm³'tür. Koşullar çelişiyor. Yanıtta hacim oranına göre sonucu verip tutarsızlığı kısaca belirtmeliyim.
```

**EN reasoning (translation)**

```text
The volumes can be calculated directly from the 1:1.4 ratio. Since the total is 2.4 parts, the surface volume is 607/2.4 ≈ 252.92 km³ and the bottom volume is 607×1.4/2.4 ≈ 354.08 km³. However, the density condition also needs to be verified. While the given average density is 1.012×1.007 = 1.019084 g/cm³, the value calculated from the volume ratio is (1.012+1.4×1.025)/2.4 ≈ 1.019583 g/cm³. The conditions contradict each other. In the answer I should give the result according to the volume ratio and briefly note the inconsistency.
```

**Agent flags**

- [medium] mistake_suspected: The prompt is internally inconsistent (stated average density 1.012*1.007=1.019084 vs 1.019583 implied by the 1:1.4 volume ratio). The reasoning says the inconsistency should be noted in the answer, but the reviewed assistant message gives only the two volumes and does NOT mention it; it also uses no sentence form. Left unchanged; owner may want to re-review. Volumes verified: 252.92 and 354.08.

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---

## g157 · occam:data/train.jsonl:86 · planning_and_advice · occam · reasoning=no · EN-output effect=full

**TR prompt (original + instruction)**

```text
Ucuz iplik almak istiyorum ama makinemin kılavuzu bu kalınlığı kullanmayın diyor. Uyumlu iplik biraz pahalı; makineyle dikeceğim. Ucuz olanı seçeyim mi?

Yanıtını Türkçe ver.
```

**EN prompt (translation + instruction)**

```text
I want to buy cheap thread, but my machine's manual says not to use this thickness. The compatible thread is a bit more expensive; I will be sewing by machine. Should I choose the cheap one?

Answer in English.
```

**TR answer (original)**

```text
Hayır, uyumlu ipliği seçin; makinenizin kılavuzu ucuz ipliğin kalınlığını kullanmamanızı söylüyor ve siz makineyle dikeceksiniz.
```

**EN answer (translation)**

```text
No, choose the compatible thread; your machine's manual says not to use the cheap thread's thickness, and you will be sewing by machine.
```

- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes:

---
