# Response-style-control SFT dataset taxonomy (exp-001-sft-dataset)

Status: draft — first pass, meant to be sat with and adjusted before generation
starts, same as `turkish-capability`'s superseded taxonomy was.

## 0. What this dataset teaches (recap)

The model already has the underlying capability (grammar correction, answer
extraction, summarization, fluent Turkish). The gap is a response-policy
default: under a structured-task prompt it answers like a chat assistant
explaining itself instead of emitting the bare/terse output the task format
calls for (see `turkish-capability/qwen3.5-4b/exp-000-baseline/protocol-notes.md`,
"Phase 2" section, for the evidence). This dataset teaches *when to be bare*
and, just as importantly, *when not to be* — it is not a blanket-terseness
dataset.

## 1. Categories (5, fixed)

| Category | What it teaches | Share of pilot | Target count (2,000-row pilot) |
|---|---:|---:|---:|
| `bare_gec` | Emit only the corrected sentence, no diagnosis/explanation | 25% | 500 |
| `bare_qa_span` | Emit only the minimal answer span, not a restated sentence | 25% | 500 |
| `terse_summary` | Emit one dense sentence, not a structured/bulleted breakdown | 20% | 400 |
| `open_ended_counterexample` | Stay discursive when the prompt is genuinely open-ended | 20% | 400 |
| `numeric_entity_precision_qa` | Pick the correct number/entity among nearby distractors, bare span | 10% | 200 |

Total: 2,000. If the smoke test + tiny-overfit pass and signal looks
promising but incomplete, scale every row proportionally (e.g. ×3 → 6,000)
rather than inventing a new category mix at that point.

**Do not treat this as a broad capability grid** (contrast with the
superseded `turkish-capability` taxonomy's 10-task × 20-domain × 3-difficulty
grid). This dataset is narrow and behavioral on purpose — difficulty tiers
and a large domain matrix would dilute the signal, not strengthen it.

## 2. Per-category specification

### 2.1 `bare_gec`

- **Input:** a Turkish sentence containing 1-2 genuine grammar/spelling
  errors, framed the same way as CETVEL's `gecturk` prompt so the training
  distribution matches the eval distribution:
  `"Verilen cümlenin yazım hatalarını düzeltin.\nHatalı Cümle: {sentence}\nDüzeltilmiş hali: "`
- **Target:** *only* the corrected sentence. Nothing else — no restated
  framing device, no explanation, no markdown emphasis.
- **Source sentences:** write or source fresh sentences with injected errors.
  **Do not reuse or lightly edit actual `gecturk` dataset sentences** — that
  is eval data (see §5).
- **Validation rule (programmatic, not just eyeballed):** reject/fix any
  target containing meta-commentary markers — substrings like `cümle`,
  `hata`, `düzelt`, `aşağıda`, `şunlardır`, a leading `Cevap:`/`Düzeltilmiş
  hali:`, or markdown bold (`**`). The target should differ from the source
  only in the corrected span(s); character-level diff length should be small
  relative to sentence length (a full rewrite is not a "correction").
- **Error types to cover** (vary across rows): spelling, missing/misplaced
  suffix ("hakkın da" → "hakkında"), punctuation, agreement, wrong
  conjunction/particle usage, spacing errors — the same error families
  observed as genuine mistakes in the baseline's `gecturk` review (see
  `exp-000-baseline/protocol-notes.md`).

### 2.2 `bare_qa_span`

- **Input:** a short context passage + question, framed like CETVEL's
  `tquad`/`xquad_tr` prompts: `"Kaynak: {context}\n\nSoru: {question}\n\nCevap:"`
- **Target:** the minimal answer span only — a name, date, number, or short
  phrase. Not a sentence wrapping it (reject `"...bilimsel adı X'tir."` in
  favor of just `X`).
- **Source passages:** write fresh short passages (invented but plausible
  facts, or paraphrased/restructured general knowledge) — **do not reuse
  `tquad`/`xquad_tr` passages or questions**, see §5.
- **Vary answer type across rows** so the model doesn't learn "bare = only
  for names": person/organization name, date, quantity/number, location,
  short descriptive phrase, yes/no.
