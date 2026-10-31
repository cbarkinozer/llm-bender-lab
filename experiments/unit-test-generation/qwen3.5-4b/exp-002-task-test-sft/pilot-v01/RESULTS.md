# Task pilot results - 2026-10-31

Eight authored task-to-tests candidates from two existing training families;
two planning contexts are separate and excluded from SFT labels. No model baseline,
Qwen training, real model repair trajectory or independent holdout result exists.

| Task | Test cases | Full native tokens | Targeted faults detected |
|---|---:|---:|---:|
| language-basic | 5 | 1353 | 2/2 |
| language-rules | 5 | 1620 | 2/2 |
| language-cli-success | 2 | 1517 | 2/2 |
| language-cli-errors | 3 | 1695 | 2/2 |
| prices-returns | 6 | 1833 | 2/2 |
| prices-charts | 3 | 1809 | 2/2 |
| prices-fetch | 1 | 1608 | 2/2 |
| prices-analysis | 7 | 2328 | 2/2 |

All 32 cases pass, all 16 targeted faults are detected, and all tasks pass seeded
runs 17/43/91. The provider-adapter task has only one collected case, so repeating
it does not constitute a changed-order test. Other seeded runs retain their actual
orders in the archived evidence; no claim of three distinct permutations is made.

Total native conversation tokens: 13763. Maximum: 2328.
The two parent whole-app conversations contained 5738 tokens total, with
a maximum of 3272. Splitting reduces individual sequence length here, while
repeating the app/plan context and adding boundary tests increases overall corpus
tokens. Eight related tasks are still only two source groups, not eight independent
application families. This is a format pilot, not 100 available training tasks.

The check runner verifies pinned external source hashes and saves reference/fault
logs, actual mutation source and collected test orders. Each task has its own
positive and failing controls; fault checks run against that task alone. Source
references are withheld from model input. Host execution is for trusted authored
fixtures with time limits and stripped credentials; network calls are mocked,
not OS-blocked. Requirements still need semantic review as expansion proceeds.
