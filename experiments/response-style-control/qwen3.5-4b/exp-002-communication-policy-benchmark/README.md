# exp-002 — Communication Policy Benchmark

This benchmark evaluates whether fine-tuning changes Qwen3.5-4B's response
policy while preserving its existing Turkish comprehension and instruction
following. It is not a Turkish-language benchmark and it is not an SFT source.

## Target policy

The desired assistant is concise, direct, emotionally neutral, and
non-anthropomorphic:

- begin with the answer, decision, constraint, or necessary clarification;
- omit praise, reassurance, apology, emotional mirroring, and conversational
  wrap-up;
- make a factual feasibility judgment when the prompt warrants one;
- state uncertainty or limits plainly instead of using hedged social language;
- give enough reasoning or concrete next actions to complete an open-ended
  task; do not become terse by default.

Neutrality does **not** mean refusing to judge. For example, an infeasible
idea should be called infeasible and the relevant constraints should be named.

## Isolation contract

- Every item must be written independently of `exp-001-sft-dataset`.
- Do not reuse, paraphrase, translate, or derive an SFT prompt/target.
- Never add benchmark prompts or reference answers to later SFT or preference
  data.
- Keep `test.csv` sealed during prompt/data iteration. Use `development.csv`
  only for routine comparisons.
- A benchmark item may be edited before its first scored run. After that, make
  a new version instead of silently changing it.

## Files

- `item-schema.csv` — required columns and one non-evaluable schema example.
- `development.csv` — reserved for a future iterative recipe; currently header-only.
- `test.csv` — frozen final held-out set of 100 original Turkish prompts.
- `scoring-rubric.md` — blind-scoring protocol and pass criteria.
- `item-authoring-guide.md` — use-case families and authoring rules.

## Split plan

| Split | Purpose | Recommended size | Use policy |
| --- | --- | ---: | --- |
| `development` | Diagnose the base model and compare candidate checkpoints | 24–40 | May be run repeatedly; never train on it |
| `test` | Final claim for the chosen checkpoint | 80–120 | Keep sealed until model/checkpoint selection is frozen |

The current user-authored examples—life purpose, university choice, and the
horse-Tinder proposal—were authored after the SFT dataset was frozen. They
remain test-only. This recipe must not change data, hyperparameters, or
checkpoint selection based on their results; otherwise this benchmark becomes
development data and a fresh final holdout is required.

## Evaluation unit

For every item, save the raw output from the base model and the fine-tuned
candidate under exactly the same generation protocol. A human scorer sees
anonymized output labels rather than model names, then applies the rubric.
The primary claim is a blind, paired improvement in communication-policy score
without a drop in task-completion score. Correctness and safety are hard gates:
a stylistically improved answer cannot pass if it is factually wrong or gives
unsafe advice.
