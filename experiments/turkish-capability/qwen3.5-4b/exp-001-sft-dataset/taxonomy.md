# Turkish SFT dataset taxonomy (exp-001-sft-dataset)

**Status: superseded.** Written before `exp-000-baseline`'s Phase 2
diagnostic, which found no evidence of a general Turkish-fluency gap —
the model's raw Turkish is already fluent and grammatically correct. The
actual weakness is instruction-following/output-format discipline under
structured-task prompts, which this 10-task/20-domain general-capability
taxonomy does not target. Superseded by the narrower taxonomy in
`experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/`. Kept
here for reference only — several of its mechanics (no-fact-teaching rule,
ID scheme, CSV schema, attrition budgeting) carried over into the new
taxonomy where still applicable.

## Arithmetic check

10 tasks × 20 domains × 3 difficulty levels = **600 cells**. With 20 domains
and 10 alternatives per cell, that's 600 × 10 = **6,000**, which lines up
exactly with my 5,000 train / 500 val / 500 test target. If I want 6,000 to be
the number that *survives* review + dedup + contamination filtering, rather
than the raw generation count, I need to generate past 600×10 — see the
attrition budget below.

## 1. Tasks (10, fixed)

| Task | What it exercises |
|---|---|
| `instruction_following` | Following an explicit, possibly multi-constraint instruction (format, length, tone) |
| `qa` | Self-contained questions answerable from the question itself (comprehension, arithmetic, everyday reasoning) — not trivia recall |
| `reading_comprehension` | Answering questions that require a supplied passage |
| `reasoning` | Multi-step inference, causal/logical reasoning, puzzle-style problems |
| `summarization` | Condensing a longer passage into a shorter one |
| `rewriting_grammar` | Grammar correction, style rewriting, register conversion |
| `classification_nli` | Labeling text (sentiment, topic, entailment/contradiction/neutral) |
| `dialogue` | Multi-turn conversational exchanges |
| `translation` | Turkish↔English (or Turkish↔other) translation |
| `structured_extraction` | Pulling structured fields (JSON, tables, key-value) out of free text |

**No fact-teaching.** My goal is capability (understanding instructions,
reasoning, producing fluent correct Turkish), not injecting arbitrary
knowledge the model may or may not already have. This mostly bites on `qa`:
"which card is used for public transit in Ankara" tests whether the model
happens to know a local fact, not whether it can comprehend or reason. Every
`qa` item needs to be answerable from the question itself (self-contained
comprehension/arithmetic/everyday-reasoning), not a trivia lookup.

## 2. Domains (20)

I picked these to spread broadly and keep any one topic from dominating. I'm
deliberately leaving out politics and religion — not because they're
off-limits in principle, but because I don't think they add real capability
value here relative to the editorial risk of keeping them neutral at
synthetic-generation scale. I'll swap any of these out if a gap becomes
obvious once I start generating.

1. Daily life & routines
2. Technology & software
3. Sports & fitness
4. Health & medicine
5. Science & nature
6. History
7. Business & finance
8. Law & civic administration
9. Education & learning
10. Environment & climate
11. Travel & tourism
12. Food & cuisine
13. Arts & literature
14. Music & entertainment
15. Family & relationships
16. Workplace & career
17. Transportation
18. Shopping & consumer life
19. Hobbies & crafts
20. Social media & internet culture

## 3. Difficulty (3, operational definitions)

| Level | Definition |
|---|---|
| Easy | Single-step factual recall or mechanical transformation. No inference required. |
| Medium | Requires connecting 2-3 pieces of information, or one light inferential step. |
| Hard | Multi-step reasoning, ambiguity resolution, or synthesis across a longer/more complex input. |

Worked calibration examples for `qa`, since it's easy to mislabel a "medium"
example as "easy" just because it's short (I did this myself on the first
draft):

- **Easy** — one operation, both givens stated directly, nothing to chain:
  *"Ali'nin 3, Ayşe'nin 2 elması var. İkisinin toplam kaç elması var?"* → 5.
- **Medium** — 2-3 given values combined in sequence, still mechanical but
  requires holding multiple values at once:
  *"Sabah 8'de kalkıyorum. Duş, kahvaltı, giyinmek 40 dakika. İşe gitmek 15
  dakika. Saat 9'da işte olmak için en geç ne zaman çıkmalıyım?"* →
  08:00 + 40dk + 15dk → en geç 08:45.
- **Hard** — chained arithmetic *plus* a genuine conditional/judgment, not
  just more numbers: *"Toplantım 14:00'te başlıyor, 90 dakika sürüyor, arada
  15 dakikalık mola var. Toplantıdan sonra 20 dakika yürüyüş mesafesindeki
  bir yere 16:00'da varmak istiyorum, yürüyüşe çıkmadan önce 10 dakika payım
  olsun. En geç ne zaman yürüyüşe çıkmalıyım, ve toplantı buna yetişiyor
  mu?"* — this needs the arithmetic *and* a check of whether the constraint
  is even satisfiable, which is what actually distinguishes hard from "medium
  with bigger numbers."

The test I'll apply to every cell going forward: if a "harder" version of an
example is just the same single composition step repeated with more numbers,
it's not actually harder — hard needs a genuinely different operation
(a conditional, an ambiguity to resolve, a synthesis across more moving
parts), not more of the same step.

**Reasoning-trace rule:** I'm only putting reasoning traces on hard-difficulty
examples, and only where reasoning is genuinely how a competent Turkish
speaker would arrive at the answer — not manufactured verbosity to make an
example look harder than it is.

One exception I want to carve out up front: a few tasks have a "hard" tier
that means *more nuanced/idiomatic*, not *more logically complex* — hard
`translation`, `rewriting_grammar`, and `dialogue` items are usually about
register/idiom mastery, not multi-step inference. A reasoning trace there
would be artificial, so I'm not adding one. My working rule:

