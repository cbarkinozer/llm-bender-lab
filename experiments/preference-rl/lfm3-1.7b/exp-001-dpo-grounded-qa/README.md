# exp-001-dpo-grounded-qa

## Status

`done` 2026-11-24 (one seed). Design frozen before any result existed. The run reproduces the notebook's recipe and a large gain on
answerable questions; pre-registered rules 1 and 2 could not be met because the baseline already scored above their bar (see Results).

## Goal

A first, hands-on DPO run (a learning experiment): can a small model be taught to answer only from the documents it is given and to
say so when they do not contain the answer? Understanding the mechanics (what the DPO and SFT losses do, what the logged reward
metrics mean, what breaks without the SFT term) matters as much as the numbers.

## Hypothesis

The recipe of the public Liquid notebook, re-implemented here, moves the share of unanswerable questions that get exactly the fallback
sentence from low (the notebook reports about 20% for the original model) to high, on questions from the training domains and on
domains never seen, without making the model refuse questions it could answer.

## Parent Experiment

`exp-000-baseline` (untouched model, same scripts and decoding).

## What Changed

LoRA DPO training on the 4,072 preference pairs of `LiquidAI/grounded-qa`, one epoch. Everything else equals exp-000.

## Base Model

`LiquidAI/LFM3-1.7B`, revision `0dc4268b561499c648c7ba7c9466bf3d8d01517a`, bfloat16, thinking mode off. LoRA is applied to the original
model; the DPO reference is the same model with the adapter off.

## Dataset

`LiquidAI/grounded-qa` (Apache-2.0), revision `eb449523389ebfe24a9255fd7a5a90ead32ad4de`. Each example has two to four short documents
about fictional companies, products and policies, a question in one of 16 languages (no Turkish), and a `chosen` and a `rejected`
answer. About half the questions cannot be answered from the documents. The rejected answers are of three kinds: `hallucination`
(answers an unanswerable question, often after writing the fallback sentence), `refusal` (declines an answerable question) and
`wrong_answer`. Prompts are 1,233 tokens at the median and 2,959 at most. Held-out `test` and `test_unseen` (new domains) are scored by rule.

## Training Setup

| Setting | Value |
|---|---|
| Method | LoRA, sigmoid DPO loss plus SFT loss on the chosen answers (weights 1 and 1) |
| LoRA | r 16, alpha 32, dropout .05, attention, conv and MLP projections |
| beta | 0.1 |
| LR / schedule | 2e-5, cosine, warmup 10% |
| Batch | 2 pairs x 8 accumulation = 16 pairs per step, about 255 steps (one epoch) |
| Max length | 3,072 tokens (one pair is cut) |
| Seed | 42 |
| Libraries | trl 1.16.0, transformers 5.20.2, peft 0.21.2, torch 2.14.1 (the versions the notebook was tested with) |

Why the SFT term: DPO only learns that the chosen answer is better than the rejected one. Here it quickly stops the model from
prefixing answers with the fallback sentence, but it also pushes the model away from the fallback when it should use it. The SFT
loss makes it actually write the chosen answers, including the exact fallback. A DPO-only run (`--sft-weight 0`) is the obvious
follow-up to see this failure ourselves.

### Pre-run checks (playbook sections 7, 8, 21)

| Check | How | State |
|---|---|---|
| Pipeline with a random miniature model on CPU (data, templates, trainer, eval, adapter save) | `run_pref_dpo_grounded_qa.py --tiny-test` | passed 2026-11-24 |
| Sequence lengths and truncation | prompt median 1,233 tokens, max 2,959; 1 of 4,072 pairs exceeds 3,072 (counted in the manifest) | done |
| Trainable parameters, finite gradients on every step, adapter reload (noise <= 20% of the adapter effect) | asserted by the runner | passed |
| Tiny overfit: 32 pairs, 10 epochs, LR 1e-4 must reach reward accuracy of at least .9 | pod stage `dpo-overfit`, stops the campaign when it fails | passed (pod) |
| Baseline | exp-000 | done (pod) |

## Evaluation

As in exp-000: rule-scored, 500 + 300 questions, Wilson 95% intervals, per-question outputs saved. Measured per split:
answerable correct, answerable declined (lower is better), unanswerable exactly-the-fallback, and the two ways to fail an
unanswerable question (`fallback_then_answered`, `answered_without_fallback`). The run also writes the 8 hand-checked showcase
questions with the original and the trained answer side by side.

