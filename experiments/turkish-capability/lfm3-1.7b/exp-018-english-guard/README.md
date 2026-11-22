# exp-018: English guard check for arm B (coding and instruction following), 2026-11-22

## Status

completed (design frozen before any result; verdict AMBIGUOUS, see Results)

## Goal

Find out whether exp-016 arm B (CPT parent + self-distilled SFT) kept coding and instruction following, the two model-card
abilities that no earlier run measured. This decides whether arm B can be called a v1 candidate for the owner's goal
(decent Turkish while tool calling, math, coding and instruction following stay mostly fine).

## Hypothesis

Arm B is within 5 points of the base on HumanEval pass@1 and IFEval prompt-level strict accuracy, in both thinking modes.

## Parent experiment

[exp-016](../exp-016-self-distill-targets/README.md) (arm B), compared with the pinned base. Arm A and the plain CPT model
are not run (the decision concerns arm B; this keeps GPU time short).

## What changed

Nothing is trained. New English-only evaluation: HumanEval (164 problems, executed against the unit tests) and a fixed random
270-prompt subset of IFEval (541), one greedy-ish sample per item with the model-card general preset (T 0.1, top_k 50,
rp 1.1), seed 3407, thinking off (1,536 new tokens) and on (6,144; unclosed thinking counts as failed).

## Base model and sources

`LiquidAI/LFM3-1.7B@0dc4268b561499c648c7ba7c9466bf3d8d01517a`; arm B merge as in exp-016. Data, pinned: `google/IFEval@966cd895`
(Apache-2.0), `openai/openai_humaneval@7dce6050` (MIT), IFEval scorer code `google-research/google-research@e6890f85`
`instruction_following_eval/` (Apache-2.0, fetched at run time, not committed). Checksums and the subset indices are in each
run's `run-manifest.json` (`sources.json`).

## Pre-registered rule (per metric and thinking mode; paired by item, bootstrap 95% interval on arm B minus base)

Cells: IFEval strict x {off, on}, HumanEval x {off, on}. PASS when the point difference is at least -0.05 and the interval's
lower bound is at least -0.10; FAIL when the point difference is below -0.10; otherwise AMBIGUOUS. The guard passes only if all
four cells PASS; AMBIGUOUS cells are rerun on the full IFEval or decided with the owner, never silently accepted. IFEval loose
accuracy is reported but not decisive.

Detectable difference: with 270 IFEval items and 164 HumanEval items, paired differences below about 6-8 points cannot be told
from noise, so a PASS means "no evidence of a drop larger than that", not "no drop".

## Threats to validity

- One sample per item at low temperature; thinking-on answers can fail by running out of tokens rather than by capability.
- IFEval is a subset (half); HumanEval is small and widely seen (possible contamination affects both models equally).
- Pass is relative to the base, not an absolute quality bar; English only; Turkish instruction following is not measured.
- HumanEval scoring executes model code (pod only, timeout and memory limit).

## Results (RTX 4090, 2026-11-22; summaries in `results/`, raw answers in ignored `results-local/`)

Run 1 (270 IFEval prompts, 164 HumanEval problems, both thinking modes; about 13 min of GPU):

| Cell | Base | Arm B | Difference (paired 95% interval) | Verdict |
|---|---:|---:|---|---|
| IFEval strict, thinking on (n=270) | .841 | .837 | -0.004 (-0.048, +0.041) | PASS |
| HumanEval pass@1, thinking on (n=164) | .927 | .933 | +0.006 (-0.018, +0.031) | PASS |
| HumanEval pass@1, thinking off (n=164) | .762 | .750 | -0.012 (-0.085, +0.061) | PASS |
| IFEval strict, thinking off (n=270) | .707 | .626 | -0.082 (-0.141, -0.022) | AMBIGUOUS |

