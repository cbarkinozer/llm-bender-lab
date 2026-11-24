# exp-001-dpo-grounded-qa

## Status

`ready`. Design frozen 2026-11-24, before any result of this run existed. The runner passes its CPU pipeline test with a tiny random
model; the real run is pending a GPU session.

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
| Trainable parameters, finite gradients on every step, adapter reload exact | asserted by the runner | in the run |
| Tiny overfit: 32 pairs, 10 epochs, LR 1e-4 must reach reward accuracy of at least .9 | pod stage `dpo-overfit`, stops the campaign when it fails | pending (pod) |
| Baseline | exp-000 | pending (pod) |

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
5. Run integrity: finite gradients on every step, adapter reload exact.

What to watch in the training log (TRL names; the run also records commit, hardware, CUDA stack, precision and attention backend in `results.json`): `rewards/accuracies` (share of pairs where the model now prefers the chosen answer),
`rewards/margins` (how far apart), `logps/chosen` and `logps/rejected` (if the chosen log-probability falls, DPO is pushing both
answers down), `loss`.

## Results

Pending.

## Regressions

Pending.

## Conclusion

Pending.

## Next Step

If it works: a DPO-only control, a seed repeat, and later a Turkish version built from our own verified and wrong answers.
