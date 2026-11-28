# exp-006 DPO on code-checked Turkish pairs (own samples, hard constraints, SFT control on the same answers)

## Status

`running` (rules frozen 2026-11-28 before any training run). Prompts, parent samples (train+dev 8 each, held-out 4) and 4,012 train pairs exist;
nothing has been trained yet. Frozen choices: all 4,012 pairs are used (the 2,500 target is dropped); 700 held-out prompts, 2 seeds; the sweep is
6 DPO runs (beta 0.05/0.1/0.3 x 1/2 epochs) plus 2 SFT controls (the control does not depend on beta); the sweep's dev guard is the anti-hack flags
(mean words within 0.8-1.25 of the matching control, skeleton share <= 5%, not-ended share <= control + 2 points); the full guard suite (rule 4)
runs on the picked configuration in the confirmatory run. Power simulation on dev (300 prompts, 4 samples at T 0.7, parent pass rate 42%):
smallest gain seen with 80% power is 2.7 points at 700 prompts (sampling noise only).

## Goal

Find out whether DPO adds a measurable gain in Turkish constrained, source-grounded answers **beyond plain SFT on the same chosen answers**,
without changing the capabilities guarded in exp-021 (math, tool calling, Belebele, TurBLiMP). The result is published whichever way it goes.

## What exp-005 Taught Us (why this design)

1. SFT on the repaired answers explained most of the gain; the DPO edge over the SFT-only arm was small (59.5%, one seed, AI judge).
2. The pairs shortened answers (34 words against 68), and the judge's criterion order favours short answers. The blind owner read (63%) and the
   AI judge (86%) disagreed, so a judge cannot be the primary metric.
3. After SFT, constraint compliance was already .916, which leaves almost no room to show a gain. The prompts must be harder.
4. A repair model wrote the chosen answers; that is the setup in which SFT matches DPO, and exp-004 showed chosen answers can be wrong.

## Hypothesis

Pairs built only from the parent's own samples, where chosen passes every code check and rejected fails at least one, with matched length,
teach the model to satisfy several constraints at once while staying with the source. DPO on these pairs raises the all-checks pass rate on
unseen passages more than SFT on the chosen answers alone does.

## Parent and Arms

Parent: `cbarkinozer/LFM3-1.7B-Turkish-SFT` (exp-021, commit `6e4f0b7658b115a28da971f82ff4009f63bed612`). All arms start from it.

| Arm | Training |
|---|---|
| `parent` | none (exp-021) |
| `sft-control` | SFT on the chosen answers only, same steps and learning rate as the DPO arm |
| `dpo` | DPO on the pairs, beta and steps chosen on dev by the pick rule |

## Data Design

- **Prompts, three sources**:
  1. The exp-004 pool (3,948 prompts, 8 parent samples each, already on disk). Measured with the code checks only (2026-11-27): 1,959 prompts carry a
     check, 1,058 have both passing and failing samples, **645 have a length-matched pair**. That is below the 1,500-pair minimum, so it is a base,
     not the whole set. (The exp-005 held-out 200 are not reused for the final test.)
  2. Programmatic prompts (`scripts/datasets/tr_dpo6_prompts.py`): a task on a topic, an explain-type question, or a source passage, each with
     2 to 4 stacked countable constraints (word limit, bullet or sentence count, required word, forbidden word, no greeting, no closing question).
     Sources: 424 topics (126 hand-written here, 300 AI-written, `data/topics.jsonl`), 1,185 explain-type questions from
     `AlicanKiraz0/Turkish-CoT-Instruct-Dataset` (Apache-2.0, revision `3473e6c6350564d5a7000faf3ff140e9c4b9d1f2`, questions only; multiple-choice,
     code and calculation questions dropped), and 400 AI-written source passages (`data/passages.jsonl`, grounded: invented-number check on).
     The passages are template-like (repeated genre frames, odd invented names, narrow subjects), so they are at most 15% of the prompts and not
     the main test. Mix topic 60% / question 25% / passage 15%. Wikipedia is not used (the parent read about 100M tokens of it in CPT).
  3. Only if the yield stays below 1,500 pairs: FineWeb-2 Turkish passages from a shard the CPT did not read, minus any URL in the CPT corpus.
  Prompts are split by topic or passage into `train`, `dev` and `held-out`, so no topic or passage appears in two splits.
