# exp-006-quality-repair-sft

## Status

Design frozen; corrective candidates awaiting human review. No training artifact
may be built until every candidate has an explicit review decision.

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

## Human-review gate

Review the five 20-record Argilla datasets. For each proposed answer choose
`accept`, `rewrite`, or `reject`. A rewrite requires a complete replacement
answer. The reviewed tranche is not frozen until all 100 decisions are
submitted and the exporter passes schema, leakage, and hash checks.

Review links:

- calibrated emotional responses: `http://127.0.0.1:6900/dataset/5a08780f-fead-4a3d-87a9-0bd7f02cf478/annotation-mode?page=1&status=pending`
- consistency and semantic integrity: `http://127.0.0.1:6900/dataset/9c148d1c-9551-4d4e-84dd-63f5eafe5afc/annotation-mode?page=1&status=pending`
- hidden ambiguity: `http://127.0.0.1:6900/dataset/e87c9dbd-0189-4874-9d33-2313dcf7496e/annotation-mode?page=1&status=pending`
- Turkish precision: `http://127.0.0.1:6900/dataset/0d98912f-99c8-4a15-b462-f46919369fc6/annotation-mode?page=1&status=pending`
- unsupported completion: `http://127.0.0.1:6900/dataset/09aec3a7-7636-4c72-968f-93f8d8d94799/annotation-mode?page=1&status=pending`

After all reviews are submitted:

```powershell
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\export_and_finalize.py
```

The command intentionally fails while any record remains pending.
