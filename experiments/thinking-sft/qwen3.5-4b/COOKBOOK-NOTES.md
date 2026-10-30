# Thinking SFT cookbook research — 2026-10-28

## Sources inspected

- [Unsloth Qwen3.5 guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune):
  model-family SFT support and BF16 LoRA starting point. The guide currently
  discourages QLoRA for this family. Treat hardware estimates as estimates.
- [Qwen3 thinking SFT notebook](https://github.com/unslothai/notebooks/blob/bf2a56f80670e9290456054f1c318f26f3db45a1/nb/Qwen3_(4B)-Thinking.ipynb):
  reasoning-data formatting and response-only masking example. It uses
  `Qwen3-4B-Thinking-2507`, not Qwen3.5; architecture/loading and inference defaults
  must not be transplanted blindly.
- [Qwen3.5 4B vision notebook](https://github.com/unslothai/notebooks/blob/bf2a56f80670e9290456054f1c318f26f3db45a1/nb/Qwen3_5_(4B)_Vision.ipynb):
  family-specific alternative; this experiment is text-only.
- [TRL SFT documentation](https://huggingface.co/docs/trl/sft_trainer):
  completion-only loss and reasoning-completion examples. Assistant-only masking
  depends on the template's generation markers; never assume it works merely
  because a configuration flag was set.
- [Qwen model card](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a):
  official checkpoint selected for this pilot. Resolved Hub main to this revision.
- [Pinned native template](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/chat_template.jinja).

## Representation findings

The inspected native template consumes assistant `reasoning_content` separately
from final `content`. In a single-user/single-assistant training example, it emits
the reasoning block followed by the answer and `<|im_end|>`. Its generation
prefix with `enable_thinking=True` ends inside the opening thinking block.
Historical assistant reasoning may be omitted in multi-turn conversations, so
this pilot uses single-turn examples and validates rendered targets explicitly.

Training and inference prefixes need separate checks: masking everything through
an inference prefix can accidentally exclude the opening reasoning tokens.
Prefer audited pretokenized labels or a verified response-only collator over an
unchecked template/masking shortcut. Preserve EOS labels even if padding uses
the same token ID; mask padding by position, not by token value alone.

## Scope

No external teacher API has been called and no paid compute started. Authored
worked solutions will carry assistant-authored synthetic provenance and require
answer checks. No blanket claim of dataset accuracy or improvement is justified
until those checks and the before/after run are complete.
