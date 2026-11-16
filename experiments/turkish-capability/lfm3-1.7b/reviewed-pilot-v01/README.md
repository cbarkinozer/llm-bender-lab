# Owner-reviewed Turkish SFT pilot v01

All 100 Argilla records were submitted. Owner edits replace the complete final target; corrected prompts replace the last user turn. Original fields, exact corrections, ratings and response statuses remain in the snapshot. Argilla was read only and its datasets remain available.

The 80 training candidates and 20 held-out test records retain their frozen assignments. Test references, corrections and variants must never enter training or guide checkpoint selection. This is a small source-balanced calibration pilot, not a representative general Turkish benchmark.

## Length and exposure balance

| Split/source | Rows | Edited | Prompt median | Final median / p90 | Reasoning rows | Target tokens | Target share within split |
|---|---:|---:|---:|---:|---:|---:|---:|
| train/all | 80 | 62 | 62.0 | 200.0 / 632 | 19 | 25505 | 100.0% |
| train/occam | 20 | 2 | 49.0 | 37.5 / 151 | 0 | 1194 | 4.7% |
| train/sft | 20 | 20 | 32.5 | 531.5 / 748 | 0 | 11360 | 44.5% |
| train/atlas | 20 | 20 | 78.5 | 198.0 / 413 | 1 | 4437 | 17.4% |
| train/cot | 20 | 20 | 117.5 | 271.5 / 527 | 18 | 8514 | 33.4% |
| test/all | 20 | 15 | 72.0 | 150.0 / 670 | 4 | 7369 | 100.0% |
| test/occam | 5 | 0 | 66 | 46 / 61 | 0 | 286 | 3.9% |
| test/sft | 5 | 5 | 34 | 642 / 698 | 0 | 3600 | 48.9% |
| test/atlas | 5 | 5 | 81 | 53 / 132 | 0 | 418 | 5.7% |
| test/cot | 5 | 5 | 103 | 395 / 460 | 4 | 3065 | 41.6% |

Counts are source-balanced by design (20/source in train, 5/source in test); token exposure need not be balanced. Training should choose capability and response-length targets deliberately, rather than forcing equal lengths or weighting sources by their raw corpus size. System tokens are reported separately and are not supervised target tokens.

## Before and after corrections

| Split | Original target tokens | Reviewed target tokens | Change | Prompt edits |
|---|---:|---:|---:|---:|
| train | 76675 | 25505 | -66.7% | 54 |
| test | 17946 | 7369 | -58.9% | 12 |

## Other exploratory features

| Split | Final 0–64 / 65–256 / 257–512 / 513+ tokens | Multi-turn | Headings | Lists | Code fences | JSON-like | Tables | Raw >4096 / >8192 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| train | 18 / 27 / 21 / 14 | 0 | 0 | 10 | 0 | 1 | 3 | 0 / 0 |
| test | 7 / 4 / 3 / 6 | 0 | 0 | 7 | 0 | 0 | 0 | 0 / 0 |

Format features are overlapping lexical indicators, not verified task coverage. Source category counts and per-source length distributions are in `eda.json`; they retain upstream labels and are not an adjudicated capability taxonomy.

## Descriptive capability coverage

Agent-assigned primary task labels describe reviewed prompts. They are not owner-adjudicated or evidence of correctness. Labels are frozen in `capability-audit.json`. Technical subject matter does not imply executable coding; JSON-like detection below includes arrays.

| Primary capability | Train | Test |
|---|---:|---:|
| arithmetic_and_constraints | 12 | 2 |
| assistant_identity | 2 | 0 |
| authorization_and_privacy | 1 | 0 |
| clarification_and_uncertainty | 4 | 1 |
| conceptual_explanation | 8 | 3 |
| grammar_and_morphology | 9 | 3 |
| grounded_comprehension | 1 | 2 |
| legal_explanation | 2 | 1 |
| logic_and_critical_reasoning | 6 | 1 |
| planning_and_advice | 18 | 4 |
| rewriting_and_summary | 4 | 2 |
| structured_extraction | 9 | 0 |
| technical_method_and_analysis | 4 | 1 |

## Reasoning and direct answers

Owner-confirmed policy: simple/verbal questions can intentionally have no separate reasoning. An edited answer without tags does not inherit its original reasoning. Both `<thinking>` and `<think>` are parsed into `worked_solution`; `messages` holds the final answer. `reviewed_target` preserves the exact submitted target. Never concatenate both representations or train a reasoning-required system prompt against a direct-only projection without adapting the instruction.

Source system prompts are preserved for provenance. Several request exhaustive detail or mandatory reasoning, while owner edits intentionally teach concise or direct answers. These rows need a separately versioned system-instruction normalization and native-template/loss-mask preflight before training. This export is semantic reviewed data, not an immediately runnable trainer dataset. Final-only supervision also preserves Occam's policy for multi-turn rows.

## Validation and limitations

Exact normalized prompt duplicate groups: 0. Exact final-answer duplicate groups: 0. Cross-split five-word containment candidates (>=0.35): 0. Records with 12-word matches to known protected inputs: 0. Excluded records: 0.

Protected-input checking covers edited prompts and targets against the known CETVEL-500 cohort and public Occam validation prompts. Lexical checks do not establish semantic/cross-lingual benchmark clearance. Correctness ratings express owner approval, not an independent proof of every claim. No rows were silently rebalanced, rewritten, or dropped.

### Targeted content issues to revisit

- `atlas:train.chat.jsonl:312719`: prompt says 20% profit margin, but reasoning and final use 20% markup. Under margin = profit / sale price, 450 / 0.8 * 1.2 = 675 TL; 648 TL requires a markup interpretation. Clarify the prompt or repair both reasoning and final.
- `cot:train.jsonl:247`: introducing some taxes and reducing others is not necessarily a contradiction. The prompt does not establish the same tax/base/time, so the assertion that both cannot be true is too strong. Repair the problem/options or qualify the conclusion.
- `atlas:train.chat.jsonl:213455`: the prompt does not specify unauthorized access. The answer leads with refusal of unauthorized access; review whether a question about authorization or a legitimate HR-access route would better teach selective clarification.

These are targeted agent findings, not an exhaustive second correctness review. Submitted owner text is preserved; none is automatically rejected or silently changed. Resolve confirmed issues before a training-ready release. Absence of reasoning tags is intentional owner policy and is not a defect.

The next growth batch should use a capability taxonomy and fill measured gaps (particularly multi-turn interaction, coding, bilingual translation and varying context lengths) after semantic review confirms actual coverage. Keep concise, medium and long answers when the task calls for them. Keep direct versus reasoning modes distinct; do not select verbose answers just to equalize token totals.

## Files and reconstruction

- `train.jsonl` / `test.jsonl`: applied owner corrections, source lineage and separate worked solutions.
- `argilla-submitted-snapshot.json`: complete reviewed records and original UI fields, with no credentials.
- `row-metrics.jsonl` / `eda.json`: measured features, distributions, duplicate candidates and longest targets.
- `manifest.json`: hashes and policy; `excluded.jsonl`: excluded decisions (empty if all accepted).
- Run `python scripts/datasets/export_turkish_reviewed_pilot.py`; the frozen snapshot is reused. Pinned local review packets and tokenizer are required to reconstruct. No live annotations are overwritten.
