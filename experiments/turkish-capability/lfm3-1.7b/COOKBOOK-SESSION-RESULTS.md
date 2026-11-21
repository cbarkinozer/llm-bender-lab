# Cookbook-aligned SFT session, 2026-11-20

Both independent original-base LoRA runs passed smoke, tiny-overfit, finite
gradient and exact adapter reload checks. Exp014 ran69 steps (83.28s training);
exp015 ran40 steps (57.94s training). These times exclude setup and inference.

264 matched development answers: each model answered72 thinking-off prompts
and16 thinking-on prompts. vLLM BF16, batch4, temperature0.1, top-k50,
repetition penalty1.1, max4096 new tokens, context8192, seed3407.

| Model | Symbolic correct, off | Symbolic correct, on | Length hits, off/on | Thinking closure, on |
|---|---:|---:|---:|---:|
| Original base | 8/8 | 8/8 | 0/1 | 16/16 |
| Exp014 | 2/8 | 8/8 | 0/0 | 16/16 |
| Exp015 | 1/8 | 8/8 | 1/0 | 8/16 |

Symbolic answers were inspected directly, separating correctness from number-only
formatting. This small slice shows recovery with thinking, not general arithmetic
preservation. Exp015 never closes thinking on the eight Turkish arithmetic word
problems; all eight symbolic controls close correctly. Exp014 closes all16 but
still makes Turkish calculation and language errors. No Turkish quality winner
or publication-ready model is established.

Median generated tokens, off/on: base145.5/272.5, exp01447.5/57.5,
exp01552/68. EOS counts, off/on: base72/15, exp01472/16, exp01571/16.
EOS does not imply semantic correctness or valid thinking markup.

## Interpretation limits

- Exp014 also changes the TRL framework and uses left padding compared with the
  historical custom Trainer; it is not a pure masking-only causal test.
- Exp015 intentionally combines cookbook recipe changes. Our640 bilingual rows
  do not reproduce the official example's6000-row extraction task.
- Empty thinking prefixes are prompt-masked; existing reasoning stays supervised.
  Actual collator masking checks covered all640 source rows.
- Packets are consumed development data. Keep12 seen training probes in the off
  packet separate from unseen tasks. None is a fresh final holdout.
- Eight symbolic controls cannot establish Turkish gains. Turkish correctness,
  naturalness and instruction following still require adjudication.

## Artifacts and next action

Adapters: each experiment's `results-local/sft/adapter`. The ignored local runtime
and result folders retain logs, manifests, optimizer state and answers. Full base
and merged weights are excluded. Backup verification is recorded in
`cookbook-runtime-local/LOCAL-BACKUP-RECEIPT.json` when download completes.

Run `python scripts/evaluation/summarize_lfm3_stage_diagnostic.py --cookbook`
after download for diagnostics and a correctness-review CSV. Next: blind review
base/exp014/exp015 Turkish outputs, retaining mode and task distinctions. Do not
launch further training solely from symbolic scores or training loss.
