# LFM3-1.7B Turkish post-training study

Latest: [pilot160 training and inference completed](PILOT160-RESULTS.md); development grading and large training backup transfer remain pending. This status supersedes preparation/pending notes below.

## Current SFT branch

Pilot80 training, inference and owner review are complete; exp-006 (2e-4) is the working winner. All80 additional reviews are exported in [pilot160](sft-pilot160-v01/README.md). The [next pair](PILOT160-PAIR-PLAN.md) has prepared160-row runners/configs, a separate dev20 and passed local native-label audit; [GPU preflight](SFT160-POD-HANDOFF.md) and training are pending the new pod. Evaluation baseline is untouched LiquidAI/LFM3-1.7B; initialization remains fresh LoRA on the pinned CPT-merged parent.

Status: both independent CPT runs trained on 2026-11-12 and synced to W&B.
The slow sequential CETVEL pass was stopped by the owner; partial outputs are
preserved. A new matched 100-item batched screening protocol (rp1.15) is complete.
See [GPU session](GPU-SESSION-20261112.md) and `cpt-eval-fast100-v02.json`.

Owner-approved question: how do four practical post-training recipes change Turkish language and task performance, and at what compute cost?

Start with `exp-000-baseline`. Planned training order: CPT, SFT, pure DPO, GRPO. Each starts independently from the same pinned original post-trained `LiquidAI/LFM3-1.7B`, not the previous arm. These recipes use different data; results cannot isolate algorithm effects alone. Future training experiments receive separate IDs after their recipes are frozen.

All checkpoints receive the same frozen multi-capability evaluation. Report grammar, language modeling, extraction, grounded QA, tools, and English regressions separately. No single winner score is planned. One seed is exploratory; repeat promising comparisons before claiming reliable gains. Public benchmark pretraining contamination remains possible.

The earlier thinking-SFT/TDD study remains paused. Its data and results are not inputs to this study.

| Experiment | Status | Change |
|---|---|---|
| exp-000-baseline | completed | Original LFM; recovered results |
| exp-001-wiki-cpt | trained; screened100 | 2.202M Wikipedia tokens, LoRA CPT |
| exp-002-mixed-cpt | trained; screened100 | Same Wiki plus 7.793M FineWeb train tokens |
| exp-003-cpt-cont-50m | trained/evaluated | Cumulative CPT continuation |
| exp-004-cpt-cont-100m | trained/evaluated; published CPT | Pinned initialization for later SFT branch |
| exp-005-sft-lr1e4 | completed; owner reviewed | Pilot80 lower LR |
| exp-006-sft-lr2e4 | completed; working pilot80 winner | Owner preference10/6/4 over exp005 |
| exp-007-sft160-lr1e4 | training/inference completed; dev grading pending | Reviewed160, checkpoints60/100 |
| exp-008-sft160-lr2e4 | training/inference completed; dev grading pending | Same160 recipe except LR2e-4 |

Both CPT adapters start independently from the original pinned checkpoint. A later
CPT -> Occam SFT branch for concise, correct responses was explicitly requested;
it is separate from the original independent-method comparison above. Audit Occam
provenance, targets and overlap before any SFT. No Occam ingestion into CPT.

Both matched fast100 screening and local recovery are complete. See [results](CPT-FAST100-RESULTS.md). Use
100 examples for early screening, extend the same cohort to 200 for promising
checkpoints, and reserve 500 for finalists. Reuse predictions only with matching
prompts, model and decoding. This comparison cohort is not a pristine final test.
The model card's general preset (temperature0.1, top_k50, repetition_penalty1.1)
is a future protocol candidate; current fast100 stays greedy/rp1.15 for all models.

## Direct-base initialization diagnostic

The matched160-row control is complete: [plan and status](BASE-SFT160-ABLATION.md), [measured comparison](BASE-SFT160-INFERENCE-RESULTS.md), [qualitative observations](BASE-SFT160-QUALITATIVE-NOTES.md). All six old/new LoRAs and required logs are verified locally. Four-way Argilla review is ready; no new quality winner is inferred from automatic scores.

## Next diagnostic: matched language transfer

Prepared `crosslingual-holdout-v01`: three matched cases in four language directions (12 prompts), plus three symbolic arithmetic controls. No inference run yet. See `CROSSLINGUAL-NEXT-STEPS.txt` for GPU/Argilla instructions and the conditional bilingual pilot. Keep all evaluation variants outside training; this tiny set becomes diagnostic development data once used for decisions.
