# Repair guide (exp-005)

You repair answers written by a small Turkish language model. Each row has a prompt (a Turkish task that carries its own data), the model's answer, and
the limits that code will check. Return the same answer with its errors fixed, nothing more. The repaired answer becomes the preferred answer of a
training pair and the model's own answer the rejected one, so the pair must differ only where the original is wrong.

## Input (one JSON object per line)

`id`, `prompt`, `answer` (the answer to repair), `limits_checked_by_code` (counts such as `max_words`, `bullets`, `exact_sentences`, `must_include`),
`answer_words`, `repaired_word_range` (`[low, high]`: the repaired answer must have a word count inside it).

## What counts as an error (fix these)

1. A claim that contradicts the prompt's data, reverses it (slower becomes faster), changes a number, or adds a fact, cause, name or recommendation that
   the data does not contain.
2. A required part is missing or wrong: a limit in the prompt or in `limits_checked_by_code` is broken (word, sentence or bullet count, required
   word, exactly N items, format such as a table or a paragraph), a banned thing is used (questions, abbreviations, personal opinion), or the answer
   does not do the task (answers a different question, adds commentary about itself).
3. Broken Turkish: invented or misspelled words, missing diacritics, wrong suffixes, English words that are not names or terms from the prompt,
   sentences that do not parse.
4. Repetition: the same statement said again.

Not errors (leave them): plainness, a formal or friendly tone that already fits, a correct but unremarkable answer, a different order of equal items.
A dull correct answer is fine. Do not improve style, add detail, or make it longer.

## Rules for the repaired answer

- Keep the answer's own words, structure and order wherever they are correct. Change only what is wrong. If most of it is wrong, still keep what you can.
- Use only information in the prompt. No outside facts, no new examples.
- Stay inside `repaired_word_range` (from 50% to 110% of the original's words; changed after the pilot, because removing invented content legitimately
  shortens an answer). Shorter is welcome when the original repeats itself, pads or invents; do not cut required content. Never pad to reach the
  range: if the true content cannot reach the lower end without invented filler, say so with `rewrite_needed`. Restating data that is in the
  prompt is allowed when a stated minimum (for example "en az 50 kelime") needs it.
- Cover every target the prompt names (each data point, each required part). When it asks for N items (suggestions, bullets), give N concrete items
  built from the data, not a filler item. (Added after the owner read of 30 pilot pairs: the three weak chosen answers missed a target, padded an
  item count or gave items that were not concrete.)
- Meet every limit exactly. Count before you answer. For lists write `- item` or `1. item` (not `1- item`). Decimal numbers such as 13,44 are fine.
- Real Turkish words with correct diacritics only. Keep names and terms from the prompt as they are.
- End like a finished answer. No preface ("İşte düzeltilmiş cevap"), no notes, no markdown fences around the whole answer.
- If the original uses a format the prompt asks for (table, bullets, JSON), keep that format.

## Output (one JSON object per input line, same `id`)

```json
{"id": "...", "verdict": "minimal", "chosen": "the complete repaired answer", "changes": ["short note per change"]}
```

`verdict`:
- `none`: the answer has no error. `chosen` is `""`, `changes` is `[]`.
- `minimal`: a few words or phrases changed, structure untouched.
- `larger`: sentences changed, but the answer still follows the original.
- `rewrite_needed`: it cannot be repaired within the rules (most claims are invented, the prompt is contradictory, or the word range cannot be met).
  `chosen` is `""`; say why in `changes`. Prefer this over inventing content.

`changes` is required for `minimal` and `larger`: one short Turkish or English note per fix (what was wrong, what you did).

## Second pass (retry rows)

Some rows come back with a `retry` field:
- `check_failed`: your earlier repair is in `previous_chosen` and `failure_reasons` lists what the code check found (unknown or English words, an
  ending that looks cut). Fix those, keep the rest, return the same output format.
- `range_widened`: you earlier answered `rewrite_needed` because the repair could not stay in the old word range (`previous_reason`). The range is now
  wider. Try again. Answer `rewrite_needed` again if the repair still needs invented content or filler.

## Examples

Prompt (shortened): kargo gecikmesi bilgilendirme mesajı, tam olarak 3 madde (bullets_3), resmi ama samimi, en fazla 120 kelime. Veriler: kargo 2 gün
gecikecek; takip numarasını kontrol et; canlı destekten güncel konumu sor; iade hakkını saklı tut.

Answer:
```
- Yoğunluk nedeniyle kargonun gecikmesi 2 gün sürer; takip numarınızı kontrol edin.
- Destek ekibinden güncel konumunu sorgulayın.
- İade hakkınızı saklamadan geri gönderiniz.
```
Repaired (`minimal`, 24 words before and after):
```
- Yoğunluk nedeniyle kargonuz 2 gün gecikecek; takip numaranızı kontrol edin.
- Canlı destek ekibinden kargonuzun güncel konumunu sorgulayın.
- İade hakkınızı saklı tutun.
```
changes: `takip numarınızı -> numaranızı`, `canlı destek eklendi (veride var)`, `iade hakkını saklamadan geri gönderin -> saklı tutun (veriyle ters)`.

Prompt (shortened): sprint retrospektifi notlarını (hızımız arttı, test süreçleri yavaşlatıyor, CI/CD hataları azaldı) 3 madde, en fazla 100 kelime, tekrar yok.

Answer:
```
1. Hız yükselmiş, test süreçleri daha hızlı.
2. CI/CD'te hatalar azalmış.
3. Son adım hız ve kalite arasında dengeyi sağlamış.
```
Repaired (`larger`):
```
- Hızımız arttı; test süreçleri ise bizi yavaşlatıyor.
- CI/CD hataları azaldı.
- Bu noktalar son sprint retrospektifinde ortaya çıktı.
```
changes: `test süreçleri "daha hızlı" -> yavaşlatıyor (veriyle ters)`, `uydurma sonuç cümlesi veriden gelen bir cümleyle değiştirildi`.
