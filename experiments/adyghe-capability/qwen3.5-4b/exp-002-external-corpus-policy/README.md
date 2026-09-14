# exp-002-external-corpus-policy

## Decision

The `ady-ru` split of `adiga-ai/circassian-russian_texts_synthetic` is **not**
primary SFT translation supervision until its provenance is established.

The detailed card description currently available in our notes describes the
different repository `anzorq/circassian-russian_paragraphs_synthetic`: a
monolingual Circassian source corpus, dialect separation with fastText, and
model-generated Russian translations with only minimal manual corrections. The
two repositories have different row counts, so this lineage cannot be assigned
to `adiga-ai` without verification. If they share that construction, translating
Russian to English compounds the noisy label path:

```text
Adyghe source → synthetic Russian → synthetic English
```

## Allowed use

- Candidate Adyghe-only data for continued pretraining after filtering,
  deduplication, and language/noise inspection.
- Low-weight synthetic auxiliary pairs only after manual spot checks and
  quality filters.

## Disallowed claim

Do not call English→Adyghe pairs derived from this corpus human-quality
translation data. Do not use them as benchmark references.

## Primary path

Use the user-authored, native-reviewed examples as the initial SFT seed. Grow
that seed with human-verified pairs; then use external synthetic material only
when it demonstrably improves a held-out, human-authored evaluation set.
