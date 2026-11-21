# Exp-015: cookbook recipe

Training passed on 2026-11-20: 40 steps, one epoch over 640 bilingual rows, from
pinned original LiquidAI/LFM3-1.7B. Rank16/alpha32/dropout0.05 LoRA, LR2e-4,
effective batch16, cosine schedule. Smoke, tiny-overfit, finite-gradient checks
and fresh adapter reload parity passed. Training runtime: 57.94 seconds on RTX4090.

This intentionally combines official cookbook recipe settings; it is not a
single-hyperparameter ablation or a reproduction of its larger extraction dataset.
Direct empty thinking prefixes are prompt-masked; existing reasoning is retained.

The prepared config is preserved as the pre-run specification; its preparation
status is historical. Actual run status and hashes are in
`results-local/sft/training-manifest.json`.

Matched development inference: 72 thinking-off and 16 thinking-on prompts.
Seen training probes remain separate; the packet is already consumed development
data. Turkish quality adjudication remains pending. See the shared
[session report](../COOKBOOK-SESSION-RESULTS.md).

Local adapter: `results-local/sft/adapter`. Full model weights are not downloaded.
