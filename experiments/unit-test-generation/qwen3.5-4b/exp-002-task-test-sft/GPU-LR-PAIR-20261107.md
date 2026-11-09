# Thinking-SFT learning-rate pair: results, 2026-11-07

**Both new runs completed; all required GPU artifacts are downloaded and verified.
The GPU is safe to close. No local commit or push was made.**

The lower-learning-rate pair did not improve the primary execution metric. Base,
original A@1e-4 rerun, Exp3@1e-5 and Exp4@3e-5 each have **0/5 complete
reference-passing suites and 0/10 gated targeted-fault kills**. This is a
five-task, one-family, one-seed adaptive-development diagnostic, not evidence
that fine-tuning thinking cannot work or that memorization caused the failures.
The new five-case review is complete: base first on two cases, Exp3 on two, Exp4 on one; none retained. See gpu-lr-results-20261107/completed-review-20261109.md. Experiment paused by owner on 2026-11-09; see PAUSED-20261109.md. Old submitted reviews remain unchanged.

## What ran

The owner clarified that the goal is to fine-tune thinking. BOTH new runs use
**A-style rationale-plus-answer loss**, not the earlier proposed B masking.
The actual training arrays are byte-identical to original A:50rows,91,858input
and17,266supervised tokens/epoch. Each fresh run used pinned original
`Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

Only peak learning rate differs within the pair: Exp3=1e-5, Exp4=3e-5. Both use
3epochs/21updates, BF16 unquantized LoRA rank/alpha16/dropout0, batch1/accum8,
seed3407, AdamW8bit, cosine/warmup2, max training sequence3072, no packing or
truncation. Data includes concise authored reasoning, not recorded internal
reasoning traces or implementation source. No planning/integrity rows were
added to these50training examples.

`lr-pair-preflight-v01/{Exp3,Exp4}` freezes recipes, actual labels, manifests and
nine revised development requests. `protocol.json` fixes execution as the primary
diagnostic; inherited recipe prose mentioning joint blinded evidence is retained
as provenance. Complete-suite reference passing is mandatory for mutant credit.
Raw failing assertions are not deleted or rewritten to rescue scores.

The earlier alleged literal-backslash defect was incorrect: AST-decoded
language-basic strings contain actual newline/tab characters. Training data was
not repaired or changed on that basis.

## Evaluation and provenance

Public API return shapes, placeholder grammar, filename policies, mutable values
and undo/revert semantics were clarified prospectively before this baseline.
No implementation or reference test code was added to generation prompts. These
contracts were informed by earlier development failures, so this is **adaptive
development, not fresh held-out evaluation**. No holdout inference or tuning ran.
Public-repository pretraining exposure remains unknown.

All four evaluated models used the same clarified nine requests and frozen
vLLM0.30.0/Torch2.13.0/Transformers5.18.0/tokenizers0.23.3 inference environment:
BF16, native thinking enabled, greedy temperature0, repetition penalty1.15,
8192output/9216context, batch1, seed3407, chunked prefill and text-only mode.
Native stop IDs were derived and checked against the pinned tokenizer.
Exact actual prompt text and token IDs match across all four models for all nine
requests; the largest prompt is715tokens. See `prompt-parity.json`.
Original A's saved adapter was rerun on these prompts; its old scores were not
reused. This is additional inference, not a third new training experiment.

Hardware: one RTX4090 24GB, driver580.159.03. Training stack retains
Torch2.7.1+cu128, Transformers5.5.0, Unsloth2026.9.6/Zoo2026.9.5,
Accelerate1.10.1. Original A training used a different driver, so cross-session
historical comparisons retain that numerical caveat. Greedy is not promised
bitwise reproducible across hardware/backends.

Local protected Docker image `tdd-posting:lr-v01` resolved to
`sha256:bb1d1fe4c828ce7dd96c819c483678edf02f28686afb5d73c0f1b88f7f45b606`.
Its Python base was pinned to
`python@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc`.
Authored controls pass5/5 and kill10/10faults. Generated tests ran only in the
network-disabled, read-only, resource-limited Docker executor, never on host or
GPU pod. Curated faults are incomplete and correlated.

## Observed outcomes

| Model | Complete parseable format /5 | Native EOS /9 | Length hits /9 | Reference passes /5 | Gated kills /10 | All-request output tokens |
|---|---:|---:|---:|---:|---:|---:|
| Base |2|8|1|0|0|43,116|
| Original A,1e-4 rerun |3|8|1|0|0|14,569|
| Exp3,1e-5 |3|8|1|0|0|44,326|
| Exp4,3e-5 |5|9|0|0|0|24,934|

Exp4 improves format/completion but has incorrect expectations and fake-helper
calls. Examples verified in protected logs: expecting non-ASCII placeholder
names despite the ASCII grammar; expecting two encoded dollars to become only
two escaped dollars; undoing three edits but expecting the third undo to be
unavailable; and confusing undo's returned variable name with its value.
Exp3 still uses brace placeholders in many tests and expects undo of a revert
to leave the restored key absent. Partial passing cases are retained in
`summary.json` as secondary diagnostics; they earn no complete-suite/fault credit.

Base and Exp3 each hit8192 on query test generation after thinking had closed,
while enumerating oversized test catalogues. No short periodic suffix flag was
found for either. Original A's revised-prompt history response has a **confirmed
answer loop**, repeating `assert sv.undo() is None`1004times until8192. This is
new rerun evidence, not a revision to the first pair's original termination
report. Exp4 has9native stops and no suffix-loop flag; lack of that heuristic
flag is not proof against every possible degeneration.

Upstream screening against30pinned Posting test files found no flags among
4base,4Exp3,5Exp4 and3historical-A complete code files. Exact normalized function
AST and8-token-shingle screening cannot rule out pretraining contamination.
Paper taxonomy smell/oracle scans are static, unvalidated diagnostics. Necessary
state calls and requirement constants can be justified; specific assertions can
still be wrong. No automatic smell/strength score is treated as a quality win,
independent human label, or human-machine agreement statistic.

## Training checks and W&B

Both arms passed separate smoke, tiny-overfit and vLLM adapter-reload gates.
Actual microbatch audits verify150microbatches, each row3times, identical order,
275,574input tokens and51,798supervised tokens per run. Every accumulation-group
token denominator, actual batch labels, runtime learning rate, precision and
optimizer/scheduler arguments were verified. Final checkpoints were preselected.

- Exp3: training135.7701s; loss1.148814; peak allocated20,728,508,416bytes.
- Exp4: training136.1100s; loss1.086813; peak allocated20,728,508,416bytes.

Losses alone do not establish better generated tests. Training losses across the
old rationale-masked B objective are not directly comparable.

W&B project: https://forge.coreweave.com/wandb/c-barkinozer/llm-bender-unit-test-generation

- Exp3 live run:`gxpa379x`; Exp4 live run:`2py34p5k`.
- Original A/B metrics were backfilled as explicitly retrospective runs
  `tdd-20261107-original-a` and `tdd-20261107-original-b` from saved log history.
  Missing system/time-series telemetry was not reconstructed.
- New evaluation is separately namespaced `eval/lr_v01`; original scores were not
  overwritten. Base eval run:`tdd-20261107-lr-v01-base`. Original B was not rerun
  on this revised evaluation.

Local validation:13focused tests pass, including LR/mask preservation and actual
runtime-LR mismatch rejection. The normalization module also passes in the pinned
remote stack. An earlier local default Python3.13 run had10passes/1failure due
missing Accelerate; no local dependency upgrade was made to hide it.

## Anonymous review

New Argilla dataset (five records, four anonymous candidates each):
http://127.0.0.1:7900/dataset/b58d58a3-c200-428a-a117-eb8f374f9910/annotation-mode

W/X/Y/Z are randomized per case; thinking, identities and machine scores are not
uploaded. Rank with ties, retain/repair/reject/uncertain, and code evidence. No
169-site human annotation or1-5 assertion rating is required. Existing primary
review remains5/5submitted; new review was0/5at publication. Reviewers should
record AI assistance and prior exposure; this is not a double-blind claim.

Downloads:`tdd-thinking-lr-blind-five-cases-20261107.txt` is reviewer-safe.
Artifact `blind-review-only-v01.zip` contains only reviewer files; PRIVATE mapping
and diagnostics stay outside that folder. Do not send the full artifact archive
to a grader who should remain blinded. Four supporting probes are separate and
optional; their existence is not evidence that planning was trained.

## Recovery and Git state

Local artifact root:
`C:/Users/barkin/Documents/llm-bender-artifacts/tdd-lr-pair-20261107`.
All adapters, exact input/output IDs, trainer state/arguments, exposure/loss audits,
setup/runtime locks, training/inference/pytest logs, source snapshots, W&B files
and review material are retained. Public8GBbase weights are not bundled; load
the exact revision above rather than relying on adapter_config's null revision.

Main backup:`tdd-lr-pair-v01-all.tar.gz`,590,930,622bytes, SHA256
`766e382350cbe4ce135b1f88770fd490c09cf05bd45b410d880c5ba0bdfe9a75`.
All344regular manifest files verified. An additional checksummed archive captures
11dereferenced W&B log-file symlinks; only three convenience latest-run directory
links remain unmaterialized on Windows, with their actual run folders retained.
Both new84,972,248byteadapter files verify and have different SHA256s. The primary
and supplemental credential scans pass. See `backup-verification.json`.
A dropped download connection was resumed successfully; neither a partial file nor
mere existence of an archive was accepted as completion. Final GPU check shows
1MiB allocated/0%utilization. No pod termination was performed by the agent.

Local changes remain **uncommitted/unpushed**, respecting the owner's instruction.
A separate temporary remote Git snapshot records executed source:
`b4adb49f5be8da362c47e57663995f877c56ac88`, then
`55e1dd91f93736cfad1383763b647b63a9d89b9e` adds only historical evaluation preflight.
Local parent remains47fbb78. Final local source recovery bundle and Downloads
Claude handoff preserve the uncommitted continuation state.

## Decision

The tested lower rates did not resolve complete-suite usefulness. The evidence
supports format/completion changes, not a claim of better reasoning, proven
memorization, or an optimal learning rate. Follow the predeclared stop rule for
this LR sweep. Next work is the five-case anonymous review and a training-family
revision focused on deriving justified oracles and checking them before output;
no development repair answers enter training. No further GPU run is requested.
