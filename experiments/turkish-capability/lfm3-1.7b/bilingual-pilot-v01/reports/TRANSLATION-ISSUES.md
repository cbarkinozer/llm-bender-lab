# Translation and original-quality issue report

Status: agent-authored translations; the reviewed Turkish originals were **not** changed. Items below are suspected mistakes,
ambiguities or unverifiable claims found while inspecting every original, plus translation decisions. Severity is the agent's
judgement, not an owner ruling. Legal/historical/product claims were preserved verbatim and not independently source-verified.

## Summary

- Originals with at least one suspected issue / ambiguity / unverified claim: **33 of 160**
- By severity: {'medium': 15, 'low': 19}
- By type: {'mistake_suspected': 22, 'ambiguity': 5, 'time_sensitive': 2, 'verification': 4, 'formatting': 1}
- Translation-decision notes by type: {'language_intrinsic': 15, 'noise_lost': 3, 'register_translation': 2, 'register': 1, 'language_bound_output': 6, 'translation_choice': 1, 'entity_preserved': 1, 'entity_translation': 1, 'localization': 9, 'language_neutral_output': 1, 'gloss': 10, 'verification': 22, 'task_note': 1, 'length_constraint': 1}

## A. Suspected mistakes, ambiguities and unverified claims in the reviewed originals (owner decision needed)

