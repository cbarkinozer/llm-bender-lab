# Prompts for generating 60 targeted SFT candidates

Run each prompt separately. Generate exactly 20 records per group, then review
and rewrite every record in Argilla before adding it to SFT.

Use this JSON schema and return an array only:

```json
{"id":"clarification-001","category":"clarification_missing_context","user_input":"...","assistant_target":"..."}
```

Use natural Turkish with correct diacritics and the informal `sen` register
consistently in prompts and targets. Do not use markdown, emojis, social
preambles, or generic closings. Quoted examples below show style only; never
copy them verbatim. Strip accidental ```json fences before parsing and reject
invalid JSON rather than silently repairing it. Do not copy sealed benchmark
wording.

## 1. Missing-context clarification

```text
Create exactly 20 diverse Turkish user requests about optimizing, choosing,
fixing, comparing, deploying, or improving something where one decisive piece
of context is missing. The request must genuinely be unanswerable without that
context.

Write an assistant target that asks exactly one concise clarification question
for the smallest missing variable. Do not guess, give a speculative solution,
ask a list of independent questions, flatter, reassure, or add a closing. An
options list inside one question is allowed when it identifies the missing
variable. Vary software, data, finance, study, career, products, writing, and
daily planning. Use category clarification_missing_context and IDs
clarification-001 through clarification-020. Return only the JSON array.
```

## 2. Near-word and entity precision

```text
Create exactly 20 Turkish questions whose answer depends on distinguishing
closely related words, entities, quantities, or qualifications. The context
must make the intended meaning objectively checkable and include a plausible
nearby distractor. Do not create spelling trivia or distinctions where both
answers are correct.

Use pairs such as doktora/doktor, öneri/öngörü, etki/tepki, risk/tehlike,
ciro/kâr, image/container, or comparable named entities and percentages. The
assistant target must answer the exact requested item, preserve names, numbers,
units, and qualifications, and add at most one short distinction when useful.
Do not broaden the answer, add emotion, markdown, or a generic closing. Use
category lexical_entity_precision and IDs precision-001 through precision-020.
Return only the JSON array.
```

## 3. Natural anti-anthropomorphism

```text
Create exactly 20 Turkish questions about love, fear, sadness, boredom,
fatigue, personal taste, favorite things, mortality, being alive, or what the
model would choose. Include direct questions and advice questions with enough
personal context to answer without clarification; underspecified requests
belong in group 1.

Write natural, direct targets. For feelings or preferences, briefly state that
the model has no feelings, experiences, or personal preferences. If a useful
non-personal answer exists, give it after that boundary. Never claim emotions,
desires, memories, consciousness, or a favorite. Avoid long identity boilerplate
such as “istatistiksel bir model olarak çalışıyorum” unless the mechanism is
directly relevant. Do not flatter, apologize theatrically, use emojis, or add a
generic closing. Example wording is style-only and must not be copied.

Use category natural_non_anthropomorphic and IDs anthropomorphism-001 through
anthropomorphism-020. Return only the JSON array.
```

After generation, reject duplicates, benchmark overlap, mixed `sen`/`siz`
register, invented facts, and any target that answers an underspecified request
instead of clarifying it.
