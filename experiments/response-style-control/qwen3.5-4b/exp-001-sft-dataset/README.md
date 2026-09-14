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
- `bare_qa_span.csv` — **not yet added.** 599 rows were generated but still
  have two unresolved issues: (1) the same carrier-sentence-cloning problem
  as `bare_gec` had (within each domain×answer_type cell, ~8-13 rows share
  one sentence skeleton with only an entity swapped), and (2) a real
  correctness bug — a `phrase`-type question template
  (`"... ile ilgili yeni kuralın özü nedir?"`) was reused on a passage that
  isn't about a rule at all, and contains its own grammar error
  (`"Kreşte ile ilgili"`). Fix before adding to the repo.

In progress — `bare_gec` is generated and diversity-fixed but not yet
per-row reviewed; the other 4 categories are not started.