| Sev | Group | Source row | Category | Type | Note |
|---|---|---|---|---|---|
| medium | g012 | `atlas:train.chat.jsonl:234323` | grammar_and_morphology | mistake_suspected | Comma guidance on the three conjunction "ki" is inconsistent/debatable: the first two get a comma, the third ("yönetiyor ki") does not, and the claim that a purpose-result "ki" never takes a comma is a style position, not a firm rule. Also the explanation says the only spelling mistake was "mektubun daki" although "ki" punctuation was also changed. Reviewed original left unchanged; owner may want to re-review. |
| medium | g028 | `cot:train.jsonl:223` | arithmetic_and_constraints | ambiguity | The 1100 TL "total fuel cost" constraint is interpreted by the original as the cost of fuel PURCHASED en route (535.68 TL); the initial full tank is not priced. If the whole 62.4 L trip were costed (~2,808 TL at 45 TL/L) the constraint would be infeasible. The prompt does not state which is meant. Also arrival in Mersin with 0 L reserve is accepted. Arithmetic otherwise verified (1040 km; 62.4 L; 43.2 and 41.4 TL/L; 535.68 and 513.36 TL). |
| medium | g030 | `cot:train.jsonl:2583` | logic_and_critical_reasoning | mistake_suspected | Legal citations (Law 4735, Const. Art. 56, Law 2872, Law 5393 Art. 14, Council of State doctrine) were NOT independently verified here. Constitution Art. 56 is described as making pollution prevention "directly a duty of the state"; the article text assigns the duty to "the state and citizens", so the original is partly imprecise. Left unchanged; owner may want legal re-review. Translation preserves all citations verbatim. |
| medium | g035 | `cot:train.jsonl:3510` | arithmetic_and_constraints | ambiguity | The prompt omits shift length; the reviewed answer resolves this by assuming 4-hour shifts and that all six workers must be assigned. The assumption is stated in the answer, but one specific resolution is imposed. Plan verified: shifts 2/2/2, Ali/Veli separate, Fatma on day, 6*4=24. "çalışan-saat" rendered "employee-hours". |
| medium | g066 | `sft:TR-part1-261025_v1-fixed.jsonl:2144` | legal_explanation | mistake_suspected | Legal citations (Const. Art. 17/28, ECHR Art. 8/10, Von Hannover No. 2, Axel Springer, Law 5651, Constitutional Court/ECtHR blanket-block case law) were not independently verified; translation preserves them verbatim. Owner may want legal re-review. |
| medium | g067 | `sft:TR-part1-261025_v1-fixed.jsonl:2236` | legal_explanation | mistake_suspected | Legal citations (TTK Arts. 369, 553, 555, 557; TBK Arts. 50-51; Law 3095; HMK) not independently verified; translation preserves them verbatim. Owner may want legal re-review. |
| medium | g068 | `sft:TR-part1-261025_v1-fixed.jsonl:227` | technical_method_and_analysis | mistake_suspected | Original answer contains apparent typos: "Buradaki taka" (should be "takas", trade-off) and "Takayı görünür kılan adım" (should be "Takası"). Left unchanged in the TR rows; EN rendering uses "trade-off". The bird name "kızkuşu" is uncertain: kept in Turkish with "a shorebird" gloss rather than guessing a species. |
| medium | g075 | `sft:TR-part1-261025_v1-fixed.jsonl:3840` | planning_and_advice | time_sensitive | Product-capability and privacy-policy claims (Alexa lacks Turkish support; Amazon cloud-processing change in 2025; Google 3/18/36-month auto-delete; Apple HomeKit Secure Video) are time-sensitive and were not verified. Preserved verbatim; consider owner re-check before wide use. |
| medium | g095 | `sft:TR-part1-261025_v1-fixed.jsonl:1750` | legal_explanation | mistake_suspected | Procedural-law claims and article numbers (HMK Arts. 116/1-b, 117, 407 et seq.) not independently verified; EN rendering of the Turkish petition template keeps Turkish procedural structure. Owner may want legal re-review. |
| medium | g102 | `cot:train.jsonl:4314` | legal_explanation | mistake_suspected | Legal citations (HMK Art. 27, Const. Art. 36, ECHR Art. 6, Court of Cassation practice) not independently verified; preserved verbatim. |
| medium | g112 | `sft:TR-part1-261025_v1-fixed.jsonl:2244` | legal_explanation | mistake_suspected | Legal citations (TTK Arts. 369, 393, 202, 553) not independently verified; preserved verbatim. Owner may want legal re-review. |
| medium | g139 | `sft:TR-part1-261025_v1-fixed.jsonl:2118` | legal_explanation | mistake_suspected | Constitutional/treaty citations (Const. Arts. 2, 57, 65; ICESCR Art. 11; UN interpretation) not independently verified; the quoted Art. 57 text is the original's paraphrase of the official wording (ellipsis "Devlet ... konut ihtiyacını"). Preserved verbatim. TOKİ (Mass Housing Administration) kept as an acronym. |
| medium | g153 | `cot:train.jsonl:4066` | arithmetic_and_constraints | mistake_suspected | The prompt is internally inconsistent (stated average density 1.012*1.007=1.019084 vs 1.019583 implied by the 1:1.4 volume ratio). The reasoning says the inconsistency should be noted in the answer, but the reviewed assistant message gives only the two volumes and does NOT mention it; it also uses no sentence form. Left unchanged; owner may want to re-review. Volumes verified: 252.92 and 354.08. |
| medium | g154 | `sft:TR-part1-261025_v1-fixed.jsonl:1078` | conceptual_explanation | mistake_suspected | The prompt asks for "doğru künyeli" (correctly cited) examples, but poem attributions and descriptions ("Açların Gözbebekleri", the quoted Kuvâyi Milliye line, etc.) were not independently verified and may be unreliable; hallucination risk in a bibliographic task. Titles/quotes kept in Turkish verbatim with English glosses. Owner may want literary re-review. |
| medium | g159 | `sft:TR-part1-261025_v1-fixed.jsonl:2194` | legal_explanation | mistake_suspected | Legal citations (Const. Arts. 38, 152; TCK Art. 2 and 2/3; ECHR Art. 7; Kokkinakis v. Greece) not independently verified; preserved verbatim. Owner may want legal re-review. |
| low | g011 | `atlas:train.chat.jsonl:224324` | structured_extraction | mistake_suspected | Original answer headers use "Öncelik" (with diacritic) although the prompt requested the column spelled 'Oncelik'; the answer also adds a 'Zaman' column header not named in the prompt (data does contain times). Left unchanged. |
| low | g014 | `atlas:train.chat.jsonl:312719` | arithmetic_and_constraints | ambiguity | "kâr marjı" (margin on price) vs markup on cost is a known ambiguity; the reviewed answer resolves it explicitly (675 TL; 648 TL would result under markup). Arithmetic verified: 450/0.8=562.5; 562.5*1.2=675. |
| low | g029 | `cot:train.jsonl:247` | logic_and_critical_reasoning | ambiguity | Original rejects all five options as the answer (flawed question); translation preserves this. Fallacy names rendered with standard English equivalents. |
| low | g037 | `cot:train.jsonl:466` | clarification_and_uncertainty | mistake_suspected | The flush count 5,148 includes straight/royal flushes (stated only in the reasoning); the standard "flush" excluding straight flushes is 5,108 (≈0.1965%). The answer text defines flush only as "5 cards of the same suit" so 0.198% is consistent with its own definition. Combinatorics otherwise verified (123,552; 5,148; 2,598,960; ratio ~24). Left unchanged. |
| low | g052 | `occam:data/train.jsonl:6` | grammar_and_morphology | mistake_suspected | The original answer also changes a comma to a semicolon, a punctuation change beyond the requested "spelling" correction (only "bina dan" -> "binadan" is a spelling error). Left unchanged. |
| low | g060 | `occam:data/train.jsonl:91` | planning_and_advice | ambiguity | Original source sentence "Şefin işaretini bazı kişiler göremediğini söyledi" has no explicit subject for "söyledi" (who said); rendered "The conductor said" as the most natural reading, matching the answer's use of the conductor's cue. |
| low | g068 | `sft:TR-part1-261025_v1-fixed.jsonl:227` | technical_method_and_analysis | verification | Ramsar sites Kızılırmak and Gediz Deltas taken from the original; not independently verified. |
| low | g071 | `sft:TR-part1-261025_v1-fixed.jsonl:3064` | conceptual_explanation | verification | Cited facts (Ezel Akay film 2006, UNESCO inscription 2009, Ottoman "Karagöz" newspaper, TRT series) not independently verified; preserved verbatim. |
| low | g097 | `atlas:train.chat.jsonl:201637` | structured_extraction | mistake_suspected | Original answer lines carry no bullet markers although "three bullet points" were requested, and it intensifies "Risk: Maliyet" to "yüksek maliyet riski" (high cost risk). Left unchanged. |
| low | g100 | `sft:TR-part1-261025_v1-fixed.jsonl:1691` | rewriting_and_summary | mistake_suspected | Reviewed summary omits two conditions from the source (original packaging; no reason required). Compression is acceptable but conditions are dropped. Left unchanged. The required prefix "Kısaca:" is rendered "In short:" in the EN variant. |
| low | g104 | `cot:train.jsonl:1406` | planning_and_advice | mistake_suspected | Answer quality issues in the reviewed original: the "Net Effect" formula double-counts (opportunity cost is the flip side of the saving) and its signs are confusing; the answer's headline says "causal effect" though the prompt does not; "annual up-front payment reduces loss aversion" is an unsupported behavioral claim; 7,200/18,000 = 40% is described as "close to half". Arithmetic verified (600/month; 1,500 allowance; 18,000/year; 900 left). Left unchanged. |
| low | g105 | `cot:train.jsonl:166` | logic_and_critical_reasoning | verification | Historical dates (30 Oct 1918, 19 May 1919, 22 Jun 1919, Dörtyol 19 Dec 1918, Erzurum Jul-Aug 1919, Sivas Sep 1919) consistent with standard accounts; not independently source-checked. "Milli Mücadele" rendered "the National Struggle". |
| low | g106 | `sft:TR-part1-261025_v1-fixed.jsonl:4645` | clarification_and_uncertainty | time_sensitive | The answer avoids giving figures (good) but states net pay is "about 30-40% below gross"; this tax-dependent claim is unverified. Turkish job-site names kept (kariyer.net, yenibiris). |
| low | g111 | `sft:TR-part1-261025_v1-fixed.jsonl:1241` | conceptual_explanation | verification | Historical claims (Jewish/Armenian/Greek printing dates; Müteferrika 1727/1729) not independently verified; preserved verbatim. |
| low | g113 | `sft:TR-part1-261025_v1-fixed.jsonl:5074` | planning_and_advice | formatting | The original answer's bullet "Birkaç isabetli hashtag ve güncel trend kullan:" has no bullet marker (formatting glitch); the EN variant reproduces the same glitch so the four variants stay structurally parallel. |
| low | g115 | `atlas:train.chat.jsonl:274051` | rewriting_and_summary | mistake_suspected | The reviewed answer adds details not in the data ("theoretical framework has been established", "fieldwork phase has begun") although the prompt supplies only three facts. Left unchanged. Length constraint (<=120 words) is checked by the validator. |
| low | g121 | `atlas:train.chat.jsonl:54523` | rewriting_and_summary | mistake_suspected | The reviewed answer adds details not in the data ("motion-sensing", "annual basis", "total operational energy costs"). Left unchanged. Length constraint (<=150 words) checked by the validator. |
| low | g140 | `atlas:train.chat.jsonl:62684` | arithmetic_and_constraints | mistake_suspected | Arithmetic verified: 800. Note the prompt says 40% were "very satisfied" while the question asks how many were "satisfied" (conflates very satisfied with satisfied); original answer treats them as the same. Left unchanged. |
| low | g148 | `atlas:train.chat.jsonl:227972` | grounded_comprehension | mistake_suspected | The original answer says climate change being "responsible at a rate of 60%" makes it "the main cause", an inference beyond the text (the prompt forbids adding comments); it also rephrases the 60% as "60% of the fires". Left unchanged. Arithmetic verified: 50-45=5. |

