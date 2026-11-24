# exp-000-baseline

## Status

`ready`. Design written 2026-11-24, before any run. Scripts pass their CPU pipeline tests (scorer self-check, DPO and GRPO with a tiny
random model); nothing has run on the real model yet. Results are added below after the pod session.

## Goal

Record how the untouched `LiquidAI/LFM3-1.7B` does on the two tasks that the preference-rl experiments train for, so that
exp-001 (DPO) and exp-002 (GRPO) have a baseline that was measured with the same scripts, the same pins and the same decoding.

## Hypothesis

None to confirm. This run measures. Two reference points from the public Liquid notebooks (references, not claims we reproduce):
the original model often writes the fallback sentence and then answers anyway, and declines only about 20% of the unanswerable
questions the way the system prompt asks.

## Parent Experiment

None. This is the first experiment of the `preference-rl` domain. Numbering restarts here; it does not continue the
`turkish-capability` series.

## What Changed

Nothing. No training.

## Base Model

`LiquidAI/LFM3-1.7B`, revision `0dc4268b561499c648c7ba7c9466bf3d8d01517a`, bfloat16, thinking mode off.

## Dataset

Both datasets are Apache-2.0 and pinned by revision (see `config.yaml`).

| Run | Dataset | Test split | Unseen split | What is scored |
|---|---|---|---|---|
| dpo-grounded-qa | `LiquidAI/grounded-qa` | 500 questions | 300 questions from domains never used in training | answer from the given documents, or reply with the fixed fallback sentence |
| grpo-phone-tools | `LiquidAI/phone-assistant-tools` | 499 requests | 300 requests for 10 tools held out of training (5 are lookalikes of training tools) | the model makes exactly the gold tool calls |

Neither dataset has Turkish (16 languages: ar, de, en, es, fr, hi, id, it, ja, ko, pl, pt, ru, th, vi, zh). A Turkish check is a later
experiment.

## Training Setup

None.

## Evaluation

- **Grounded QA** (greedy, `repetition_penalty` 1.1, 256 new tokens): answerable questions are correct when the answer contains the gold
  answer and not the fallback sentence; we also count how often the model declines them (lower is better). Unanswerable questions are
  correct when the answer is exactly the fallback sentence. Two failure kinds are counted separately for unanswerable questions: the
  fallback followed by an answer anyway (`fallback_then_answered`) and an answer without the fallback (`answered_without_fallback`).
- **Phone tools** (greedy, 512 new tokens, prompt about 8,100 tokens with all 108 tools): exact match of the calls in any order, with
  arguments compared by kind (`scripts/evaluation/phone_tools_scoring.py`; checked on all 3,307 gold rows and by a render-parse round
  trip). Reported overall and per category (`single`, `multi`, `lookalike`, `no_tool`, `clarify`, `partial`).
- All rates come with Wilson 95% intervals. Outputs of every question are kept in `results/`.

The scorer is a re-implementation from the dataset's description, and the subsets are full splits, so the numbers can differ from the
ones in the public notebooks (which score 200 questions per split). Compare our runs with each other, not with Liquid's numbers.

## Results

Pending.

## Regressions

Not applicable.

## Conclusion

Pending.

## Next Step

exp-001 (DPO) and exp-002 (GRPO), both scored against these numbers.

Noted 2026-11-24 for the later Turkish experiments: [`vngrs/Kumru-2B`](https://huggingface.co/vngrs/Kumru-2B) (a Turkish-from-scratch 2B instruct model, Apache-2.0
per its card) is the owner's chosen comparison point for Turkish output accuracy. Neither dataset here has Turkish, so it does not enter exp-000 to exp-002.
