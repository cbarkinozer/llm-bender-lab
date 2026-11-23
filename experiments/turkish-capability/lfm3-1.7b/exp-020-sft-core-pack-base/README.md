# exp-020: the exp-019 pack on the original LFM3-1.7B (no Turkish pretraining), 2026-11-22

## Status

Finished 2026-11-22. One training seed. Rules and gates are those of [exp-019](../exp-019-sft-core-pack/README.md); here
they are applied for information, because exp-020 is an ablation and not a release candidate.

## Question

How much of exp-019's result comes from the SFT dataset alone and how much from the earlier Turkish pretraining (CPT)?
Single change against exp-019: the parent. Same pack (`train.jsonl` sha256 starts `caf7c09ffe15ec6b`, 2,909 rows, the base
model's own verified answers), same LoRA r32/alpha64, LR 1e-4, one epoch, 364 steps, same seed, same evaluation.

Parent: `LiquidAI/LFM3-1.7B` at revision `0dc4268b5614`, no CPT. Training: 1,034 s, mean train loss .376 (exp-019: .458; the
pack is the base model's own text, so it fits the base better than the CPT parent). Audit, reload parity and merge receipt are in
`results/`.

## Results (thinking on unless noted; one seed)

| Measure | base | exp-019 (CPT parent + pack) | exp-020 (base + pack) | exp-020 vs base |
|---|---|---|---|---|
| Diagnostic D (Turkish text, Turkish question) | .691 | .752 | .7105 | +.020 [-.008, +.048] |
| Diagnostic C | .729 | .755 | .7105 | -.018 [-.041, +.003] |
| Diagnostic F | .717 | .773 | .724 | +.007 [-.020, +.033] |
| Diagnostic A / B (English reading) | .949 / .952 | .949 / .938 | .954 / .954 | +.005 / +.002 |
| Final test, Turkish (100 fresh GSM8K items) | .7625 | .770 | .7725 | +.010 [-.015, +.035] |
| Final test, English | .9375 | .930 | .940 | +.0025 [-.015, +.025] |
| Final test without the 4 flawed items (96), Turkish / English | .7943 / .9479 | .7969 / .9453 | .7995 / .9557 | +.005 / +.008 |
| Eval v2 math, Turkish | .717 | .717 | .658 | -.059 [-.118, .000] (lost 15, gained 6, McNemar p = .078) |
| Eval v2 math, English | .954 | .947 | .947 | -.007 |
| Eval v2 tool calls, EN / TR | .950 / .825 | .925 / .850 | .950 / .825 | 0 / 0 |
| Eval v2 symbolic, EN / TR | .967 / .983 | .983 / 1.0 | .967 / .983 | 0 / 0 |
| Belebele Turkish, restricted | .352 | .480 | .414 | +.062 |
| Belebele English, restricted | .670 | .707 | .672 | +.002 |
| TurBLiMP macro | .718 | .854 | .719 | +.001 |
| IFEval strict, thinking on (270) | .841 | .871 | .878 | +.037 [.000, +.074] |
| IFEval strict, thinking off (full 541) | .730 | .710 | .699 | -.031 [-.065, +.002] |
| HumanEval, thinking on / off | .927 / .762 | .915 / .756 | .921 / .835 | -.006 / +.073 [+.018, +.128] |
| Writing probe, thinking off: answers fully in English | 0 / 40 | 0 / 40 | 0 / 40 | |
| Writing probe, thinking off: hit the 800-token cap | 10% | 17.5% | 12.5% | |

Gates, applied as written for exp-019: G1 pass (D +.020 against base; +.099 [+.043, +.155] against arm B), G2 pass, G5 pass,
G6 pass, G7 pass (tools and English math within .05 of base), **G3 fail** (.414 against the .45 floor) and **G4 fail** (.719
against .85). G3 and G4 were set for a CPT parent; exp-020 has none, so failing them is the expected outcome and not a defect of
the pack.

### What the CPT adds (exp-019 minus exp-020, same pack, paired over the 152 diagnostic items)

| Cell | exp-019 - exp-020 |
|---|---|
| D | +.041 [+.003, +.081] |
| F | +.049 [+.002, +.097] |
| C | +.044 [-.002, +.091] |
| G | +.061 [-.021, +.138] |
| A / B (English text) | -.005 [-.023, +.012] / -.016 [-.031, -.003] |
| Belebele Turkish restricted | +.066 |
| TurBLiMP macro | +.135 (.854 against .719) |
| Eval v2 math Turkish | +.059 (.717 against .658; descriptive, not tested here) |

The paired intervals resample items, not training runs; a second seed per parent would be needed to say how much of the
difference is run-to-run noise.

## Reading

1. **The pack alone keeps the skills and does not hurt the base.** English math, tool calls, symbolic items, HumanEval and
   IFEval on are level with the base or above it; thinking-off IFEval is 3 points lower (not significant, exp-019 was 2 lower,
   arm B 9 lower). HumanEval thinking off is 7 points higher; a possible cause is the code replay rows, which was not tested.
2. **The pack alone does not teach Turkish.** Diagnostic cells and the fresh final test sit at the base level (+.01 to +.02, all
   intervals include zero) and TurBLiMP is exactly the base score (.719 against .718). Belebele Turkish rises by 6 points, about
   half of what exp-019 reaches, which suggests the SFT supplies part of the reading-question format and the CPT the rest.
3. **Grammar comes from the CPT.** TurBLiMP moves from .72 to .85 only with the CPT parent. Turkish diagnostic reading gains
   (+.04 to +.05 on D and F) also need the CPT, though the intervals are close to zero at their lower end.
4. **Eval v2 Turkish math is the one measure where exp-020 lands below base** (.658 against .717). The diagnostic cell D says
   +.020 on the same capability, so the true effect of the pack alone on Turkish math is about zero within noise; neither number
   should be quoted alone. One seed.
5. **For the v2 plan:** this is the ablation result the owner's plan assumes. More Turkish pretraining text is the lever for
   grammar and vocabulary; SFT of this kind is the lever for keeping skills, thinking mode and instruction following.

## Writing probe with thinking on (base, arm B, exp-019; not run for exp-020)

The first writing probe ran with thinking off, but the owner uses thinking on. The same 40 native prompts, thinking on, 6,144
new tokens, all answers closed their thinking block and reached the end token.

| | base | arm B (exp-016) | exp-019 |
|---|---|---|---|
| Answers fully in English (heuristic) | 0 / 40 | **31 / 40** | 1 / 40 |
| Unknown-token rate / English-token rate | 4.0% / 1.1% | 44.8% / 43.5% | 3.4% / 1.9% |
| Constraint checks passed (12 prompts) | 10 | 11 | 9 |
| Mean words | 174 | 145 | 165 |

Arm B answers most Turkish writing prompts in English once thinking is on. This had not been measured before (the exp-018
guard uses English prompts); exp-019 and the base do not show it. The single English exp-019 answer is the 30-word summary prompt (wr-tr-18). The thinking-off
exp-019 and exp-020 numbers are in `results/writing/`. Constraint counts come from 12 prompts and cannot separate the models.

### Blind two-score review (naturalness 1-5, task yes/partly/no)

Sheets: [thinking on, base against exp-019](../exp-019-sft-core-pack/results/writing-review-think-on/) (arm B left out, 31 of its
40 answers are English) and [thinking off, base, arm B and exp-019](../exp-019-sft-core-pack/results/writing-review/). **All 200
answers were rated by an AI assistant, not by a native speaker.** Its stated limits: AI rating, same provider as the
training-prompt translator, it read the experiment README before scoring (aggregate results visible, answer keys not opened),
and the thinking-off sheet was rated after the thinking-on one with the same prompts. Integrity checked afterwards
(`scripts/evaluation/analyze_lfm3_writing_ratings.py`): only rating lines changed in both sheets and the rating files equal the
sheet lines. The owner personally judged three random thinking-on prompts: wr-tr-15 base (exp-019 tied for the AI rater), wr-tr-18
neither (exp-019 answered in English, base was Turkish but wrong), wr-tr-22 exp-019 (the AI rater also preferred it, 5 against 4).

| Mean over 40 prompts | base | arm B | exp-019 |
|---|---|---|---|
| Naturalness, thinking on | 2.38 | n/a | 2.65 |
| Naturalness, thinking off | 2.45 | 2.98 | 3.03 |
| Share rated 4 or 5, on / off | 7.5% / 5% | n/a / 25% | 7.5% / 10% |
| Task score (yes 1, partly .5, no 0), on / off | .56 / .53 | n/a / .40 | .61 / .56 |
| Flagged wrong or invented words per answer, on / off | 2.38 / 2.27 | n/a / 0.42 | 1.40 / 1.07 |

Paired over prompts (exp-019 minus the other, 95% interval): naturalness against base +.275 [.000, +.55] with thinking on and
+.575 [+.325, +.825] with thinking off; against arm B +.05 [-.25, +.375] (a tie); task score against arm B +.163 [+.062, +.25]
(arm B is worse on the task, base against arm B +.125 [+.025, +.225]); flagged words against base -.975 [-1.525, -.425] on and
-1.2 [-1.825, -.575] off. Reading: by an AI rater exp-019 writes somewhat more naturally than the base with fewer wrong words,
but the level is still low (about 3 on a 1 to 5 scale, 7.5 to 10% of answers rated natural, task fully done in 25 to 27% of
answers).

Native check (owner, thinking on, base against exp-019), 27 of the 40 prompts in three parts: 3 prompts drawn at random, 15 more
drawn at random (blind), and the 9 prompts the AI rater had scored as a tie that were not yet judged (a selected group, not random).
- Random 18 prompts: exp-019 preferred on 12, base on 5, neither on 1 (wr-tr-18, exp-019 answered in English); two-sided sign
  test p = .14, a direction only.
- AI-tie 9 prompts: exp-019 7, base 1, neither 1 (wr-tr-21, both wrong); p = .07.
- All 27: exp-019 19, base 6, neither 2 (sign test p = .015, but 9 of the prompts were selected, so this is not a clean test of the
  whole prompt set).

By category (decided prompts, exp-019 against base): explain 5-1, constraint 4-0, email 4-1, creative 2-1, advice 1-1, rewrite 1-1,
summary 1-1, translate 1-0.

The owner's reasons were fine-grained: word choice (ulasin against basvurun), kitapci read as booklet, grammar, order of an advice
answer. Winners were often called "still really bad" or "not acceptable". Against the AI scores: on the 25 prompts with a winner,
the AI rater gave both answers the same naturalness on 16, agreed on 7 and disagreed on 2 (wr-tr-01 and wr-tr-24). So the AI scores point
the same way but separate answers much less finely than a native reader; where the AI rater saw no difference the owner still found
exp-019 better in 7 of 8 decided prompts. 13 prompts remain unjudged by the owner. Preferences:
`results/writing-review-think-on/owner-preferences.json`.

Owner's remarks on likely causes (hypotheses, not tested): emails are weak because the CPT and SFT data had no email or letter
writing (SFT core v01 has no dedicated email category), and science vocabulary (wr-tr-07, seasons) is missing from the CPT.

## Limits

- One training seed per parent; the exp-019 against exp-020 difference includes seed noise of unknown size.
- The 152 diagnostic items and Belebele are development data; the 100-item final test is the clean check and resolves only
  about 8 to 10 points.
- Translations for the final test were AI-produced and reviewed by an AI (not by the owner).
- The merged exp-020 model is not stored locally (the adapter is: `results-local/dl/exp020-adapter.tar.gz`, not in Git).

## Files

`results/gates.json`, `final-test-compare.json`, `final-test-verified-summary.json`, `diag-exp019-minus-exp020.json`,
`eval-v2/`, `guard/`, `belebele-summary.json`, `turblimp-scores.json`, `merge-receipt.json`, `writing/`. Ignored:
`results-local/` (extracted runs, adapter, downloads).
