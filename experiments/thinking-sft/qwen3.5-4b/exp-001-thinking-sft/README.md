# exp-001 — Occam 2 Turkish reasoning SFT

Status: 80/20 authored draft and native-label preparation complete; actual 4B
training and held-out baseline have not run. No improvement result exists.

Preparation evidence: [representation summary](representation-summary.json),
[model scope](model-scope.json), [historical lexical audit](data-v1/historical-overlap-report.json).
All 80 native training targets passed exact decoded-label checks: maximum 240
tokens per full example, zero truncation, 2,809 reasoning tokens and 1,093 final
answer tokens (4,462 total supervised including delimiters/turn termination).
Nine offline tests pass, including arithmetic/time checks, real-template masks,
EOS padding, missing-review-score refusal, and tiny hybrid-model LoRA gradients.
The portable Colab ZIP also passed the same tests after extraction.

Hypothesis: supervising checked Turkish worked reasoning and concise final
answers improves correctness on unseen Turkish source-contained tasks at the
same thinking-enabled inference budget.

Use [experiment-config.json](../experiment-config.json),
[data-v1](data-v1/README.md), and [execution instructions](../RUN.md).
The single proposed recipe is fresh-base BF16 LoRA, rank/alpha16, LR1e-4,
effective batch8, 30 updates / three nominal epochs, final checkpoint preselected.
Native labels supervise reasoning, final answer and end-of-turn. Packing is off.

Framework decision: use Transformers/PEFT with explicit audited labels for this
small pilot. Unsloth's family guide informs BF16/LoRA and architecture support;
its vision collator and generic response-masking shortcuts are not needed here.
This is a deliberate implementation choice, not a claim of equivalent speed.

Model inspection found 128 eligible text-only linear projections: 32 each of
gate/up/down and eight each of q/k/v/o. Qwen3.5 is hybrid: the 24 linear-attention
blocks use different projection names and are not adapted by this first recipe.
Their MLPs are adapted. Vision, embeddings and output head stay frozen.

A tiny randomly initialized, two-layer hybrid Qwen3.5 CPU model produced finite
masked loss and nonzero LoRA gradients with this collator. That is an integration
check; it does not replace CUDA 4B smoke, tiny-learning, save/reload, or baseline checks.

Next: review the draft and development-probe evidence, prepare a compatible GPU
environment, record frozen base thinking-on outputs, run training diagnostics,
then one fresh full run and the matched candidate evaluation.
