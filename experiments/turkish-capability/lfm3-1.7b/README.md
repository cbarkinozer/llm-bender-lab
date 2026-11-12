# LFM3-1.7B Turkish post-training study

Status: baseline completed and local recovery verified. On 2026-11-12 owner approved preparation of two independent CPT runs: 2.202M Wikipedia and 10M Wikipedia/FineWeb. No CPT training yet. Current checklist: [CPT pair](CPT-PAIR-TODO-20261112.md).

Owner-approved question: how do four practical post-training recipes change Turkish language and task performance, and at what compute cost?

Start with `exp-000-baseline`. Planned training order: CPT, SFT, pure DPO, GRPO. Each starts independently from the same pinned original post-trained `LiquidAI/LFM3-1.7B`, not the previous arm. These recipes use different data; results cannot isolate algorithm effects alone. Future training experiments receive separate IDs after their recipes are frozen.

All checkpoints receive the same frozen multi-capability evaluation. Report grammar, language modeling, extraction, grounded QA, tools, and English regressions separately. No single winner score is planned. One seed is exploratory; repeat promising comparisons before claiming reliable gains. Public benchmark pretraining contamination remains possible.

The earlier thinking-SFT/TDD study remains paused. Its data and results are not inputs to this study.

| Experiment | Status | Change |
|---|---|---|
| exp-000-baseline | completed | Original LFM; recovered results |
| exp-001-wiki-cpt | planned | 2.202M Wikipedia tokens, LoRA CPT |
| exp-002-mixed-cpt | planned | Same Wiki plus about 7.798M FineWeb train tokens |

Both CPT adapters start independently from the original pinned checkpoint. A later
CPT -> Occam SFT branch for concise, correct responses was explicitly requested;
it is separate from the original independent-method comparison above. Audit Occam
provenance, targets and overlap before any SFT. No Occam ingestion into CPT.

Next action: finish CPU pair preparation, then request fresh GPU SSH details and
run real-model smoke/label/tiny-overfit gates before training each adapter. Reuse
the completed baseline under its fixed protocol. See the current CPT pair checklist.
