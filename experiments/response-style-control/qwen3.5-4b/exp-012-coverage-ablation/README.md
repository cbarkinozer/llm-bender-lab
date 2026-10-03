# exp-012-coverage-ablation — B

Status: trained (four epochs / 40 steps); all 20 primary outputs reached native
EOS. Human comparison is ready; full local backup verification passed.
All 24 new targets were approved as-is in conversation and frozen on 2026-10-03.
Actual-batch and W&B checks passed; user explicitly waived repeat smoke/tiny-
overfit and pre-training reload. Saved-adapter reload passed through inference.
See GPU-RUN-NOTES.md. Active config: config-reviewed-v1.yaml, mirrored in
training-preflight-v1/training-config.json. config.yaml remains the draft record.

## Design

The user approved B as a data-composition intervention, not a rewrite of all
existing answers: retain 56 reviewed rows, replace 24 simple examples with
distinct scenarios teaching grounded and useful reasoning. Train from the same
fresh pinned base as A for four epochs, 40 steps, at LR 1e-4 and rank/alpha 16.
All other training settings and the 20 validation items remain unchanged.

The removed IDs and the one-to-one replacement positions are recorded in
data-draft-v1/manifest.json. Six examples each are removed from grammar correction,
answer extraction, numeric/entity extraction and summarization; two controls per
reduced family remain. All eight existing examples in each of Turkish precision,
non-anthropomorphism, useful explanation, grounded completion, selective
clarification and consistency are retained verbatim as row objects. Original
reviewed-v2 files are never edited. Replacements occupy removed rows' positions.

The new tranche contains ten explanations/recommendations, six evidence-bound
answers, four selective-clarification examples and four consistency/constraint
examples. New examples are project-agent-authored Turkish drafts, not summaries
of newly generated base answers. Their full authoring brief and limitations are
in candidate_specs.py. No third-party dataset or external generation API was used.

## Review completed

User message: "i checked them, they seem fine". Approval is recorded in
user-approval.json and copied into data-reviewed-v1; it binds all 24 IDs and the
exact draft SHA-256. Argilla had zero responses and was not modified. Do not
claim that 24 annotation responses were submitted. No further review is needed
unless the user wants edits. Training and primary inference are now completed.

Original review instructions and queue remain below for history:

Review only the [24 new answers in Argilla](http://127.0.0.1:6900/dataset/0e41d340-72a7-4643-a4ec-6c58917873ce/annotation-mode?page=1&status=pending).

- accept: use the proposed answer as-is.
- rewrite: enter your corrected answer in corrected_answer.
- reject: unsuitable question; describe the problem in notes. We must resolve
  rejected examples before B can train; no silent substitution or reduced count.

Judge substance and natural Turkish before shortness. Keep the useful rationale,
conditions and uncertainty. Remove filler, not necessary explanations. Existing
56 answers do not need to be annotated again. No new validation review queue.

CSV fallback: data-draft-v1/candidates-24.csv. The review exporter uses Argilla;
CSV edits are not silently imported as approved targets.

## Checks and confounds

Local checks passed against current 80 training / 20 validation prompts, 348
historical benchmark rows and 3,500 historical training rows (these inventories
overlap; not 3,500 unique scenarios). Exact normalization and turn-aware lexical
similarity checks detected no matches/flags. Candidate scenario groups are unique;
nearest validation comparisons are preserved. Agent scenario inspection is not
proof of universal semantic independence. The existing 20 remain development data.

Pinned-tokenizer preview passed: zero truncation at 1024; final-answer-only masks;
EOS supervised; validation tokens identical to A/exp009. Training target tokens
per epoch: A 5,384; B draft 6,594 (+22.47%). These numbers will be recomputed
after your edits. Equal 80-row/40-step schedules do not equalize token exposure
or update magnitude. B versus A changes coverage, targets and supervised-token
exposure; do not describe any gain as isolated proof of target quality.

## Safety and rebuilding

Draft training-preflight-draft-v1/report.json deliberately has status
draft-not-approved. Planning config.yaml has an invalid sentinel training hash
and points at absent data-reviewed-v1. The shared GPU runner refuses the draft.

For submitted Argilla reviews, run export_review.py with the tokenizer-capable CPU Python.
It reads annotations without modifying them, validates frozen input fields,
requires exactly one submitted accept/rewrite per row, preserves the original
56 and validation, repeats leakage/tokenization checks and freezes a new reviewed
dataset/config/preflight. Rejected, missing or empty reviews fail before writing.
Existing frozen exports are never overwritten.

Alternatively, an explicit --approval-file can record the user's conversational
accept-all-as-is decision against all 24 IDs and their exact draft hash, only if
there are no Argilla responses to conflict with it. This option was used for this
freeze; it does not manufacture responses or auto-approve future candidates.

CPU preparation: python prepare_pair.py. Tests: python test_preparation.py.
Argilla import: python import_review.py using the existing Argilla SDK venv.
No training, W&B run, base generation or GPU connection is performed by these scripts.

See [GPU-HANDOFF.md](GPU-HANDOFF.md) and [EVALUATION.md](EVALUATION.md).