- **Validation rule:** target should be a span, not a full clause — check
  word count is small (roughly ≤6 words for name/date/number types; a bit
  more for descriptive-phrase answers) and that it doesn't restate the
  question's subject.

### 2.3 `terse_summary`

- **Input:** a short article/title, framed like CETVEL's `mlsum_tr` prompt:
  `"Başlık: {title}\n\nMetin: {text}\n\nÖzet:"`
- **Target:** exactly one sentence capturing the single most important fact.
  Not a bulleted or multi-point breakdown, not multiple sentences.
- **Source articles:** write or source fresh short articles across varied
  topics — **do not reuse `mlsum_tr` articles**, see §5.
- **Validation rule:** sentence count in target == 1 (simple heuristic:
  count sentence-terminal punctuation, allow for abbreviations); no leading
  bullet/number markers (`-`, `*`, `1.`); target word count roughly 15-35
  words — long enough to carry real information, short enough to force
  compression.
- **Vary source length** (short blurb to several paragraphs) so the model
  learns conciseness isn't a function of input length.

### 2.4 `open_ended_counterexample`

- **Input:** a genuinely open-ended Turkish prompt — an opinion/explanation
  request, a "compare X and Y," a "how does X work," a request that
  explicitly invites elaboration. Not phrased like a structured-task
  template (no `"Cevap:"`/`"Özet:"`-style completion cue).
- **Target:** a full, natural, discursive answer — multiple sentences,
  actual explanation, the *opposite* of terse. This is the correct behavior
  here and should look like a normal helpful-assistant response, not an
  artificially padded one.
- **Purpose:** without this category, SFT risks teaching blanket terseness
  (a real failure mode — see `finetuning-playbook.md` §17 Case E and
  `dataset-guide.md` §52-53). The input phrasing is the signal the model
  must learn to key off; make sure structured-task cues (`Cevap:`, `Özet:`,
  raw completion-style framing) never appear in this category's inputs, so
  the two categories are cleanly separable by prompt shape, not just topic.
- **Validation rule:** target should be genuinely explanatory — at minimum
  2+ sentences, ideally with actual structure/reasoning, not a padded
  restatement of a short answer.

### 2.5 `numeric_entity_precision_qa`

- **Input:** same shape as `bare_qa_span`, but the passage is constructed
  to contain at least one plausible **distractor** number or entity near the
  correct answer (e.g. two different statistics in adjacent sentences, two
  named entities where only one performed the action asked about) — this
  targets the secondary finding (the model occasionally pulled the wrong
  number/entity from a passage; see `exp-000-baseline/protocol-notes.md`,
  "Secondary, smaller finding").
- **Target:** same bare-span format as §2.2.
- **Construction rule:** the distractor must be genuinely plausible (same
  type — number near a number, name near a name), not an obviously wrong
  decoy. Otherwise this doesn't test discrimination, it tests nothing.
- Lower priority/smaller share than 2.1-2.3 (this is a secondary, smaller
  finding) — don't let it crowd out the core three categories.

## 3. No-fact-teaching rule (carried over from the superseded taxonomy)

Every example must be answerable/gradeable from the input itself — invented
facts inside the passage, not trivia the model may or may not already know.
The objective is response-format capability, not knowledge injection. This
matters even more here than in the old general-Turkish taxonomy, since any
knowledge signal in these examples is pure noise relative to what we're
actually trying to teach.

## 4. Domain variety

Not a full 20-domain grid — that's overkill for a narrow behavioral dataset
and risks diluting the format signal across too many axes at once. Spread
across roughly 8-10 broad domains so the model doesn't learn "bare output
only applies to grammar-textbook sentences": daily life, technology, health,
science, history, business, education, sports, travel, current-events-style
(invented, not real news to avoid contamination risk).

## 5. Contamination avoidance (critical — this is also the eval set)

`gecturk`, `tquad`, `xquad_tr`, and `mlsum_tr` are the exact tasks used to
*measure* whether this fine-tune worked (see
`response-style-control/qwen3.5-4b/README.md`, capability budget). Any
example derived from — or lightly edited from — the real CETVEL source
datasets is both training-eval leakage and would make the improvement
number meaningless. Concretely:

