# exp-016: self-distilled SFT targets (pilot, 2026-11-22)

Question: do SFT targets written by LFM3 itself stop the collapse of thinking-off arithmetic and tool calling that
every externally authored SFT run showed (exp010-exp015)? Plan: [../SELF-DISTILL-PLAN-20261121.md](../SELF-DISTILL-PLAN-20261121.md).

## What was done

- Prompts, recipe, order and four directions of exp014 (`cookbook-sft-v01/train.jsonl`, groups of
  tr->tr, en->tr, tr->en, en->en). Only the targets changed.
- LFM3 (pinned base, vLLM, model-card presets) answered each group's English prompt 4 times in its native mode
  (thinking off for direct groups, on for the 30 reasoning groups). Per group the shortest complete (EOS) sample is kept.
  English rows use it unchanged (reasoning kept in the model's own English). Turkish rows use a Turkish rendering of the
  final answer written by Claude (Sonnet 5.5), checked automatically (numbers and code spans must survive) and not by a
  second AI. No correctness filtering (the unfiltered arm of the plan).
- Groups dropped (31 of 160): 6 where the model never finished an answer within the token budget, 24 whose own answer
  exceeded 1,500 characters (writer cost cap; also brings the mean target to 659 characters, exp014: 733), 1 over the
  4,096-token limit. Result: 129 groups, 516 rows, 84 with reasoning. `build-report.json` lists everything.
- Training: exp014 recipe (LoRA r32/alpha64, LR 1e-4, 2 x 4 batch, completion-only loss through native TRL, sequential
  sampler), exposure per row matched to exp014 (55 steps, cosine horizon scaled to the same stop fraction), one seed.
  92 s on the 4090, reload parity exact.
- Evaluation: eval v2 (seed 3407, both thinking modes) plus the frozen TurBLiMP subset (1600 pairs). Results in
  [../eval-v2/results/baseline-20261122](../eval-v2/results/baseline-20261122/README.md).

Arms (all unfiltered; deviations from the plan are exploratory, not planned single-variable comparisons):
A = base parent, 55 steps. B = CPT-merged parent, 55 steps. C = base parent, 3 passes (165 steps).

## Results (accuracy; `off`/`on` = thinking mode)

| Model | math EN off/on | math TR off/on | symbolic EN off | tool EN off/on | tool TR off/on | TurBLiMP |
|---|---|---|---:|---|---|---:|
| base | .89 / .95 | .39 / .72 | .97 | .95 / .95 | .74 / .82 | .718 |
| CPT | .57 / .93 | .03 / .63 | .50 | .06 / .91 | .00 / .75 | .869 |
| A (base + SD) | .86 / .94 | .32 / .60 | .83 | .90 / .96 | .76 / .81 | .718 |
| B (CPT + SD) | .86 / .93 | .21 / .59 | .85 | .88 / .94 | .69 / .80 | .868 |
| C (base + SD x3) | .85 / .95 | .34 / .59 | .88 | .86 / .91 | .76 / .86 | .708 |

## Conclusions (one seed; intervals are in the compare files, differences below about 5-9 points are noise)

1. **The self-distilled targets stop the collapse.** Thinking-off English symbolic arithmetic is 0.83-0.88, tool calls
   0.86-0.90; earlier SFT runs collapsed to 12-25% on a smaller control set (not re-measured on eval v2: the exp014
   adapter could not be uploaded). Remaining costs: symbolic EN off is 8-14 points below base (A: McNemar p=0.008, so
   it fails the proposed -5 budget), tool EN off 5-9 points below. With thinking on, English cells are within noise of base.
2. **Arm B is the interesting one.** The published CPT adapter is unusable with thinking off (tool calls 0.06). 55
   steps of self-distilled SFT repair it to base-like English behavior (tool EN .88, symbolic .85, always ends with EOS)
   while keeping the full grammar gain (TurBLiMP .868 vs .869 for CPT, .718 for base). That is the first run in this
   project that has both Turkish grammar and working chat/tool behavior.
3. **No arm improves Turkish task understanding.** Turkish math with thinking on is 12 points below base in all three
   arms (p about 0.003) and with thinking off B is 18 points below. The base model's Turkish gap (math .89 EN vs
   .39 TR off) is unchanged by grammar gains. The SFT rows may even hurt: a likely cause is that the reasoning of
   Turkish rows stays English while the Turkish prompts are now different from the eval prompt style (untested).
4. More passes (C) do not help Turkish (grammar .708, TR math not better). Do not scale this recipe as is.

## Not done / caveats

- exp014 and exp015 were not evaluated on eval v2; the English guard set (IFEval, GPQA, HumanEval+), the answer-language
  check and a filtered arm were not run. The scale gate in the plan is therefore not passed.
- Single seed, small n (math 152, symbolic 60, tool calls 80); Turkish renderings were written by one AI without a
  second-model check. No overlap check between the training prompts and eval v2 items was run.
- Adapters (local only, ignored by Git): `results-local/sft/adapter` (A), `results-local/sft-arm-b-cpt-parent/adapter`,
  `results-local/sft-arm-c-base-x3/adapter`. If published, use base-first names, for example
  `LFM3-1.7B-Turkish-SelfDistill-SFT`; nothing has been published.

## Next (proposed, gated)

Turkish understanding is the open problem, not grammar. Candidates: Turkish-input task data whose targets are still the
model's own (the missing piece is more Turkish prompts, not more Turkish answers), a thinking restatement arm from the plan,
or on-policy distillation from the English answers. Before spending more GPU: finish the guard set and compare with exp014.
