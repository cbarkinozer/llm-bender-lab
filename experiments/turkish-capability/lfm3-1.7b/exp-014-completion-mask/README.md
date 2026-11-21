# Exp-014: completion masking

Training passed on 2026-11-20: 69 steps from pinned original LiquidAI/LFM3-1.7B,
independent rank32 LoRA, LR1e-4. Smoke, tiny-overfit, finite-gradient checks and
fresh adapter reload parity passed. Training runtime: 83.28 seconds on RTX4090.

The prepared config is preserved as the pre-run specification; its preparation
status is historical. Actual run status and hashes are in
`results-local/sft/training-manifest.json`.

Direct-answer empty thinking prefixes are prompt-masked. Genuine reasoning and
answer termination remain supervised. The data source contains 640 bilingual
rows; this run uses the prescribed order and stops at step69.

This is not a pure single-variable comparison with historical exp012: the TRL
training framework and left padding also differ from the historical custom
Trainer. Do not attribute every change solely to masking.

Matched development inference: 72 thinking-off and 16 thinking-on prompts.
Seen training probes remain separate; the packet is already consumed development
data. Turkish quality adjudication remains pending. See the shared
[session report](../COOKBOOK-SESSION-RESULTS.md).

Local adapter: `results-local/sft/adapter`. Full model weights are not downloaded.