## B. Translation decisions and language-bound content

| Sev | Group | Type | Note |
|---|---|---|---|
| low | g004 | language_intrinsic | Spelling-correction task on Turkish text: Turkish material quoted verbatim in EN prompt and EN answer; only the explanations are translated. |
| low | g007 | language_intrinsic | Turkish word analysed: morphemes kept in Turkish, glosses translated. Original total-meaning line adds "sürecimiz" (our process), a paraphrase not a morpheme; kept. |
| low | g011 | noise_lost | TR source prompt is ASCII-folded Turkish (no diacritics: "ogrenci", "asi takvimi", "Oncelik"), a robustness feature that cannot be reproduced in the EN input variant. |
| low | g012 | language_intrinsic | Turkish grammar of "ki"; Turkish text and examples quoted verbatim in EN variants. |
| low | g015 | language_intrinsic | Turkish word analysed: morphemes kept in Turkish, glosses translated. |
| low | g018 | register_translation | Turkish slang ("birbirine sallıyor", "falan kalmadı", "valla") rendered with English colloquial equivalents; exact register can only be approximated. |
| low | g019 | language_intrinsic | Turkish word analysed: morphemes kept in Turkish, glosses translated. |
| low | g022 | language_intrinsic | Historical proper names (Yeniçeri Ocağı -> Janissary Corps; Tanzimat Fermanı -> Tanzimat Edict) kept recognisable. Original answer mixes formal user prompt ("belirtin") with informal 2nd person ("kabul edersen"); preserved as "you". |
| low | g027 | register | Original answer addresses the user informally ("Senin karşı-olgusalının") while the prompt is impersonal; preserved as "your counterfactual". Prompt wording "önerme" rendered "proposition". |
| low | g033 | language_intrinsic | The quoted Turkish question "Neden bu kadar geç kaldın?" ("Why are you so late?") is the object sentence of the task; kept verbatim in Turkish inside EN variants (a Turkish word order point is part of the premises). "devrik cümle" rendered "inverted sentence". |
| low | g034 | language_intrinsic | Turkish grammar term "bağlı cümle" rendered "conjoined sentence"; Turkish conjunction list (ve, ama, fakat, çünkü) rendered with English equivalents. The rule is stipulated by the prompt. |
| low | g041 | language_bound_output | The task corrects a Turkish sentence (person agreement "öğrendim" -> "öğrendiniz"); the only possible answer is Turkish text. Assistant content is identical for TR and EN output directions, so the "answer in English" instruction has no effect (output_language_effect=none). |
| low | g044 | language_intrinsic | Turkish "doktora" (PhD) vs "doktor" (physician) contrast rendered "PhD program" vs "doctor"; the distraction partly relies on the Turkish word similarity and is weaker in English. |
| low | g051 | language_bound_output | The task selects a Turkish lexical item (kır vs kir). The Turkish words stay verbatim in the EN prompt; answer "kir" is identical for TR and EN output directions (output_language_effect=none). Glosses of the two words were translated. |
| low | g052 | language_bound_output | Turkish spelling correction; Turkish sentence verbatim in prompt and answer; identical answer for TR and EN output directions (output_language_effect=none). |
| low | g055 | language_bound_output | Turkish spelling correction ("tekrarlamıyınca" -> "tekrarlamayınca"); Turkish sentence verbatim; identical answer for TR and EN output directions (output_language_effect=none). |
| low | g057 | translation_choice | The user's flawed message is not quoted in the source, so the corrected message is simply the target-language equivalent (EN: "I haven't given you the book yet; I still have it."). The TR answer "Kitabı sana henüz vermedim, hâlâ bende." is unchanged. |
| low | g058 | entity_preserved | Catalog product names (Kül Grisi, Deniz Mavisi, Kum Beji) kept verbatim as entity names rather than translated to Ash Grey / Sea Blue / Sand Beige; answer identical for TR and EN output directions (output_language_effect=none). |
| low | g081 | language_intrinsic | The Turkish answer's adverbial-participle example ("Güneş batınca sokak lambaları yandı") has no exact English conjunction-free counterpart; rendered with an English absolute participle. The TR prompt quotes Turkish sentences; the EN prompt quotes their English equivalents (task is conjunction-free joining, not Turkish-bound). |
| low | g087 | language_intrinsic | The contrast relies on Turkish "doktora" (PhD) vs "doktor" (physician); English "doctorate" vs "doctor" preserves it but the lexical-similarity trap is weaker. |
| low | g089 | language_intrinsic | The ambiguity stems from Turkish possessive "kitabını" (his/her book). The EN variant recreates it with the English pronoun "his" (gender must be chosen in English). The TR rows keep the original sentence. |
| low | g093 | register_translation | Turkish text mixes Turkish slang with English loanwords (status, milestone, weekly report) and Turkish chat abbreviations (tmm, slm, bi); the English variant replaces them with English chat abbreviations/colloquialisms. |
| low | g098 | noise_lost | TR source prompt is ASCII-folded Turkish (no diacritics); not reproducible in the EN input variant. |
| low | g119 | language_intrinsic | The task is about the figurative sense of Turkish "akıl" (reason/mind/brain). The EN variant recreates it with English "mind" ("the mind behind this project"); the exact sense mapping (akıl sağlığı = mental health, "sound mind") is only approximate. TR rows keep the original word and options. |
| low | g123 | language_bound_output | Turkish spelling/punctuation correction (diacritics, capitalization, comma). Turkish text verbatim; assistant text identical for TR and EN output directions (output_language_effect=none). |
| low | g130 | language_intrinsic | Turkish word analysed: morphemes kept in Turkish, glosses translated. |
| low | g131 | noise_lost | TR source prompt is ASCII-folded Turkish (no diacritics); not reproducible in the EN input variant. Arithmetic verified: 240/60=4. |
| low | g133 | language_intrinsic | Turkish idiom "elinize sağlık" (lit. "health to your hands", praise for completed work) rendered "well done"; the Turkish answer also uses the formal "siz" form. |
| low | g135 | language_bound_output | Turkish spelling correction ("hiçbirşey" -> "hiçbir şey"); the Turkish sentence is quoted verbatim in the EN prompt and the answer is the corrected Turkish sentence, identical for TR and EN output directions (output_language_effect=none). |
| low | g143 | entity_translation | Institution names are descriptive and were translated ("Fen Lisesi Müdürlüğü" -> "The Science High School Directorate"). Original wording "Aşağıdaki metne göre" ("according to the following text") points to text that appears above; preserved literally. |
| info | g001 | localization | Labels “Durum”/“Etki” rendered as “Status”/“Effect” in prompt and answer consistently. |
| info | g002 | localization | Turkish ordinal connectors rendered as English connectors; sequence preserved. |
| info | g006 | localization | Structured column keys urun/miktar/tarih kept verbatim in EN prompt and table (the task fixes the keys); "adet" -> "units". |
| info | g010 | language_neutral_output | Output is pure JSON with no natural-language content: assistant text is identical in TR and EN output directions (expected duplicate content across directions). |
| info | g011 | gloss | Turkish acronym KKK (kızamık-kızamıkçık-kabakulak) rendered as the standard English acronym MMR. |
| info | g013 | localization | Number formatting localized (5000 -> 5,000; %36 -> 36%; −%36'ya karşı +%5 -> −36% versus +5%). Arithmetic verified: 5000-3200=1800=36%; 4725-4500=225=5%; 36+5=41. |
| info | g014 | localization | Decimal comma -> decimal point (562,50 -> 562.50; 0,80 -> 0.80). |
| info | g016 | localization | "usta" (master craftsman) rendered as neutral "worker". Arithmetic verified: 36-12=24. |
| info | g017 | gloss | "KVKK" expanded as "the Turkish data protection law (KVKK)" for an English reader. |
| info | g021 | localization | Arithmetic verified (8000*0.1*3=2400; total 10400). Number format localized. "Ayşe Hanım" -> "Mrs. Ayşe". |
| info | g023 | localization | Arithmetic verified: h=0.5*9.8*1.8^2=15.876; v=17.64; E=0.5*600*17.64^2~93.3 kJ. Decimal commas localized in prose and LaTeX. |
| info | g024 | verification | R^2=-I verified by matrix multiplication; (3,7)->(-3,-7). |
| info | g025 | verification | Arithmetic verified: 432 reps; 2332.8 s; 38.88 min = 38 min 52.8 s ~ 38 min 53 s. Decimal commas localized. |
| info | g026 | verification | Arithmetic verified: 2610 s = 43.5 min. "kendi sporcusu" rendered "their athlete" (no gender stated). |
| info | g031 | verification | Solution verified: x=7.5, y=13.75. |
| info | g036 | verification | Arithmetic verified: 90*0.2=18. |
| info | g038 | verification | 0.012*64=0.768. Option letters/values unchanged apart from decimal point. |
| info | g061 | gloss | "SHGM" expanded as "the Directorate General of Civil Aviation (SHGM)". The answer asserts that SHGM has urban-air-mobility regulations and local noise regulation exists; these regulatory claims were not verified. |
| info | g062 | gloss | Turkish proverb kept verbatim with a literal English gloss in the prompt and first answer sentence. |
| info | g063 | gloss | Turkish proverb kept with English equivalent in parentheses. |
| info | g064 | verification | Cited literature facts (Hesiod, Aeschylus, Plato's Protagoras, Frankenstein 1818 subtitle, Anders "Promethean gap", Jonas, 2018 CRISPR births) are consistent with common knowledge but were not independently source-checked; the Tevfik Fikret "Promete" attribution not verified. |
| info | g070 | task_note | The prompt provides no message; the reviewed answer asks for it (clarification behavior). Preserved. |
| info | g074 | gloss | "KKK aşısı" rendered "MMR vaccine"; e-Nabız (Turkish national health records system) and emergency number 112 kept (Turkey-specific content retained). Vaccination guidance not clinically verified. |
| info | g076 | verification | Arithmetic verified: 2*150*52=15,600. |
| info | g082 | verification | Arithmetic verified: dx=2.1213-2=0.1213; dy=4-2.1213=1.8787; d=1.8826; theta=3.69 degrees. Decimal commas localized; "K 3,7° D" -> "N 3.7° E". |
| info | g084 | verification | x=-2 verified. |
| info | g094 | gloss | Turkish authorities and laws expanded for English readers (SGK, BDDK, EPDK, TTK, KVKK). Legal statements not independently verified. |
| info | g103 | length_constraint | The prompt demands 50-80 words and the EN answer is 76 words (checked by the validator); the TR original is checked separately. |
| info | g107 | gloss | Turkish proverb kept verbatim with a literal English gloss in the prompt; EN answer keeps the proverb in Turkish in the final paragraph. |
| info | g108 | verification | Arithmetic verified: 270,000. |
| info | g109 | verification | Arithmetic verified: A=60, R=40. |
| info | g116 | verification | Arithmetic verified: 96/2=48. |
| info | g118 | verification | Arithmetic verified: 28,000 and 21,000. |
| info | g120 | verification | Optimality verified by enumeration: salad+soup+2 bread = 46 g protein at 570 kcal is the maximum under 600 kcal. |
| info | g124 | gloss | SPK/BDDK expanded as "Capital Markets Board (SPK) / Banking Regulation and Supervision Agency (BDDK)". |
| info | g126 | localization | Turkey-specific police number 155 retained. |
| info | g127 | verification | Arithmetic verified: 1200; 30%. "Fatma Teyze" -> "Aunt Fatma" (honorific). |
| info | g129 | verification | 4^5=1024 so n=6. |
| info | g136 | verification | Arithmetic verified: 80-60=20. (Original answer contains a trailing space after "alıyor." which is preserved in the TR text; EN keeps the same line structure.) |
| info | g137 | gloss | "KVKK" expanded as "the Turkish data protection law (KVKK)". |
| info | g138 | verification | Verified: capacity bound 3 < rule bound 5; distribution 4,2,3,3 satisfies the rule. |
| info | g150 | verification | Verified: floor(log2 4096)+1 = 13. |
| info | g151 | verification | Arithmetic verified: 20:30 total; 04:00 UTC departure; 00:30 UTC arrival; 04:00 Tehran time next day. |
| info | g156 | verification | Arithmetic verified: 45; 15; 5 each; 25/20/15; weekly 75/60/45. |
