# exp010 execution — 2026-10-03

## Training identity

Training completed: 80 reviewed-v2 rows, unchanged 20 development-validation
references, fresh pinned unsloth/Qwen3.5-4B revision
3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636. No old data or historical adapter.
Only training hyperparameter change versus exp009: LR 5e-5 -> 1e-4.
Two epochs, 20 optimizer steps, BF16 LoRA rank/alpha 16/16, effective batch 8,
cosine, warmup 2, seed 3407, final-answer-only loss, no packing/truncation.
Runtime source: 86c69c8. Config hash:
5867ebb02c47fd943ac2e2296aa4218f7a5227fc1e7a54aa1d1dc11e873be328.

RTX 4090 24GB, driver 580.95.05, host c4cb262f2e49,
direct SSH 91.203.49.76:27054. Python 3.11.16, Torch 2.7.1+cu128,
Transformers 5.5.0, Unsloth 2026.9.6, PEFT 0.21.2.
Exact exp009 package freeze reused and compared locally: zero differences.
Venv /workspace/.venvs/exp010-train; caches on /workspace.
CUDA wheel downloaded directly, known SHA256 verified; imports/BF16 passed.
No vLLM installation or inference.

New GPU representation check passed for all tokenized rows and padding labels;
trainable parameters 21,233,664. User explicitly waived repeat smoke/tiny-overfit
for this LR-only test. In-progress smoke and its parent were terminated; partial
logs preserved. Gate marks those checks false/waived, not newly passed. Prior
exp009 evidence referenced. Full run started fresh, not from smoke.

Full training: 20/20 steps, 2 epochs, 89.7461s, mean training loss 1.3649966836.
Both checkpoint-10 and checkpoint-20 saved with optimizer/scheduler/RNG state.
Actual TrainingArguments, CLI and sanitized numerical/env metadata saved.
W&B https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/0d328a15
verified finished through API, 23 history rows retained separately.
Credential taken from local .env through SSH stdin, never logged/copied to files.
Detached launcher removes inherited W&B service variables (prior exp009 fix).

## Inference incident and recovery

Original inference source c815c3f: Unsloth/HF BF16, greedy, repetition penalty
1.05, no extra system prompt, non-thinking, native tokenizer/end-of-turn EOS.
Epoch1 completed eight EOS answers. On me-049 it produced repetitive paragraphs
about the brain's alleged morning sleep cycle, including unsupported claims.
Both 4096 and 8192 attempts hit length limits without EOS (196.76s / 409.14s).
It then retried 16384 tokens, delaying every later prompt and epoch2. This was
not a training crash or inference exception. EOS 248044 corresponded to
tokenizer <|im_end|>; an EOS-ID mismatch was not observed.

Operator stopped the parent and child; third in-flight output was not saved by
the original runner, a telemetry limitation explicitly recorded. Original raw
4096/8192 attempts, eight completed answers, manifest and interruption sidecar
are preserved unchanged in validation-epoch1-v1. The third attempt cannot be
recovered; do not claim it was backed up. Exact cause of the model entering
the loop is not proven; observations do not isolate training from backend/state
or numerical sensitivity.

Recovery source c0d49a0, same adapter/backend/greedy/penalty 1.05. New v2 output
directories: no overwrites. Reuse the eight verified EOS answers by adapter,
validation and input-token identity. Per answer max 4096, no budget escalation;
stop if a 32..512-token block repeats exactly four times or elapsed >180s.
Checks are batch1 generation-level safeguards, not a model repair or scoring
improvement. Any guard/length stop remains native_eos=false, with finish reason
and incomplete IDs. Token-progress snapshots every 128 generated tokens.
Three CPU tests passed for loop detection. Sampling/penalty were not changed.

On restart, me-049 reached EOS at 641 tokens. This is run/order/implementation
sensitivity evidence, not proof the original problem is solved. Stop-policy and
resumed request-order differences are explicit in v2 manifests; do not report
guarded failures as natural successful completions or exact original parity.

Next-run lesson: do not automatically give deterministic repetition increasingly
large budgets. Keep failed attempts, bounded per-item execution and progress
telemetry. Repetition penalty 1.05 reduces token preference, not a guarantee of
EOS or freedom from multi-sentence loops. Do not silently raise it for only one
candidate. Loss reduction and successful optimization are not quality evidence.

## Durable recovery

Local root: C:/Users/cbark/Documents/llm-bender-artifacts/exp-010-lr-ablation.
Training backup downloaded, SHA256 matched and extracted locally:
84703524eff4142209bef3d4397a46b45cefcfaa0f0390e8994bea3ba84e1ac1.
Includes adapters/checkpoints/resume state, effective args, gates/waiver,
setup/download/partial smoke/training logs, exact freeze and dereferenced W&B
files. Source bundles and final inference support backup must also be retained.
Pinned public base weights remain a download dependency; no claim of fully
offline or bitwise-identical reproduction.

Inference/support backup final verification is recorded after both epochs finish.
