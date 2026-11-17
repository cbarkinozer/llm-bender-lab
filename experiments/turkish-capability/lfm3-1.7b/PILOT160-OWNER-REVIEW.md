# Pilot160 owner review

All20 owner reviews were submitted and parsed without invalid rankings. Raw Argilla responses are preserved in the ignored runtime snapshot; verbatim rankings, reasoning, decoded preferences and snapshot/key hashes are recorded in `PILOT160-OWNER-REVIEW.json`. Argilla annotations were not modified.

Selected working checkpoint: **exp-007-sft160-lr1e4-step60**, LR1e-4, epoch3. This is checkpoint60 from a100-step/five-epoch cosine schedule, not a separately trained three-epoch schedule. It wins head-to-head against every other candidate.

| Selected checkpoint versus | Wins | Losses | Ties |
|---|---:|---:|---:|
| Untouched LiquidAI base | 16 | 4 | 0 |
| Same LR, step100 | 9 | 1 | 10 |
| LR2e-4, step60 | 7 | 5 | 8 |
| LR2e-4, step100 | 10 | 5 | 5 |

It occupies the top preference group on12/20 prompts, including ties. The closest rival is LR2e-4 step60; the7-5 comparison with8 ties is a modest preference, not decisive statistical evidence. The20 prompts are development selection data, not a final unbiased test. Comparisons within a prompt are correlated; pooled pairwise outcomes are not independent trials.

Owner reasoning identifies continuing problems with Turkish spelling and natural wording, preserving meaning during rewriting, ambiguity, unsupported assertions, and instruction constraints. For example, dev01's top outputs still miss spelling corrections; dev02's top rewrite drops the repeated-experiment detail; dev04 does not resolve ambiguity appropriately; dev18's answers are all poor; dev19 does not clearly explain the contextual sense of 'ince'. Conversely, dev03's top sentence merge and dev05's top grounded summaries are described as fully correct. Relative wins must not be converted into an absolute pass rate. No extra correctness labels were inferred.

Prefer step60 over step100 for this recipe: owner preference favors the earlier checkpoint at both learning rates. This observation does not establish the optimal number of epochs generally. The selected checkpoint also has the highest recorded TurBLiMP subset accuracy,86.625%, but owner preferences drive selection.

Recovery update: all six old/new adapters and required logs are now verified locally; see BASE-SFT160-BACKUP.json. Retain the selected checkpoint for subsequent evaluation. Use these development failures to define capability categories for future training data, without copying these prompts, owner reference answers, or close derivatives into training. A fresh independent evaluation is needed before making broader quality claims. No further training, publishing or deployment was started.