- **Hard-prompt filter**: sample 8 answers per prompt from the parent (4 at temperature 0.7, 4 at 1.0, repetition penalty 1.1 as in exp-004; changed
  from "all at 1.0" so that passing samples exist); keep prompts where the parent passes 20-80% of the samples. Prompts it always or never passes teach nothing.
- **Code checks** (no model judge in the pair builder or in the primary metric): every stated limit met (words, sentences, bullets, required or
  forbidden words, no greeting, no closing question), every required fact from the source present, no number absent from the source, answer is
  Turkish, answer ends normally. Reuse the exp-005 checks where they exist; add what is missing and test each on hand-made pass and fail cases.
- **Pairs**: chosen = a sample that passes every check; rejected = a sample from the same prompt that fails at least one check. Chosen/rejected
  word ratio between 0.8 and 1.25. At most 2 pairs per prompt. Balanced by the failure type of the rejected answer (no type above 35% of the pairs, reported before and after). On the exp-004 samples one type dominates (500 of 715 pairs are bullet-count failures), and a 25% cap would cut 715 pairs to 160, so the cap is 35% (330 pairs there); the new prompts spread over 9 constraint types, so the real mix is measured after sampling.
- **Size**: target 2,500 pairs (to freeze). If fewer than 1,500 pairs survive, stop and report; do not loosen the checks.

## Training and Dev Sweep

- Library stack as in exp-005 (trl 1.16.0, transformers 5.20.2, peft 0.21.2, torch 2.14.1), LoRA, one pod.
- Dev sweep, at most 6 runs: beta in {0.05, 0.1, 0.3} x length in {1 epoch, 2 epochs} (to freeze), each against its own SFT control.
- **Pick rule (frozen before the sweep)**: highest dev all-checks gain over the matching control among runs that pass the dev anti-hack flags
  and the dev guards; ties go to the larger beta. The sweep result, including the runs where things go wrong, is reported as a figure.
- Exploration uses `dev` prompts only. `held-out` is used once, for the confirmatory run.

## Evaluation (confirmatory run)

- 2 seeds; `parent`, `sft-control` and `dpo` on 600-800 held-out prompts, 4 samples each (temperature 0.7) (to freeze).
- **Primary metric**: per-prompt all-checks pass rate; paired bootstrap over prompts, 95% interval of the difference.
- Secondary: pass rate per constraint type; a blind AI-judge comparison on 400 prompts (reported, never decisive).
- Anti-hack flags on every run: mean words and share of answers below 40% of the parent's median length, distinct 2-gram ratio, longest source
  copy rate, number of invented numbers, KL to the parent. Plus 40 answers read blind by the owner and the AI evaluator.
- Guards (non-inferiority): Turkish and English Belebele, TurBLiMP, the exp-021 math set and tool-calling set, IFEval and HumanEval if exp-021
  ran them; lower bound of the paired difference to the parent above -2 points (list to freeze).

## Pre-registered Success Rules (FROZEN 2026-11-28, before any training run)

1. `dpo` minus `sft-control` on the primary metric at least +3 points, with the lower bound of the 95% interval above 0, in both seeds.
2. `dpo` minus `parent` at least +3 points, lower bound above 0, in both seeds.
3. Length and style: mean words of `dpo` within 0.8-1.25 of `sft-control`; share of skeleton answers (below 40% of the parent's median) at most 5%;
   source copy rate not above `sft-control` by more than 5 points; invented numbers not above `sft-control` by more than 1 per 100 answers.
4. Guards: every guard non-inferior (above).
5. Owner and AI-evaluator blind read of 40 answers: no pattern of reward hacking (templates, number stuffing, source copying, skeleton answers).
6. Run integrity: finite loss on every step, adapter reload exact.

A pass on 1-5 allows publishing `LFM3-1.7B-Turkish-SFT-DPO-Experimental` (the owner approves the exact files). A tie or a miss is written up
as it is, with the pairs published as a dataset; no extra tuning after seeing the held-out result.

## Power (to verify)

About 200 decisive prompts give 80% power for 60% against 50%; for a mean-difference metric the paired variance decides, and the dev set
measures it. Simulate on dev before freezing the held-out size.

## Results

Pending.

## Regressions

Pending.
