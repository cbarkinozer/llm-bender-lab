# exp-016-diverse-coverage-sft (F)

## Status

GPU paired pipeline launched 2026-10-04;104 reviewed training rows frozen and
CPU-checked; canonical baseline generation/required GPU gates precede F SFT.
Use config-reviewed-v1.yaml/data-reviewed-v1/training-preflight-v1;
config.yaml remains blocked draft history. F training has not started at launch.
Shared reviews/export/final leakage signoff live in exp015.

## Question and parent

Does adding24 independent scenarios to E's improved80-example core improve
transfer at the same40-optimizer-step budget? Parent/comparator: exp015 (E).
F starts from the same untouched pinned base, NEVER from E/C's adapter.

## What changes

Exact E80 retained first, in the same order; add24 new questions, four per skill:
Turkish editing/lexical precision, conditional decisions, mechanisms/trade-offs,
faithful summary, selective clarification, listening/neutral interaction.
Different scenes, opposing decision conditions and variable appropriate lengths.
No validation question seeds, direct paraphrases, hidden chain-of-thought or
external teacher API. New grammar/lexical cases include doktoraya/doktor as
explicitly disambiguated uses; no answer-revealing lexical-trap instruction.
Review criteria are metadata, never added to model prompts.

## What remains fixed

All model, LoRA, optimizer, seed, mask/template and inference settings from E.
Explicit40 optimizer steps, cosine horizon40, warmup2. Effective batch8.
With104 rows, roughly3.08 passes rather than E's4; nominal epochs4 is overridden.
Final step40 preselected, saves/evaluation every10 steps. Original20 development
items unchanged; separate12 evaluation-only controls shared with E.

This is addition under a fixed update budget, NOT pure diversity isolation.
Dataset size/task mixture and exposures per original row change. Draft F6179
target tokens versus E5133 per full dataset (+20.4%); per-dataset totals are
not total shuffled40-step exposure. Measure runtime token exposure separately.
Do not attribute a win solely to diversity or claim forgetting prevention.

## Checks, review and next step

104 train tokenized; first80 identical to E,20 validation identical to C.
No1024-token truncation; final-assistant-only masks/native EOS inspected.
Active audit compares24 new+12 controls against current80/20, historical
benchmark/training inventories, earlier B24 and each other. Zero detected
exact/near flags; not a proof of semantic independence.
Use [shared E/F review](../exp-015-target-quality-sft/README.md) and
[evaluation protocol](../exp-015-target-quality-sft/EVALUATION.md).
Human approvals must freeze both arms before GPU launch. Preserve all configs,
logs, source/env/W&B, adapters/resume state and inference before pod termination.

## Results

No model results yet. Reviewed data ready locally, not GPU-ready/completed/selected.
Final F6216 vs E5121 supervised tokens per dataset (+21.4%, not runtime exposure).
All24 new rows reviewed; retained80 E rows identical.32 eval questions remain
separate. No item-level leak identified; shared task-family/generic-answer
limitations documented in exp015/data-reviewed-v1/SEMANTIC-LEAKAGE-REVIEW.md.
