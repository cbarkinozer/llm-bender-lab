# exp-001-sft-dataset

- `taxonomy.md` — full spec: categories, per-category input/target rules,
  contamination avoidance, schema, sizing, and the stage-2 DPO plan.
- `quota-matrix.csv` — one row per category with `target_count` to fill in
  `generated_count`/`accepted_count` while generating.
- `master-schema-template.csv` — column layout plus one labeled example row
  (delete the example row before adding real data).
- `bare_gec.csv` — 500 rows, generated then reviewed. Initial batch had a
  severe repeated-closing-clause problem (76% of rows shared one of 17
  boilerplate tail phrases, some of which carried the actual injected error
  and couldn't be blindly swapped); fixed in two passes — decorative tails
  replaced from a diverse pool, error-bearing tails replaced with
  hand-authored alternatives that preserve the exact same
  error/correction pair. Max repeat count for any full closing phrase is
  now 2 (down from 100). Per-row `quality_status` is still `needs_review` —
  the tail-diversity fix is not a substitute for the full manual review
  pass in `dataset-guide.md` §25-28.
- `bare_qa_span.csv` — 547 rows (down from an initial 599; some dropped
  during the fix pass below), fixed with Codex and re-verified here. The
  original batch had the same carrier-sentence-cloning problem as
  `bare_gec` (within each domain×answer_type cell, ~8-13 rows shared one
  sentence skeleton with only an entity swapped) plus a real correctness
  bug — a `phrase`-type question template
  (`"... ile ilgili yeni kuralın özü nedir?"`) reused on a passage that
  wasn't about a rule at all, with its own grammar error
  (`"Kreşte ile ilgili"`). Both fixed: 544/547 rows now have distinct
  sentence skeletons (multiple rotating structures per answer type, not one
  clone), and the mismatched template only appears once, correctly. Still
  `needs_review` per-row — this fix is diversity/correctness triage, not
  the full manual review pass in `dataset-guide.md` §25-28.

## Terse summary candidate

`terse_summary.csv` contains 500 synthetic v4 candidate rows. V4 fixed the
previously found faithfulness bugs, removed the explicit instruction prefix to
match the CETVEL-like `Başlık`/`Metin`/`Özet` prompt shape, and fixed three
impossible age/experience combinations. Exact source/artifact hashes and the
current review state are recorded in `terse_summary.manifest.json`.

This remains an unsplit, contamination-pending `needs_review` candidate pool;
it must not be used for training before the final combined review.

## Numeric/entity precision QA candidate

`numeric_entity_precision_qa.csv` contains 500 synthetic v1 candidate rows.
Each passage includes a plausible same-type distractor, while its target is
the bare answer span only. The checked source/artifact hash and current review
state are recorded in `numeric_entity_precision_qa.manifest.json`.

This remains an unsplit, contamination-pending `needs_review` candidate pool;
it must not be used for training before the final combined review.

## Open-ended counterexample candidate

`open_ended_counterexample.csv` contains 400 synthetic v1 candidate rows. It
teaches that genuinely open-ended Turkish requests merit natural, discursive
answers, preventing this experiment from accidentally teaching blanket
terseness. Import validation confirmed the exact source/artifact hash, valid
two-message rows, zero exact repeated assistant sentences, and absence of the
previous malformed health-domain fragments. Details are in
`open_ended_counterexample.manifest.json`.

This remains an unsplit, contamination-pending `needs_review` candidate pool;
it must not be used for training before the final combined review.

All five candidate pools are now generated and through initial structural,
diversity, and correctness triage. The next gate is a final combined manual
review, then contamination/deduplication checks, splitting, and full
pre-training validation.

## Manual review UI

`annotation/argilla/` provides a localhost-only Argilla review workflow for
the five candidate pools. It preserves candidates as immutable source artifacts
and exports submitted human edits as separate, ID-keyed review artifacts. See
[`annotation/argilla/README.md`](annotation/argilla/README.md).

## Current manual-review state

The immutable candidate pools are never edited during review. Reviewed layers
are derived artifacts, with a hash-checked decision snapshot and manifest.

- `reviewed-v1/` records the first 47 human-reviewed rows and its 2,400-row
  pending pool.
- `reviewed-v2/` adds the next 30 human-reviewed rows: 77 accepted rows in
  total and 2,370 records still awaiting review.
- `reviewed-v2/argilla-v2-decisions.json` preserves the exact Argilla
  responses and notes used for that derived version.
- `reviewed-v2/pending-after-v2.csv` is the only active review input. All of
  its rows are explicitly marked `needs_review`.

The second pass also repaired only repeated defects directly evidenced by the
reviewer: 27 malformed year-source sentences, 35 missing `TL'dir` copulas in
price questions, 73 redundant product labels, and 4 `arttırdı` spellings.
These mechanical repairs are not approvals; the rows remain in the manual
review queue.

## Final reviewed layer

`reviewed-v3/accepted-reviewed.csv` is the final exp-001 reviewed artifact:
all 2,442 rows are marked `accepted`, with no exact duplicate user/assistant
pairs. Five duplicate GEC copies were removed from the source artifact rather
than merely filtered at training time. `argilla-v3-decisions.json` preserves the 56 saved decisions
from the final sampling pass and `manifest.json` records every input/output
hash and finalization rule.

Before finalization, the QA source text received a last template-level repair
pass. It removed malformed temporal formulations, 24 remaining
`Yapılan araştırmalara göre … konumlandırılmıştır` location templates, and 73
`uzmanlara göre … olarak tanımlanmaktadır` templates. These became direct,
natural source sentences while keeping each target answer span unchanged.
