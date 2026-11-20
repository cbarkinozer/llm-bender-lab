# Native prompt/completion SFT preparation, 2026-11-20

Status: CPU preparation complete; no GPU accessed, no training performed.
GPU TRL integration, actual batch-mask audit, smoke and tiny-overfit remain
pending. Config files are specifications, not executable training runners.

## Correction to the earlier interpretation

The owner intended absent reasoning to remain absent. This was NOT an
instruction to train the model to emit empty thinking. The earlier assistant
claim that this output policy was an intentional owner decision was incorrect.
Historical targets nevertheless supervised `<think></think>` on direct rows.
Historical native-template equality checks passed: the issue under investigation
is the loss boundary, not a claim that the old template text was invalid.

The native template still renders empty thinking in non-reasoning mode. The
cookbook-style generation prompt already contains it, so completion-only loss
should exclude it. Real reasoning is retained, with thinking enabled per row.
The opening `<think>` belongs to that row's prompt; reasoning and its closing
tag remain supervised. This mixed-mode policy intentionally differs from the
official extraction notebook's entirely non-reasoning task.

## CPU evidence

`prepare_lfm3_cookbook_sft.py` reads the frozen corrected 640 rows and the
previously pinned native template. It does not edit the source dataset.
All 640 rendered sequences have identical text to the old rendering. All new
generation prompts are exact token prefixes of their corresponding sequences.

- 520 direct rows: supervised completion is answer plus end-of-turn only.
- 120 reasoning rows: original reasoning and answer preserved; no invented
  reasoning and no empty thought supervision on direct rows.
- One-pass target tokens: 146,282 before, 145,122 after.
- Maximum full sequence: 1,602 tokens; no truncation.

`audit.json` stores every decoded target and prompt suffix. CPU rendering uses
the original Jinja template with generation-tracking block delimiters removed;
the output logic is unchanged. The local Transformers installation cannot
import because its tokenizers dependency range conflicts with the installed
version. No shared environment was modified. Independent AutoTokenizer and
actual TRL mask verification therefore remain mandatory on the GPU environment.

This establishes a training-policy difference, NOT its causal responsibility
for arithmetic failures. Empty-prefix supervision and arithmetic regression
must not be equated without the controlled experiment.

## Two prepared experiments

1. `exp-014-completion-mask`: original base, same data, rank32/alpha64,
   dropout0, LR1e-4, effective batch8. Compare step69 against exp-012 step69.
   Preserve the first552 original ordered row exposures and the original
   113-step cosine scheduler horizon; stopping at69 must not compress the
   schedule. Primary variable: loss boundary/mode-aware prompt construction.
2. `exp-015-cookbook-recipe`: original base, same data, rank16/alpha32,
   dropout0.05, LR2e-4, effective batch16, one epoch (40 steps), cosine,
   warmup_steps=0.05 under the notebook's pinned TRL API. This is a combined
   recipe trial, not evidence isolating any individual hyperparameter.

Neither increases data count or adds arithmetic examples. Source task content,
source acceptance and existing exclusions remain unchanged. No consumed
evaluation prompts or references enter training.

## Tomorrow's execution checklist

- Obtain a fresh pod endpoint; old pod may close. Reuse the existing SSH key.
- Read `docs/environment-setup-gotchas.md`; use a separate pinned environment.
- Notebook pins: torch2.14.1, torchvision0.29.1, torchao0.18.0, trl1.16.0,
  transformers5.20.2, peft0.21.2, accelerate1.15.0, datasets5.1.0,
  huggingface-hub2.3.0, tokenizers0.23.3, safetensors0.8.0.
- Implement TRL runners for these specifications before full training.
  Set completion_only_loss=True explicitly. Verify per-row template kwargs
  and reasoning fields survive preprocessing; never silently drop reasoning.
- Independently compare AutoTokenizer outputs to every CPU audit row.
- Inspect actual TRL input_ids/labels for all640 rows: prompt and padding
  masked, direct empty prefix masked, real reasoning and EOT supervised,
  no truncation. Archive decoded supervised spans and token totals.
- For exp014 preserve original data order, AdamW settings and scheduler
  horizon; verify actual first batch. Record any framework-default mismatch
  rather than calling a confounded run a pure mask ablation.
- Finite-loss/gradient smoke and adapter reload; train-only tiny overfit.
- Train only after those checks pass. Save adapter, losses, effective args,
  runtime versions, hashes and sample masks. Do not download full weights.
- Reuse the consumed stage packet as development/regression evidence with
  exactly matched inference settings. Evaluate English/Turkish, arithmetic,
  stopping and thinking modes separately; exclude seen probes from general
  accuracy. Compare exp014 to exp012 and exp015 to untouched base.
- Fresh final holdout only after selecting a candidate. No publication implied.

## Reference and scope

Local notebook: `C:/Users/cbark/Downloads/lfm3_sft_with_trl.ipynb`.
Upstream: https://github.com/Liquid4All/cookbook/blob/main/finetuning/notebooks/lfm3_sft_with_trl.ipynb

The notebook performs multilingual structured extraction, not general language
teaching. Its dataset currently has6000 training rows,500 test,300 unseen-test
and6 showcase rows; the notebook evaluates200 examples per test split.
We do not duplicate existing rows to imitate that count. Different task/data
scale and the preserved reasoning subset limit direct recipe transfer.
