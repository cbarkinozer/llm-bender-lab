# exp-006-quality-repair-sft

## Status

Dataset frozen after human review and post-review QA. All 100 candidates have
an explicit decision: 69 were rewritten, 31 were accepted, and none were
rejected. The resulting 958-row training artifact is ready for GPU preflight;
full training remains gated on representation, smoke, and tiny-overfit checks.

## Primary hypothesis

Keeping the exp-005 model recipe fixed while adding a separately identifiable,
human-reviewed quality-repair tranche will reduce five observed failure modes
without losing exp-005's gains in directness, plain formatting, brevity, and
non-sycophantic tone.

The five repair families are:

1. hidden ambiguity and assumption-free clarification,
2. unsupported causal/filler completion,
3. Turkish morphology, syntax, and near-term precision,
4. calibrated and warm non-anthropomorphic responses,
5. internal consistency, non-repetition, and semantic integrity.

## Experimental isolation

The first exp-006 run changes data only. It starts from the same pinned base
model, not the exp-005 adapter. Training hyperparameters remain identical to
exp-005. Preference pairs are retained for diagnosis but preference training
is outside this experiment.

## Evaluation integrity

The exp-005 48-item holdout influenced this design and is now development /
diagnostic material. It cannot support an independent final exp-006 claim.
`evaluation/final-holdout-v2.csv` is a fresh, sealed final test. Do not inspect
model outputs from it or use them for data, recipe, or checkpoint decisions.

This internal holdout measures the five repair families, but it is not by
itself independent third-party proof of general model quality. Any later
release claim must also use a version-pinned benchmark not authored for this
project, with its untouched test split excluded from training and evaluated
under a protocol frozen before results are inspected.

## Frozen dataset

- parent artifact: 858 rows from exp-005,
- reviewed repair tranche: 100 accepted rows, 20 per repair family,
- combined artifact: `data/sft-clean-v4-quality-repair-958.csv`,
- canonical-LF combined SHA-256: `bbaab152182318da5aff73a5227b784550933dfac1848037ad86f4cc57a7ebff`.

The full reviewed export is `data/quality-repair-reviewed-100.jsonl`. Two
issues found during the final full-tranche QA pass were corrected only after
explicit reviewer approval; their IDs and rationale remain in the category
exports and quality report.

Validation results:

- exact overlap with the 1,006-prompt prior train/evaluation pool: 0,
- near overlap with that pool at the frozen 0.86 threshold: 0,
- candidate-to-final-holdout near overlap at the frozen 0.82 threshold: 0,
- empty, duplicate, malformed-Unicode, markdown-like, or overlength targets: 0.

Rebuild and validate from the durable category exports:

```powershell
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\export_and_finalize.py
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\validate_artifacts.py
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\validate_reviewed.py
```

## GPU preflight and run order

Use the exp-004 shared training/evaluation entrypoints with this experiment's
complete config. From a clean committed checkout, first generate the untouched
base output on the sealed holdout without inspecting it or changing the
experiment. Then run representation-check, smoke, and tiny-overfit. Start the
full run only after all three pass.

```bash
python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/evaluate.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/config.yaml \
  --role base \
  --output experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/results/final-base.jsonl

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/config.yaml \
  --mode representation-check \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/results/representation-check

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/config.yaml \
  --mode smoke \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/results/smoke

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/config.yaml \
  --mode tiny-overfit \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-006-quality-repair-sft/results/tiny-overfit
```
