# LFM3-1.7B Turkish post-training study

Status: baseline completed and local recovery verified, 2026-11-11. No CPT training yet; owner deferred training until next session.

Owner-approved question: how do four practical post-training recipes change Turkish language and task performance, and at what compute cost?

Start with `exp-000-baseline`. Planned training order: CPT, SFT, pure DPO, GRPO. Each starts independently from the same pinned original post-trained `LiquidAI/LFM3-1.7B`, not the previous arm. These recipes use different data; results cannot isolate algorithm effects alone. Future training experiments receive separate IDs after their recipes are frozen.

All checkpoints receive the same frozen multi-capability evaluation. Report grammar, language modeling, extraction, grounded QA, tools, and English regressions separately. No single winner score is planned. One seed is exploratory; repeat promising comparisons before claiming reliable gains. Public benchmark pretraining contamination remains possible.

The earlier thinking-SFT/TDD study remains paused. Its data and results are not inputs to this study.

Next action: follow exp-000-baseline/TODO-20261112.md; reuse the completed baseline under its fixed protocol, validate GPU training, then run the notebook-derived CPT pilot. Turkish extraction/tool/preference data remain future-arm decisions, not blockers for this baseline. See `exp-000-baseline/README.md`.
