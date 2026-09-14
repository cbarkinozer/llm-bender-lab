# exp-003-initial-sft-data

## Status

`ready` for dataset review. No training run has started.

## Goal

Create the first clean, model-neutral Adyghe fine-tuning candidate CSV and a
separate runnable CSV representation of the sole initial benchmark.

## Parent

`exp-001-benchmark-curation`

## What changed

Created two generated CSV artifacts:

- `datasets/adyghe/initial-sft-v0.1/initial-training-data.csv`
- `benchmarks/adigebench/v0.2-candidate/adigebench-v0.2-candidate.csv`

The training-candidate CSV combines the Wiktionary data and the supplied
`adige data.txt` material. Its usable fields are:

| Field | Meaning |
| --- | --- |
| `input_text` | Adyghe lemma or authored Adyghe source text |
| `target_text` | Plain-text English definition, gloss, or romanization; no HTML |
| `part_of_speech` | Wiktionary POS, separate from the target |
| `variants` | Adyghe forms, separate from the target |
| `split` | Deterministic train / validation / development-test assignment |

## Split and leakage policy

Eligible Wiktionary rows are deterministically stratified by source, category,
and POS into **80% train / 10% validation / 10% development test**, using seed
3407. Variants belonging to a source entry never cross splits.

`adige-bench.txt` is derived from `adige data.txt`. Therefore the 192 authored
source rows remain in the combined CSV for inspection but are marked
`excluded_benchmark_parent`; they are not used in this no-leak initial run.
264 direct Wiktionary benchmark overlaps and 9 missing-definition records are
also excluded.

The resulting eligible split is:

| Split | Rows |
| --- | ---: |
| Train | 3,451 |
| Validation | 426 |
| Development test | 426 |

The separate AdygheBench CSV has **188** curated rows. It is the only initial
benchmark and is never used for optimization, early stopping, or checkpoint
selection. It retains a `context` field for all reading tasks. Its 54
`native_review_required` items must be treated as provisional.

## Evaluation interpretation

This first protocol is designed to prevent direct training/benchmark overlap.
It is still a small, initial diagnostic, not a final generalization benchmark.
If the authored source is added to gradient updates in a later experiment,
AdygheBench scores must be labelled **curriculum mastery**.

## Next step

Review the two CSVs, then create a Qwen-specific SFT-message builder that uses
only rows where `training_eligible == true` and preserves this split exactly.