The AMBIGUOUS cell was rerun on the full IFEval as pre-registered (the other 271 prompts, thinking off, both models, same
settings; the first run's 270 are kept, so n=541):

| Cell | Base | Arm B | Difference (paired 95% interval) | Verdict |
|---|---:|---:|---|---|
| IFEval strict, thinking off (n=541) | .730 | .641 | -0.089 (-0.129, -0.046) | AMBIGUOUS |
| IFEval loose, thinking off (n=541) | .765 | .680 | -0.085 (-0.124, -0.044) | (not decisive) |

Guard verdict by the pre-registered rule: **AMBIGUOUS** (three cells PASS, IFEval strict thinking off has a point difference
between -0.05 and -0.10 and an interval reaching below -0.10). With 541 prompts the drop is a real one of roughly 5 to 13 points.

Exploratory breakdown of the thinking-off drop (post hoc, not pre-registered; n per category in parentheses):

| IFEval category | Base | Arm B | Difference |
|---|---:|---:|---:|
| response language (31) | .87 | .55 | -.32 |
| length constraints (133) | .64 | .50 | -.14 |
| detectable format (155) | .79 | .66 | -.14 |
| detectable content (52) | .79 | .67 | -.12 |
| keywords (148) | .57 | .47 | -.10 |
| change case (84) | .62 | .55 | -.07 |
| punctuation (66) | .70 | .65 | -.05 |
| combination (65) | .58 | .58 | .00 |
| start/end (66) | .79 | .80 | +.02 |

Without the 31 prompts that ask for a response in another language the difference is -0.075 (-0.118, -0.033), so the language
category explains little of it (the owner is willing to lose other languages anyway). Arm B's thinking-off IFEval answers are
shorter: 260 generated tokens on average against 420 for the base.

## Token budget with thinking on (post hoc, from the saved answers; no new generation)

Owner's usage assumption: thinking is on and callers may have a small context budget (8k or 16k per call). An answer counts as
correct only if it finished (thinking closed, EOS) within the budget of generated tokens; everything else counts as wrong.
Generation cap in these runs: 6,144 tokens (IFEval, HumanEval) and 8,192 (math, exp-017).

| Cell (thinking on) | Model | 1k | 2k | 3k | 4k | 6k | 8k | median / p90 tokens |
|---|---|---:|---:|---:|---:|---:|---:|---|
| IFEval strict (270) | base | .16 | .42 | .60 | .70 | .83 | .83 | 2283 / 6144 |
| IFEval strict (270) | arm B | .27 | .56 | .67 | .76 | .84 | .84 | 1563 / 4836 |
| HumanEval (164) | base | .27 | .57 | .75 | .85 | .93 | .93 | 1666 / 4259 |
| HumanEval (164) | arm B | .30 | .63 | .82 | .88 | .93 | .93 | 1628 / 4201 |
| math, English (152 x 4) | base | .70 | .84 | .89 | .93 | .94 | .95 | 553 / 2789 |
| math, English (152 x 4) | arm B | .73 | .85 | .90 | .91 | .94 | .94 | 551 / 2636 |
| math, Turkish prompt+reply (152 x 4) | base | .32 | .53 | .59 | .64 | .67 | .69 | 1581 / 7595 |
| math, Turkish prompt+reply (152 x 4) | arm B | .43 | .51 | .56 | .58 | .60 | .61 | 957 / 6352 |

Reading: accuracy stops improving at about 6k generated tokens, so budgets of 8k or 16k per call lose nothing for English
tasks. At 4k the base loses about 13 points on IFEval and 8 on HumanEval against its own ceiling, arm B about 8 and 5, because
arm B thinks shorter; at every budget arm B is at least as good as the base on IFEval, HumanEval and English math. Turkish math is
the exception: above 3k tokens arm B is about 5-9 points below the base (the exp-017 reading regression), below 2k it is ahead.
Caveats: the budget here counts generated tokens only (prompt and tool outputs come on top); real clients truncate rather than
score, and a truncated thought gives no answer.

## Regressions

IFEval with thinking off, about 8 points (73% to 64% strict). Nothing else measured here regressed beyond noise.

## Conclusion

Arm B kept coding in both thinking modes and instruction following with thinking on. With thinking off it loses about 8
points of IFEval, concentrated in length, format and keyword constraints, and its answers are shorter. The drop is probably
caused by the exp-016 training targets: answers longer than 1,500 characters were dropped (mean target 659 characters), which
may have taught shorter answers and hurt "at least N words" style constraints. That is a hypothesis; it was not tested.
The model's default chat template has thinking on, where there is no measured drop. For the owner's goal (decent Turkish,
tools/math/coding/instructions mostly kept), arm B is a usable v1 candidate with one known cost; the pre-registered guard is
formally AMBIGUOUS, not PASS.

## Owner decision (2026-11-22) and model-card notes

The owner assumes thinking on and accepts the thinking-off IFEval drop if the model card states it. The model card should say:
thinking-off instruction following is about 9 points lower than the base (IFEval strict .641 vs .730) and answers are shorter;
thinking mode needs roughly 4-6k generated tokens for full accuracy (8k or 16k total budgets are fine); Turkish math word
problems with thinking on are about 7 points below the base at large budgets (.61 vs .69); other languages were not trained
or evaluated.

## Next step

The owner accepted the thinking-off drop for v1 (documented in the model card). Publishing needs a separate approval. If the
Turkish-understanding training goes ahead, include answers longer than 1,500 characters and constraint-following rows (length, format, keywords) so
the length bias is not repeated, and rerun this guard on the new model. GPQA and Turkish instruction following are still not
measured.
