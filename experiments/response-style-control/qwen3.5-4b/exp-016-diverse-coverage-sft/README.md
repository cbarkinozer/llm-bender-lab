# exp-016-diverse-coverage-sft (F)

## Status

Completed2026-10-04:104rows,40steps,3.0769epochs,106.8984seconds;32/32nativeEOS.
Actual token exposure19131supervised/37334input,320microbatches. Final adapter
and all essential evidence hash-verified locally; human review completed.
Canonical base/C/E/F32 comparison and recovery details live in exp015/gpu-results-v1.
User waived F smoke/tiny explicitly; actual masks/W&B and final reload verified.
Use config-reviewed-v1.yaml/data-reviewed-v1/training-preflight-v1;
config.yaml remains blocked draft history. Selected experimental style candidate;
this SFT phase closed2026-10-04. See phase-closure.json and publication drafts.
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

The paragraph below records the pre-run freeze, not the current lifecycle status.
Final F6216 vs E5121 supervised tokens per dataset (+21.4%, not runtime exposure).
All24 new rows reviewed; retained80 E rows identical.32 eval questions remain
separate. No item-level leak identified; shared task-family/generic-answer
limitations documented in exp015/data-reviewed-v1/SEMANTIC-LEAKAGE-REVIEW.md.

Final32 development grades: F26pass/3partial/3fail, E24/3/5, base17/11/4.
External500 new source-group questions: median tokens98 base vs26 F;
blind30 preferences F19/base6/tie2/neither3, grades F23/4/3 vs base21/3/6.
Reviewed QA12/12 pass for BOTH; preference/compliance is not new knowledge.
GEC pass4/6 vs0/6; translation5/6 each. Summary pass F2/6 vs base4/6:
possible task regression despite higher ROUGE. No zero-forgetting/hallucination claim.
Selected for concise/direct Turkish response style with these documented limits.
No further GPU work now; summary/de-da interventions and agentic RL are deferred.
Model/dataset cards and Turkish blog: ../../../../docs/publication/README.md.
Publication is not yet executed; rights/provenance/license choices remain required.
