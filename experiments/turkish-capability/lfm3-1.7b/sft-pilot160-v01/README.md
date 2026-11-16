# Reviewed Turkish SFT pilot160

Status: owner review complete; semantic export frozen. Training deferred to the next session at the owner's request.

- `batch02-train.jsonl`: all80 submitted final Input/Thinking/Output responses,20 per source.
- `train.jsonl`: corrected previous80 plus new80;40 each from public Occam, Turkish-SFT, Atlas and CoT.
- `test.jsonl`: previous protected20, byte-identical; diagnostic evaluation only, never training.
- `manifest.json`: hashes, provenance, review snapshot fingerprint, checks and raw tokenizer statistics.

Input and output use submitted owner text verbatim. Optional blank Thinking means no reasoning; source reasoning is never restored. No quality ratings are inferred from submission. Immutable original messages, pinned source identities and the complete saved response remain in each new row. Argilla records remain intact. Raw server snapshots are additionally retained under ignored `source-audit-v01/review-local/batch02/`.

The new80 contain11 nonempty reasoning examples; the combined160 contain30. Native empty blocks for direct-answer rows are a serializer behavior, not fabricated reasoning. New80 target tokens total20,141 (raw source targets61,103); combined targets45,437. Equal row counts do not imply token balance.

| Source | Rows | Target tokens | Share | Median target tokens |
|---|---:|---:|---:|---:|
| occam | 40 | 2,703 | 5.9% | 40.0 |
| sft | 40 | 19,589 | 43.1% | 486.0 |
| atlas | 40 | 7,549 | 16.6% | 144.0 |
| cot | 40 | 15,596 | 34.3% | 287.0 |

Counts exclude native template tokens; reasoning and output are tokenized together. Duplicate normalized training prompts and train/test exact prompt overlap: zero. Final new80 input/output/reasoning have no protected12-word matches against the old20, public Occam validation or the pinned CETVEL500 audit text. New prompts have no holdout5-word containment hits at0.35. These lexical checks do not prove semantic or cross-lingual independence.

Selection was stratified by source and answer length with category diversity where metadata existed; it was not a systematic model-weakness quota sample. Owner revision improves targets but does not establish complete general coverage. Keep that limitation explicit.

Before tomorrow's GPU launch: prepare160-compatible configs/entrypoint, establish a separate frozen development packet and selection rubric, rerun native labels/lengths and actual-model smoke/tiny-overfit gates. Preserve optimizer/scheduler/RNG state and epoch3/5 checkpoints. See [pair plan](../PILOT160-PAIR-PLAN.md). No training was launched by this export.
