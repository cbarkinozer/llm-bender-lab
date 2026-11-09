# Completed five-case review ? 2026-11-09

Raw annotations frozen before unblinding; 5/5 submitted.

| Model | First-ranked cases | Retain | Repair | Reject | vs base W/T/L |
|---|---:|---:|---:|---:|---|
| base | 2 | 0 | 3 | 2 | ? |
| historical_A | 0 | 0 | 2 | 3 | 0/1/4 |
| Exp3 | 2 | 0 | 2 | 3 | 2/1/2 |
| Exp4 | 1 | 0 | 2 | 3 | 2/0/3 |

All models: 0/5 complete reference passes; 0/10 gated fault kills. Exp3 wins undo/redo and history preferences; Exp4 wins query preference, being the only complete parseable candidate there. Base wins path and filename preferences. No candidate was marked retain.

These are preferences among defective suites, not successful end-to-end tests. No overall demonstrated utility gain. Further LR sweeping is not supported by this result. Review training-family demonstrations for explicit state tracing, requirement-to-oracle derivation, real-SUT imports and final self-checks; preserve development/holdout boundaries.

Limitations: five adaptive development cases and one reviewer account. Evidence does not explicitly declare AI assistance/prior exposure; do not claim independent human-only validation.
