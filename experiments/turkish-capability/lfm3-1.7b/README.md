# LFM3-1.7B Turkish post-training study

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
