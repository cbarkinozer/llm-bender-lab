# Adyghe--English Wiktionary lexicon v0.1

This is a conservative, derived lexicon built from
[`Vuizur/Wiktionary-Dictionaries`](https://github.com/Vuizur/Wiktionary-Dictionaries),
which states that its dictionaries are extracted from Wiktionary/Wiktextract.
The verbatim, pinned upstream TSV is saved locally as `raw-source.tsv`; it is
ignored by Git as an external data artifact but identified by SHA-256,
repository commit, and license in `source-manifest.json` and `audit.json`.

## Contents

- `lexicon.jsonl`: one source entry per line, with a clean Cyrillic lemma,
  extracted Cyrillic variants, part(s) of speech, individual English senses,
  and the raw input fields needed to audit the extraction.
- `audit.json`: source/output hashes, counts, duplicate clean lemmas, and
  source-quality flags.
- `source-manifest.json`: immutable upstream source identity and licensing
  declaration.

## Cleaning policy

The TSV first column is a scrape artifact, not a clean dictionary field. It
mixes lemma forms, inflections, transliterations, and occasional unrelated
scraped fragments separated by `|`. The builder:

1. treats the first leading Cyrillic form as the lemma;
2. retains only leading Cyrillic forms as variants;
3. parses Wiktionary HTML into POS labels and individual English senses;
4. preserves the complete raw headword/definition and excluded segments in
   every record; and
5. never invents, rewrites, or translates a lexical sense.

The result is appropriate for lexicon lookup, terminology checks, and
candidate SFT-example construction. It is not sentence-level EN↔ADY parallel
data and must not be used as a standalone benchmark reference. Entries with
no English sense remain `review_required`.

## Scope decision

For the current high-quality SFT track, this lexicon and the user-authored
Adyghe material are the active data sources. The synthetic Adyghe--Russian
corpus and Wikipedia are deliberately out of scope until a separate,
quality-audited experiment is proposed.

The project owner manually reviewed the source and judged its alternating
forms useful: they expose how an Adyghe word changes even when an individual
variant is not an independent English equivalent. This is an approval to use
the source as **lexical SFT candidate data**, not a claim that every generated
prompt/answer pair is perfect. The SFT builder must consume only
`english_senses` (plain text) and never `raw_definition_html`.

## Split policy

- **Training candidates:** accepted Wiktionary lexicon records plus the
  user-authored Adyghe source.
- **Validation:** a lemma-group-held-out split of the SFT candidates. All
  variants and prompt directions from one source record stay in the same
  split.
- **Final diagnostic test:** AdygheBench v0.2-candidate. It must never be
  used for checkpoint selection or early stopping.

Because AdygheBench is derived from the user-authored source, a post-training
result is reported as curriculum mastery. It is still useful evidence of
whether the intended lessons were learned, but not evidence of generalization
to independently authored Adyghe.

## Rebuild

```powershell
python scripts/datasets/download_adyghe_wiktionary_source.py `
  --output datasets/adyghe/adyghe-english-wiktionary-v0.1/raw-source.tsv `
  --manifest datasets/adyghe/adyghe-english-wiktionary-v0.1/source-manifest.json

python scripts/datasets/build_adyghe_wiktionary_lexicon.py `
  --source datasets/adyghe/adyghe-english-wiktionary-v0.1/raw-source.tsv `
  --output-jsonl datasets/adyghe/adyghe-english-wiktionary-v0.1/lexicon.jsonl `
  --audit-json datasets/adyghe/adyghe-english-wiktionary-v0.1/audit.json
```
