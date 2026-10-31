# Native loss-label audit

**Passed for all 78 active training-family candidates using the saved preprocessing implementation and actual token/label arrays.** No model inference or training was performed. This does not establish parity with an unconfigured future trainer.

| Candidate track | Records | Full input tokens | Supervised tokens |
|---|---:|---:|---:|
| Tests | 50 | 91858 | 17266 |
| Planning | 13 | 48852 | 45786 |
| Clarification/integrity | 15 | 3684 | 1833 |
| Total | 78 | 144394 | 64885 |

79509 tokens are ignored by loss. Maximum sequence length is 5328 against a limit of 8192; no truncation occurred. The 95 total candidate count and train/development/holdout roles are unchanged. This audit covers training-family records only, not an approved mixture of all tracks.

## Exact masking policy

The native Qwen3.5 chat template is applied unchanged, thinking enabled, without a generation prompt on completed examples. The complete rendered sequence is tokenized without adding special tokens again, and the resulting IDs are compared with native apply_chat_template tokenization.

Fast-tokenizer character offsets map each token to its native rendered region. A token crossing a masked/supervised boundary is rejected. The system/user messages and their delimiters, assistant role header and final post-EOS newline are masked with -100. The native assistant body is supervised: think markup, supplied authored rationale, final answer and the assistant's im_end end-of-turn token. Reserved role/think markup embedded in content is rejected rather than allowing a false boundary.

Labels are saved unshifted and match input IDs at supervised positions. A later causal-LM loss must perform its normal next-token shift; a collator must not shift the labels again. Both left and right padding are position-masked; tests include pad_token_id equal to eos_token_id so a real end-of-turn label is retained while padding EOS labels stay masked. Dynamic multi-example padding is tested. Packing is disabled. Unsupported multi-turn, tool or multimodal records fail rather than inheriting a possibly wrong mask.

50 test-generation records contain authored rationale. The 13 planning and 15 decision records have no rationale field. Their unchanged native serialization contains an empty think block; no rationale is invented or removed. Thus 28 candidates teach immediate thought closure. These remain separate tracks with planning/reliability training disabled. If mixed once each, planning would contribute about 71% of supervised tokens despite being only 13 rows; choose mixture weights deliberately after baseline evaluation rather than treating row counts as equal training exposure.

## Evidence and negative checks

- `native_tdd_labels.py` is the reusable preprocessing/padding implementation; `model_fields` exposes only input_ids, attention_mask and labels to a future trainer.
- `audit_native_tdd_labels.py` checks every active projection against its corresponding training-family record and verifies exact native rendering/token IDs, decoded assistant-only supervised text, all reasoning/answer/EOS labels, both padding sides and pad==EOS behavior.
- Actual unpadded arrays for all 78 records are saved as `native-label-audit-v01/encoded-labels.jsonl.gz` (162573 bytes), alongside per-record region positions, boundary examples, code/input hashes and environment versions.
- Seven regression tests exercise real native tokenization, empty reasoning, padding, no truncation, reserved markers, unsupported turns, template drift and independent checks of the saved corpus arrays. Deliberate prompt-label leakage, missing reasoning/answer/EOS labels, shifted labels and padding supervision are rejected.
- Local tokenizer.json, tokenizer_config.json, chat_template.jinja and config.json match official Hugging Face metadata for revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`: LFS SHA-256 for tokenizer.json and Git blob hashes for the other three. This closes the prior review's exact-tokenizer-identity uncertainty. Metadata and local SHA-256 hashes are saved in tokenizer-pin-verification.json. No model weights were downloaded.

Per-region token memberships can overlap at BPE boundaries; use supervised_tokens rather than summing region membership counts. Empty reasoning is reported as absent, not as failed rationale supervision.

## Scope of completion

The native-label audit is complete for this processor, tokenizer and exact active input hashes. Record-level historical metadata may still say label auditing was pending at record creation; this separate report supplies the current evidence without editing audited conversation artifacts.

There is no configured trainer. Before a real run, compare its actual first batches with these arrays, including labels after collation and causal shifting behavior. A framework's assistant-only flag is not proof of parity; the saved native template has no generation-span blocks for an automatic assistant mask. Keep packing off unless a separate audit verifies it. Training remains disabled and trainer_label_parity_verified remains false.

Remaining work: semantic near-duplicate review, selecting the experimental capability mixture, freezing a runtime/generation/scoring protocol, and real starting-model inference. No baseline claim follows from a label-mask audit.

## Reproduce

From repository root, with the existing external environment:

```powershell
$env:PYTHONUTF8 = '1'
$env:USE_TORCH = '0' # tokenizer-only work; remove for a future model run
& 'C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/.venv/Scripts/python.exe' -m unittest discover -s scripts/evaluation/tests -p test_native_tdd_labels.py
& 'C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/.venv/Scripts/python.exe' scripts/evaluation/audit_native_tdd_labels.py --tokenizer C:/Users/barkin/Documents/llm-bender-artifacts/tdd-v07-windows/tokenizer --output native-label-audit-v02
```

The audit refuses to overwrite an existing output revision. Tokenizer identity verification reads official metadata over HTTPS. Inspect the existing report/arrays without running a new audit if no inputs or preprocessing changed.