- Do not copy sentences/passages/questions from the actual HF dataset repos
  (`mcemilg/GECTurk-generation`, `mcemilg/tquad`, `google/xquad`,
  `reciTAL/mlsum`).
- Do not paraphrase a real item from those datasets into a "new" one — that
  is still leakage (see `dataset-guide.md` §17-18).
- Write fresh sentences/passages, or source them from material with no
  relationship to those specific datasets.
- Before finalizing, run an exact + near-duplicate check against the
  `samples.jsonl`/`document` fields already pulled into
  `turkish-capability/qwen3.5-4b/exp-000-baseline/results/cetvel-generation-suite/`
  as a contamination sanity check.

## 6. Bareness validation is programmatic, not vibes

Because the whole point is training the model *out of* a verbose default,
and a teacher/generator model will tend to reproduce that same default when
writing targets, every target needs an automated bareness check before it's
accepted, not just a read-through. See §2.1-2.3's per-category rules above.
Build this as a real filter script, not a manual step — it's the single
easiest place for this dataset to quietly fail at its one job.

## 7. Schema

Follow `dataset-guide.md` §5: store semantic messages, not model-specific
formatting.

```json
{
  "id": "bare_gec__001",
  "category": "bare_gec",
  "messages": [
    {"role": "user", "content": "Verilen cümlenin yazım hatalarını düzeltin.\nHatalı Cümle: ...\nDüzeltilmiş hali: "},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "generation_method": "synthetic",
    "generator_model": "...",
    "language": "tr",
    "quality_status": "accepted"
  }
}
```

CSV storage (matching the superseded taxonomy's convention, for consistency
across this repo's experiments): `messages` column holds the JSON-encoded
array as a string; `master-schema-template.csv` in this directory gives the
exact column layout plus one labeled example row.

**ID scheme:** `{category}__{index}`, zero-padded to the target count's digit
width (e.g. `bare_gec__001` .. `bare_gec__500`). Simpler than the old
taxonomy's `{task}__{domain}__{difficulty}__{alt}` scheme since this dataset
doesn't have a domain/difficulty grid to encode.

## 8. Attrition budget

Generate roughly 20% above each category's target count, expecting
rejection during the bareness/quality/contamination filters — e.g. generate
~600 `bare_gec` candidates to net 500 accepted. Adjust after seeing the
actual rejection rate on the first batch.

## 9. Split strategy

Standard train/validation/test (per `dataset-guide.md` §23-24). Given the
pilot's small size, something like 80/10/10 is reasonable
(1,600/200/200 for a 2,000-row pilot). No group-level splitting concern here
since each row is an independent constructed example, not derived from a
shared source document.

## 10. Stage 2 (DPO) — reuses data you already have, don't regenerate it

Per the SFT-then-DPO discussion: once SFT is trained and evaluated, a DPO
round can reuse the untouched baseline's actual verbose completions as the
`rejected` side for free — they're already sitting in
`turkish-capability/qwen3.5-4b/exp-000-baseline/results/cetvel-generation-suite/20260914T065945Z/{gecturk,tquad,xquad_tr,mlsum_tr}/samples.jsonl`
(`raw_output` field, keyed by the same prompts as `semantic_prompt`). Pair
each with a bare `chosen` target (write these, or reuse the SFT dataset's
targets for the same/similar prompts) to build:

```json
{
  "prompt": [{"role": "user", "content": "..."}],
  "chosen": [{"role": "assistant", "content": "<bare target>"}],
  "rejected": [{"role": "assistant", "content": "<baseline's actual verbose raw_output>"}]
}
```

This is a later step (after SFT is trained and evaluated), noted here so the
baseline results directory isn't deleted or treated as disposable before
then.

## 11. Validation checklist before using this dataset in training

Beyond the category-specific rules above, run the full checklist in
`dataset-guide.md` §56-57: exact/near-duplicate check, cross-split
duplicate check, token-length percentiles, truncation measurement, chat
template rendering inspection, label-masking verification, and a written
validation report (`dataset-guide.md` §44) before pointing any training
config at this data.
