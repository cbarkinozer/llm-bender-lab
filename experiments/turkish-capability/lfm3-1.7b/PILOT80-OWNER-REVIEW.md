# Partial owner review, 2026-11-16

Superseded by [completed20-row report](PILOT80-OWNER-REVIEW-FINAL.md). Preserve
the partial snapshot below as historical evidence; it is not the final result.

Exported 13 submitted records out of20 from the simplified Argilla queue
`turkish-pilot80-blind-holdout20-simple-v01`. Joined opaque external IDs against
that queue's private per-record model key; rank1 means best. No annotations were
changed. Remaining7 are ungraded, not failures. Owner can stop reviewing this pilot.

| Comparison (first vs second) | First preferred | Second preferred | Tied |
|---|---:|---:|---:|
| SFT1e-4 vs SFT2e-4 | 4 | 5 | 4 |
| SFT1e-4 vs CPT | 13 | 0 | 0 |
| SFT2e-4 vs CPT | 12 | 1 | 0 |

These are rankings as entered, not correctness or production-readiness scores.
The small, partially reviewed subset does not establish an SFT winner. The owner's
impression favors1e-4; retain this as qualitative feedback, not a measured victory.
Both SFTs strongly outperform CPT in these recorded preferences.

At least one annotation has a material note/rank conflict:
`sft:TR-part1-261025_v1-fixed.jsonl:3373` says C and A repeat and B is generally
good, but ranks C first and B last. B maps to2e-4 on this record. Preserve the
original ranking and note; do not silently invert or selectively drop it.

Notes flag unnatural Turkish, suffix/word-choice errors, hallucination and weak
reasoning. The running-plan example explicitly judges all three incorrect despite
ranking them. Preference therefore does not imply an acceptable answer. Some notes
are too brief to support per-dimension classification. No pass rate is inferred.

Local ignored evidence under `pilot80-runtime-local/argilla-blind-review-simple-v01/`:
`owner-responses-snapshot.json` preserves server records/responses;
`decoded-owner-review.json` retains decoded submitted rankings, original notes,
pairwise counts and the snapshot hash. Private mappings remain local and are not
uploaded to Argilla. Published model identities make this pilot unblinded from
this point; remaining reviews must not be reported as a fully blinded new study.

Next baseline per owner: untouched pinned LiquidAI/LFM3-1.7B, with matched prompts,
template controls, decoding and budgets. Existing CPT results remain historical.
Changing the comparator does not itself change SFT initialization. Next data step:
80 new reviewed source examples toward160 training rows, plus separate development
data. Do not absorb these20 evaluation examples or corrected versions into training.