Pre-registered success rules (differences smaller than the intervals are not claimed):
1. Unanswerable declined correctly, `test`: at least baseline + 30 points and at least 70%.
2. The same on `test_unseen`: at least baseline + 25 points.
3. Answerable correct, both splits: not more than 5 points below the baseline.
4. Answerable declined, both splits: not more than 10 points above the baseline.
5. Run integrity: finite gradients on every step, adapter reload noise within 20% of the adapter effect.

What to watch in the training log (TRL names; the run also records commit, hardware, CUDA stack, precision and attention backend in `results.json`): `rewards/accuracies` (share of pairs where the model now prefers the chosen answer),
`rewards/margins` (how far apart), `logps/chosen` and `logps/rejected` (if the chosen log-probability falls, DPO is pushing both
answers down), `loss`.

## Results

One seed (42), RTX 4090, 255 steps, 42 minutes (2,512 s), train loss 0.54. `rewards/accuracies` went from .36 to about 1.0 by step 40.
All 255 steps had finite gradients. Overfit check (32 pairs) passed. Held-out scores (Wilson 95% in the run's `results.json`):

| Metric | `test` before | after | `test_unseen` before | after |
|---|---|---|---|---|
| Answerable, answered correctly | 4.4% (12/275) | **66.2%** (182/275) | 6.1% (10/165) | **61.2%** (101/165) |
| Answerable, wrongly declined | 90.5% | **10.5%** | 89.1% | **14.5%** |
| Unanswerable, declined with the exact fallback | 92.4% | 91.1% | 94.1% | 91.1% |
| Unanswerable, answered without the fallback | 6.7% | 8.9% | 5.9% | 8.9% |
| Unanswerable, fallback then an answer | 0.9% | 0 | 0 | 0 |

Pre-registered rules: 3 (answerable correct not lower) and 4 (answerable declined not higher) pass by a wide margin. Rules 1 and 2 could
not be passed: they were written for the notebook's baseline (about 20% on unanswerable questions), but under our system prompt the
untouched model refuses almost everything (it declines about 90% of answerable questions), so unanswerable questions were already at
92-94%. The gain is entirely on answerable questions. The small rise in "answered without the fallback" (6.7% to 8.9%, intervals overlap)
is the cost to watch. Rule 5 (integrity) passed after the reload check was redesigned (see Lessons).

Other skills (merged model against the original, one run, differences of a few points are noise): IFEval strict thinking on 84.1% to
84.8%, thinking off (541) 73.0% to 78.4%; HumanEval thinking on 92.7% to 93.3%, off 76.2% to 81.1%; English math 93.8% to 94.1% (one seed);
Turkish math 69.1% to 69.1% (one seed); tool calls English 95.0% to 95.0%, Turkish 82.5% to 87.5% (4 of 80 items); TurBLiMP grammar
71.8% to 71.6%. Belebele did not run (a source file was missing on the pod) and the writing probe was generated but not scored.
No Turkish improvement, as expected: the data is English and has no Turkish content.

## Regressions

None found among the measured skills. Not measured: Belebele, writing quality.

## Lessons

- The exact reload-parity check (trained model against reloaded adapter, bit for bit) fails because of bf16: logits near 20 move in
  steps of 0.125 and a fresh model can pick other kernels. Three attempts failed and are kept on the pod. The check that works compares,
  on real trained answers, the noise (trained against reloaded) with the effect (adapter on against off) and requires noise <= 20% of
  the effect. It measured 1.2% here. A generic probe text is blind to a light adapter, so it must be real trained answers. For merged
  bf16 models the limit is 25% (measured 17%). PEFT loads adapters as fp32, the trainer may leave them bf16, so they are cast to fp32
  before saving.
- A data replication matters more than a recipe replication: this run and exp-003 use the same recipe; only the data differs.

## Conclusion

The notebook's recipe reproduces on our pipeline with a clear, single-seed gain and no measured loss in other skills. exp-003's null
result is therefore about its data (226 mixed, edited pairs, 14 steps), not about the pipeline.

## Next Step

exp-004 (on-policy Turkish pairs, thousands, one signal). A DPO-only control, a seed repeat and Belebele/writing-probe scoring of this
merged model are possible but not needed for that decision.
