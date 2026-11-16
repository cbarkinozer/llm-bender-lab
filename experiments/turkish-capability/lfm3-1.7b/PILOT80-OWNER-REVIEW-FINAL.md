# Completed owner review, 2026-11-16

All20 simplified Argilla records are submitted. Original rankings and notes were
joined by opaque external ID to the correct private per-record key. Rank1 is best.
No annotations changed. This supersedes PILOT80-OWNER-REVIEW.md.

| Comparison (first vs second) | First preferred | Second preferred | Tied |
|---|---:|---:|---:|
| SFT1e-4 vs SFT2e-4 | 6 | 10 | 4 |
| SFT1e-4 vs CPT | 19 | 1 | 0 |
| SFT2e-4 vs CPT | 18 | 2 | 0 |

**Working pilot winner: exp-006-sft-lr2e4 (learning rate2e-4).** It wins10 of16
decisive SFT comparisons (62.5%);4 are ties. This is a modest observed preference,
not statistical proof or production readiness. Preserve exp-005 as an alternative.
A/B/C identities change across prompts; there is no fixed A model.

One material note/rank conflict remains:
`sft:TR-part1-261025_v1-fixed.jsonl:3373` says C and A repeat and B is generally
good, but ranks C first and B last. B maps to2e-4 on this record. Leaving it
unchanged gives2e-4 ten wins vs six; excluding it as a sensitivity check gives
ten vs five, with four ties. Either way the working choice is2e-4. No inferred
grade replaces the owner's original response.

Notes explicitly judge all answers inadequate on several prompts. They identify
unnatural Turkish and suffixes, meaning changes in rewriting, invented technical
explanations, ungrounded claims, arithmetic/constraint failures and repetition.
Some notes are too brief for dimension-specific judgments. Preferences are not
correctness pass rates. Reference/regulatory claims in notes were not fact-checked.

The owner saw partial decoded results before completing the final7 items, so the
full20 are not presented as a pristine fully blinded study. First13 gave2e-4 five
wins,1e-4 four and four ties. These20 now inform iterative diagnosis/working
selection and are not a fresh final release test. Never train on them or rewrites.

Ignored evidence: `pilot80-runtime-local/argilla-blind-review-simple-v01/` contains
the timestamped server snapshot and `decoded-owner-review.json` with original
notes, decoded rankings, pairwise counts and snapshot/key hashes. Exporter:
`scripts/evaluation/export_lfm3_pilot80_owner_review.py`.
Final snapshot SHA256:
`cad49385eb2d334094511a5a89d3c1ff1f2d532c76385ab36840af04ffb96c16`.

Next primary baseline is untouched pinned LiquidAI/LFM3-1.7B. This does not change
the CPT-merged initialization of planned SFT runs. See PILOT160-PAIR-PLAN.md.
