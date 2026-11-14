# Recovered LFM3 100M final500 responses

Recovered on 2026-11-14 at the owner's request for row-by-row weakness analysis.
The four original files are byte-identical in both Downloads recovery folders;
SHA-256 hashes and validation details are in `recovery-verification.json`.

- `answers.jsonl`: all 500 original generations, prompts, source documents,
  targets, raw outputs, token IDs, timing, and stopping metadata.
- `scored-samples.jsonl`: the same rows plus task-specific scores and diagnostic
  flags. Start here for row-by-row analysis; join by `id`.
- `manifest.json`: selected IDs, checkpoint path, protocol, generation settings,
  and runtime versions. Output order differs from selection/submission order.
- `scores.json`: original aggregate scores.

There are 100 rows each for GECTurk, TQUAD, XQuAD Turkish, WMT English-to-Turkish,
and MLSUM Turkish. This evaluates the 100M continuation checkpoint; the manifest's
base model repository identifies its starting model. No generations were rerun,
cleaned, truncated, or reconstructed. Original scoring is preserved.
Keep these evaluation-only rows out of training data. This narrow owner-requested
Git exception does not change storage policy for other local artifacts.
