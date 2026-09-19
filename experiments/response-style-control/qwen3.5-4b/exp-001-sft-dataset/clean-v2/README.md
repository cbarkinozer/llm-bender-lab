# Clean SFT v2

This is a reviewable 1,000-row candidate SFT set: 200 rows from each source
category. The original source CSVs and `reviewed-v3` data are unchanged.

The deterministic builder (`scripts/evaluation/build_clean_sft_v2.py`, seed
`3407`) removes exact prompt/target duplicates, caps repeated exact answers and
repeated prompt-content fingerprints, and prefers multi-word targets. Single-
word targets are therefore reduced rather than used as the dominant training
pattern. The fixed task wrappers (for example `Kaynak` / `Soru`) remain visible
so they can be reviewed; they are not treated as evidence that the underlying
Turkish content is good.

Each category also has a separate Argilla review dataset. Review `keep`, `edit`,
or `remove`; put a corrected target or a concrete quality note in the notes
field. The benchmark prompts are not copied into this SFT set.

| Category | Rows | Argilla dataset |
|---|---:|---|
| `bare_gec` | 200 | `exp-004-sft-clean-v2-bare_gec` |
| `bare_qa_span` | 200 | `exp-004-sft-clean-v2-bare_qa_span` |
| `terse_summary` | 200 | `exp-004-sft-clean-v2-terse_summary` |
| `numeric_entity_precision_qa` | 200 | `exp-004-sft-clean-v2-numeric_entity_precision_qa` |
| `open_ended_counterexample` | 200 | `exp-004-sft-clean-v2-open_ended_counterexample` |

`manifest.json` records the source counts, filtering statistics, and SHA-256
hashes. This is a candidate for review, not yet the final training set.
