# Editing guide: repair a Turkish model answer with as little change as possible

You get `edit-worksheet.jsonl`, one JSON object per line. Each row has a prompt and an answer written by a small Turkish model, and
notes from automatic detectors. Your job is to write the same answer again, correct. The original answer becomes the "rejected" side
of a preference pair and your version the "chosen" side, so **the only differences between the two should be the mistakes.**

## Fill in these fields (leave the others unchanged)

| Field | What to write |
|---|---|
| `edited_answer` | The repaired answer, as plain text exactly as it should be shown to a user. No commentary, no notes, no quotes around it. |
| `edit_kind` | `minimal`, `larger` or `drop` (see below). |
| `accept_words` | Words the detector flagged that are real Turkish words or names (the detector misses some). Lowercase list. |
| `editor_notes` | One short line: what you fixed. |

## What to fix

- Invented or wrongly suffixed words ("kutuplağa", "yaşılan", "erterleyebilir"): replace with the correct word of the same meaning.
- Wrong terms or facts: correct them. If you are not sure about a fact, use `drop`; never invent one.
- English words inside a Turkish answer (not in a translation's quoted source): replace with Turkish.
- Awkward word-for-word phrasing: only when it is clearly unnatural; use the plain, ordinary Turkish word order.
- Agreement and case errors, wrong possessive or verb suffixes.
- Broken countable constraints (the notes say which: words, sentences, bullets, required word).
- An answer cut off at the token cap: end it with the shortest natural ending (one or two sentences). Do not extend it further.
- A translation: the Turkish must say what the English says, with natural Turkish word order.

## What not to change

- Keep structure, order, tone, formatting (bullets, bold, numbering), and every sentence that is already fine, word for word.
- Keep the length. Do not add content, examples, greetings or disclaimers that were not there. Do not shorten parts that are fine.
- Keep numbers, names and dates exactly.
- Do not "improve" style or make it more eloquent. A repaired answer should still sound like the same small model, minus its mistakes.

## `edit_kind`

- `minimal`: you changed at most about a quarter of the words and kept the length (within 15%). This is the default, and the only
  kind used for the first training run.
- `larger`: the fix cannot be small. Typical cases: the answer does the wrong task (it gives advice about writing an e-mail instead of
  the e-mail), or a countable constraint needs a different length ("exactly 2 sentences" and the answer has 16). Reuse the model's own
  wording and ideas where you can. These rows are stored separately and are not used unless the owner decides so.
- `drop`: not repairable without inventing content, or you are unsure it is correct. Leave `edited_answer` empty.

## Check your work

Run the validator after editing; it prints, per row, why an edit is not usable (too many words changed, length band, constraint still
broken, flagged words left, no proper ending):

    python scripts/datasets/tr_dpo_flags.py validate --worksheet edit-worksheet.jsonl --out DIR

Fix the rows it rejects and run it again. The validator only counts; it cannot tell whether your Turkish is right. When in doubt about a
word, prefer the more common one.

## Provenance

The finished rows are synthetic (written by an AI assistant). Do not mark them as reviewed by a person unless the owner has reviewed
them row by row. Record which assistant and settings did the editing in the private provenance notes (`samples-local/PROVENANCE-NOTES-PRIVATE.md`),
not in files that go into Git or to Hugging Face.
