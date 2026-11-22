# SFT core v01 — translation provenance

Translation completion date: **2026-11-22**. This card supplements
[README.md](README.md) and the pinned source information in
[build-manifest.json](build-manifest.json).

## Completed worksheets

| File | Rows | Status and use |
|---|---:|---|
| `worksheets/01-gsm8k-train.csv` | 1,000 | Turkish problem statements completed; training split |
| `worksheets/02-gsm8k-final-test.csv` | 100 | Turkish problem statements completed; final evaluation only, never training |
| `worksheets/00-wrappers.csv` | 8 | Turkish instruction templates completed |
| `worksheets/03-mbpp-text.csv` | 300 | Deferred; Turkish cells remain empty |
| `worksheets/04-tool-user-queries.csv` | 300 | Deferred; Turkish cells remain empty |

IDs, English text, row counts, and row order are preserved. Wrappers preserve
`{q}`, `{text}`, `{tests}`, newline positions, and blank lines. The permitted
`math:w3` answer marker is translated to `Cevap: <sayı>`.

## Translator and review

- **Tool/provider:** OpenAI Codex, in this conversation.
- **Model/version:** GPT-6-based assistant, as identified by the runtime instructions.
  The exact deployed model revision, application build, sampling settings, and seed
  are not exposed; no more specific revision is claimed.
- **Method:** direct English-to-Turkish translation by the Codex assistant, in
  worksheet order, followed by same-assistant review and deterministic checks.
- **Date:** 2026-11-22.
- **Final-test review:** the assistant read all 100 English final-test questions
  individually and authored/reviewed their Turkish translations. This is AI review,
  not owner review or independent native-speaker validation.
- **No solutions:** only problem statements and instruction wrappers were translated;
  no worked solutions, gold answers, or reasoning targets were added.
- **Discarded alternatives:** local OPUS-MT and Qwen translation smoke tests/drafts
  were explored before the owner requested direct translation. None of those draft
  translations remains in the delivered Turkish cells. The preliminary Qwen wrapper
  wording was also replaced with direct Codex translations.
- **Anthropic:** no Anthropic model output was used in these translated cells.

The original problems' relationships, names, units, currencies, and quoted values
were retained. Units such as pound, fit, ons, galon, pint, quart, and cup denote
the original units; they were not converted to metric measurements. Number words
already present in English can remain number words in Turkish. Existing digits
were not replaced with number words. No digits were introduced to explain implicit
conversions or supply solution hints.

For `c-mathtest-0011`, the Turkish explicitly identifies the **English alphabet**
to preserve the original English-language alphabet context rather than silently
substituting the Turkish alphabet. No letter count is supplied.

Some source questions contain awkward, incomplete, or ambiguous assumptions, for
example `c-math-0381` (ages and “current age”), `c-math-0533` (“scores” as colored
objects), and `c-math-0647` (different currencies without an exchange rate).
Translation does not repair their English, alter the gold checker, or insert an
exchange rate. Such source limitations remain distinct from translation quality.

## Provider terms review

Checked 2026-11-22 against the official
[OpenAI Terms of Use](https://openai.com/policies/terms-of-use/)
(effective January 1, 2026) and
[OpenAI Services Agreement](https://openai.com/policies/services-agreement/)
(effective January 1, 2026).

Both assign output ownership to the customer/user, subject to compliance with their
terms. The Terms of Use prohibit using output to develop models that compete with
OpenAI. The Services Agreement has a corresponding competing-model restriction
in section 3.3(e), with specified permitted exceptions. Output ownership alone
does not eliminate those restrictions. The applicable account agreement was not
independently inspected.

The owner explicitly described this work as personal, noncommercial learning and
research: a Turkish fine-tuning experiment on LFM3-1.7B, with no competing product
or service and no earnings, and directed Codex to translate it directly. Work
proceeded on that stated **noncompeting research scope**. This terms assessment is
conditional on that scope; it is not a claim of unrestricted permission to train
competing models, nor written clearance from OpenAI. The owner's intended open
resource should retain this provider provenance rather than claim provider approval
or human authorship.

The GSM8K source license remains **MIT**, as recorded in the build manifest. This
card does not relicense unrelated core categories or override their source licenses.

## Validation and handoff

The existing validator was run on a temporary directory containing only the three
completed priority sheets, so the deferred sheets do not count as incomplete
translations in that report. Command:

```text
python scripts/datasets/validate_lfm3_sft_core_translations.py --worksheets C:/tmp/sft-core-priority-validation --report experiments/turkish-capability/lfm3-1.7b/sft-core-v01/worksheets/translation-validation.json
```

See [translation-validation.json](worksheets/translation-validation.json) for the
unaltered validator output, [translation-integrity.json](worksheets/translation-integrity.json)
for row counts, hashes and immutable-source checks, and
[translation-review.json](worksheets/translation-review.json) for warning disposition.
Passing structural checks does not prove every translation is semantically perfect.
The owner will perform the downstream validation, rendering, and base-model sampling.