```
reasoning_trace = (difficulty == hard) AND
                  (task in {reasoning, qa, reading_comprehension,
                            classification_nli, structured_extraction})
```

## 4. No real-source grounding — trade-off and mitigation

I originally wanted to ground reading-comprehension/summarization/etc. in
real Turkish source documents for authenticity. I'm ruling that out: a real
document (news, Wikipedia, forum text) could itself overlap with a CETVEL
source dataset, and that's a contamination risk independent of anything the
generator model writes. Going fully synthetic removes that risk entirely, but
it brings back the "translationese"/generic-AI-Turkish risk the source
grounding was supposed to solve.

My mitigation is that I'm reading and fixing every single example myself, so
this is a coherent trade rather than a gap I'm ignoring — I just can't skip
that review step to save time, since it's now the *only* defense against
unnatural Turkish, not a backstop on top of source grounding.

One thing I'll lean on to help the generator model even without a real
source: concrete, specific, invented constraints per item — a named
(fictional) company, a specific plausible number or date, a concrete scenario
detail — instead of a vague topic prompt. "Write about technology" invites
generic AI-Turkish; a specific invented scenario doesn't.

## 5. What "10 alternatives" actually means — no paraphrasing

I'm not generating one example per cell and paraphrasing it nine times.
Paraphrases share the same entities, the same structure, the same underlying
content with synonyms swapped — and my own near-duplicate dedup pass
(MinHash/n-gram over the corpus) will catch most of that and throw it out,
quietly shrinking me back down from 6,000 before contamination checking even
starts. That defeats the entire point of generating 10 per cell.

A real alternative is a different concrete instance that happens to land in
the same (task, domain, difficulty) cell. Between the 10, I want at least
several of these to vary, not just one:

- **Different scenario/situation** — not the same event retold, a genuinely
  different one (a different sport, a different city, a different product).
- **Different entities and numbers** — different invented names, dates,
  quantities, not the same ones with the topic swapped.
- **Different angle on the instruction** — for the same task+domain+difficulty,
  the actual instruction shape can differ (a QA pair vs. a "compare X and Y"
  vs. a "what would happen if" framing, all still `qa`/`easy` for example).
- **Different register/formality** — one alternative formal, another
  colloquial, where the task allows it.
- **Different length within the band** — see length guidance below; not
  every "easy" example needs to be exactly the same length.

If I generate an alternative and realize it's structurally the same example
as one I already have, it's not alternative #6 — it's a duplicate, and I
should throw it out and write a genuinely different one instead of just
counting it toward my target.

## 6. Length guidance by difficulty

These are word-count bands for the *response*, for tasks where I actually
control the output length freely (`instruction_following`, `qa`,
`reading_comprehension`, `reasoning`, `dialogue`, and the prose side of
`rewriting_grammar`). I'm not forcing every example to hit these numbers
exactly — they're a band to keep me from writing an "easy" example that
rambles for a paragraph, or a "hard" example that's answered in five words.

| Difficulty | Response length | Reasoning trace |
|---|---|---|
| Easy | ~15-35 words, direct | none |
| Medium | ~35-70 words, may briefly justify itself in one clause | none |
| Hard | ~20-60 word answer + ~30-90 word reasoning trace where the rule in §3 applies | yes, where applicable |

For tasks whose output length is dictated by the task itself rather than by
difficulty, I'm not applying this band — instead:

- `translation`: response length tracks source length (it's a translation,
  not a free composition).
- `summarization`: response is a fixed compression of the source (roughly
  20-30% of source length), regardless of difficulty tier.
- `structured_extraction`: response is whatever the extracted fields require
  — often shorter than the "easy" band, and that's fine.
- `classification_nli`: response is a label, optionally with a one-clause
  justification on medium/hard — never a paragraph.

Input side (passage length, where a task needs one): roughly 50-100 words for
easy, 100-200 for medium, 200-350 for hard — again a band, not a hard rule.

## 7. Attrition budget

I'm planning generation/review toward more than the bare 6,000 if I want
6,000 net survivors after: my own rejection, internal near-duplicate removal,
and CETVEL contamination removal. Starting assumption is a 20-30% cushion
(~7,200-7,800 raw candidates), and I'll adjust once I see my actual rejection
rate on the first few hundred.

## 8. ID scheme

I'm not using an arbitrary global counter for `id`. Each row's id is
`{task}__{domain}__{difficulty}__{alt_index}`, where `alt_index` is
zero-padded 01-10 — the position of that row among its cell's 10
alternatives. So `qa__technology__easy__01` through `..__10` are the 10
alternatives for that one cell. This makes every id self-describing: I can
tell which cell and which alternative number a row is just by reading the id,
without a lookup, and it makes it trivial to spot a cell that's short of 10
or has a gap.

## 9. Tracking and storage

`quota-matrix.csv` in this directory: one row per (task, domain, difficulty)
cell with `target_count` (10) and empty `generated_count` / `accepted_count`
columns for me to fill in as I go. Sum of `target_count` = 6,000, matching
this taxonomy.

The dataset itself is a CSV, not JSONL — `master-schema-template.csv` in this
directory is the column template plus one labeled example row (delete that
row before adding real data). CSV over JSONL because I want this reusable for
other models/tools later, not locked to one training pipeline's expected
shape. The `messages` column holds a JSON-encoded array of `{"role":
"...", "content": "..."}` objects as a string — standard CSV quoting
(doubled `"` inside a quoted field) makes that safe to store and round-trip.
At training time, whichever model I'm targeting parses that JSON back out and
applies its own chat template — the stored format doesn't assume Qwen's
template or anyone else's.
