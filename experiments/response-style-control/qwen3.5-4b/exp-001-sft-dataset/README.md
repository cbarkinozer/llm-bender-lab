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

In progress — `bare_gec` and `bare_qa_span` are generated and
diversity/correctness-fixed but not yet through per-row manual review; the
other 3 categories are not started.
