# Translation worksheets (owner)

Fill the `turkish` column of each CSV. Do not edit `id` or `english`; do not add, merge, split or reorder rows.
The files are UTF-8 with a header row (`id,english,turkish`) and open in Google Sheets or Excel (import as UTF-8).

## Order (most important first)

| File | Rows | What it is | Why |
|---|---:|---|---|
| `01-gsm8k-train.csv` | 1,000 | math word problems (training) | the main experiment: Turkish math reading |
| `02-gsm8k-final-test.csv` | 100 | math word problems (final test, never trained on) | the clean test; **please read and check these yourself** |
| `00-wrappers.csv` | 8 | instruction templates around a problem | 8 short lines; keep `{q}`, `{text}`, `{tests}` exactly |
| `03-mbpp-text.csv` | 300 | one-sentence coding tasks | code rows and translation rows |
| `04-tool-user-queries.csv` | 300 | one-sentence user requests for a tool | tool-call rows and translation rows |

Start with 01 and 02: the first experiment can run on them alone.

## Rules

1. **Meaning first, natural Turkish second.** Not word for word. Keep the difficulty: do not simplify, explain or add hints.
2. **Numbers stay the same.** The digits must not change. You may write them the Turkish way (`10.000`, `0,5`), but do not spell
   numbers out as words (write `3`, not `üç`) and do not convert units or currencies. `$`/`%` signs may stay or become words.
3. **Names, code, quoted text:** keep person names; keep code, function names, JSON-like text and anything in quotes exactly.
   In `04-tool-user-queries.csv` also keep place names and other values the tool would need (for example `New York`,
   `United States`) exactly as in English; translate everything around them.
4. **Wrappers (`00-wrappers.csv`):** keep `{q}`, `{text}` and `{tests}` as they are, and keep line breaks. In `math:w3` you may
   translate the marker (`"Answer: <number>"` becomes e.g. `"Cevap: <sayı>"`).
5. One row = one cell; line breaks inside a cell are fine if the English has them.
6. **Tell me which tool translated them** (name, version, date) so it can go on the dataset card, and check that its terms allow
   using the output to train a model. Text produced by an Anthropic model cannot go into this dataset (consumer terms, see
   `bilingual-pilot-v01/TERMS-RESTRICTION.md`). If you proofread them yourself, say so.

Return the filled files in this folder (same names). The validator
(`scripts/datasets/validate_lfm3_sft_core_translations.py`) checks ids, empty cells, digits and placeholders and reports every
problem row; fix those and send again.
