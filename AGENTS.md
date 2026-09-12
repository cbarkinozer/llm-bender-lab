# Agent Instructions

Before making changes, inspect the repository structure and read the documentation relevant to the task.

Use the following documents as the source of truth:

- `docs/finetuning-playbook.md`
  - training decisions
  - debugging
  - smoke tests
  - tiny overfit
  - OOM handling
  - loss diagnostics
  - checkpoint selection
  - post-training diagnosis

- `docs/experiment-guide.md`
  - creating and naming experiments
  - experiment folder structure
  - configs
  - result recording
  - experiment lifecycle

- `docs/dataset-guide.md`
  - dataset creation
  - formatting
  - provenance
  - deduplication
  - splits
  - leakage prevention
  - token-length analysis
  - dataset publishing

- `docs/evaluation-guide.md`
  - baseline evaluation
  - benchmark selection
  - generation configuration
  - target/supporting/regression metrics
  - checkpoint comparison
  - manual evaluation

- `docs/reproducibility.md`
  - seeds
  - model revisions
  - dataset revisions
  - environment versions
  - Git commits
  - experiment manifests
  - artifact tracking

## Required behavior

Before answering a repository-specific question or modifying code:

1. Identify which part of the workflow the task belongs to.
2. Read the corresponding document(s) above.
3. Inspect the relevant experiment README and config if one exists.
4. Base decisions on repository guidance rather than generic assumptions.
5. Do not silently override documented experiment decisions.
6. If repository documentation conflicts with a generic best practice, follow the repository documentation unless the user explicitly asks otherwise.
7. If a decision is not covered by the documentation, use engineering judgment and document the new decision if it is likely to matter again.

## Fine-tuning work

Before starting or modifying a training run, consult:

`docs/finetuning-playbook.md`

Do not start a full run unless the required pre-run checks have passed.

## Dataset work

Before creating, modifying, filtering, or publishing a dataset, consult:

`docs/dataset-guide.md`

Never train on benchmark or test data.

## Evaluation work

Before adding or modifying a benchmark or comparing models, consult:

`docs/evaluation-guide.md`

Keep baseline and fine-tuned evaluation conditions comparable.

## Experiment work

Before creating a new experiment, consult:

`docs/experiment-guide.md`

Prefer one primary hypothesis per experiment and preserve previous experiment results.

## Reproducibility

For any meaningful experiment change, consult:

`docs/reproducibility.md`

Preserve enough information to reproduce the run later.

## General engineering rules

- Do not commit secrets.
- Do not commit large checkpoints or model weights.
- Do not add frameworks solely for completeness.
- Prefer simple and explicit implementations.
- Avoid premature abstractions.
- Fail loudly when important assumptions are violated.
- Do not change multiple experimental variables without documenting why.