# exp-002-grpo-phone-tools

## Status

`planned`. Design written 2026-11-24, before any result of this run existed. The runner passes its CPU pipeline test with a tiny
random model. It becomes `ready` after a 5-step smoke test on the real model has measured seconds per step and peak GPU memory, which
decides whether the full 150-step run fits an affordable session on a 24 GB GPU.

## Goal

A first, hands-on GRPO run (a learning experiment): improve tool calling with reinforcement learning against a rule-based reward, with
no preference pairs and no judge model. Understand what GRPO does (a group of answers per request, advantage = reward minus the group
mean, KL penalty towards the original model) and what its logs mean.

## Hypothesis

150 GRPO steps raise the exact-match rate on requests for tools seen in training (`test`), and part of that gain carries over to
requests for 10 held-out tools (`test_unseen`), without the model learning to always call a tool (the `no_tool` and `clarify`
categories must not collapse).

## Parent Experiment

`exp-000-baseline`.

## What Changed

LoRA GRPO training on the 2,500 training requests (the 375 requests that need no tool call, `no_tool` and `clarify`, are shown twice,
because without that RL learns that always calling a tool pays). Everything else equals exp-000.

## Base Model

`LiquidAI/LFM3-1.7B`, revision `0dc4268b561499c648c7ba7c9466bf3d8d01517a`, bfloat16, thinking mode off. LoRA on the original model; the
KL reference is the same model with the adapter off.

## Dataset

`LiquidAI/phone-assistant-tools` (Apache-2.0), revision `02100f57ab94eda248909b83a79e9d46a590d038`. A request with the phone's date,
time and locale, in 16 languages (no Turkish), and the gold calls. Every prompt carries all 108 tool schemas (about 8,100 tokens).
Categories: `single`, `multi` (several calls), `lookalike` (a tool that resembles another), `no_tool` (answer directly), `clarify`
(ask for a missing detail), `partial` (do what is possible and say what is not). `test_unseen` asks for 10 tools never right in
training; five are lookalikes of training tools.

## Training Setup

| Setting | Value |
|---|---|
| Method | LoRA GRPO, rule-based reward, transformers generation (no vLLM) |
| Reward | 1.0 for exactly the gold calls (for no-call requests: no call); otherwise 0.2 x F1 of the tool names |
| Group | 8 answers per request, 4 requests and 32 answers per optimizer step |
| Steps | 150 (the notebook's default; its text says 200 steps reach about 80% on training tools and 76% on held-out tools) |
| Completion length / temperature | 256 tokens / 1.0 |
| LR / schedule | 1e-5, constant after 5 warmup steps |
| KL penalty beta | 0.04 |
| LoRA | r 32, alpha 64, dropout 0, attention, conv and MLP projections |
| Seed | 42 |
| Libraries | trl 1.16.0, transformers 5.20.2, peft 0.21.2, torch 2.14.1 |

The cost is the open question. Each prompt is about 8,100 tokens, each step generates 32 answers and trains on 32 sequences of about
8,300 tokens. A rough estimate is 1 to 3 minutes per step, so 3 to 7 hours for 150 steps; the smoke test replaces this estimate with a
measurement before we spend it.

### Pre-run checks (playbook sections 7, 8, 21)

| Check | How | State |
|---|---|---|
| Pipeline with a random miniature model on CPU (prompts, parser, reward function, trainer, eval, adapter save) | `run_pref_grpo_phone_tools.py --tiny-test` (short tool list) | passed 2026-11-24 |
| Scorer correct on all gold rows and on the chat template round trip | `scripts/evaluation/check_phone_tools_scoring.py` | passed (3,307 gold rows, 2,786 round trips, 28 comparator cases) |
| Smoke test on the real model: 5 steps, speed and peak memory | pod stage `grpo-smoke` | pending (pod) |
| Tiny RL overfit: the same 4 requests for 12 steps, the mean reward must rise by at least .05 | pod stage `grpo-overfit` | pending (pod) |
| Baseline | exp-000 | pending (pod) |

## Evaluation

As in exp-000: `test` (499) and `test_unseen` (300), exact match with the scorer in `scripts/evaluation/phone_tools_scoring.py`,
overall and per category, Wilson 95% intervals, every output kept. The run also writes the 8 hand-checked showcase requests with the
original and the trained calls side by side. Parse failures (completions whose tool-call text cannot be read) count as no call and are
counted separately.

Pre-registered success rules (differences smaller than the intervals are not claimed):
1. Exact match on `test`: at least baseline + 10 points.
2. Exact match on `test_unseen`: higher than the baseline (any gain larger than its interval).
3. `no_tool` and `clarify`, both splits: each not more than 5 points below the baseline.
4. Run integrity: finite gradients on every step, adapter reload exact.

What to watch in the training log: mean `reward` (1.0 means every answer in the batch is exactly right), `reward_std` and `frac_reward_zero_std` (a group whose
answers all get the same reward teaches nothing, so the zero-std share should not be near 1), `completions/mean_length`,
`kl` (distance from the original model), `step_time` (seconds per step).

## Results

Pending.

## Regressions

Pending.

## Conclusion

Pending.

## Next Step

If it works: a longer run (the notebook says accuracy keeps improving), a seed repeat, GRPO on the MoE model, and a Turkish tool-calling
check using our own Turkish tool-call evaluation items.
