# New80 training candidates, batch02

[Open the simplified text editor](http://127.0.0.1:6900/dataset/2622bd70-e5e5-48af-8905-91a4ea47032f/annotation-mode).
Active dataset `turkish-sft-train80-batch02-text-v02`, workspace `sft-review`.

Owner changed the workflow: exactly three editable text questions, ordered Input,
Thinking (optional), Output. No keep/edit or quality selections. All text is
prefilled as the owner's draft, not a model suggestion requiring acceptance.
Submit saves the final text. Blank Thinking explicitly means no separate reasoning;
export must NEVER restore source reasoning when the submitted field is empty.
Write reasoning without wrapper tags; Output contains only the final response.
Submitted text indicates owner completion, not a set of inferred good/pass labels.

Migration preserved14 submitted owner edits and20 standing-approved Occam records
as completed. The other46 rows have editable draft responses. Earlier corrected
input/answers were retained; think/thinking wrappers were split into separate
thinking/output fields, and untagged corrected answers retain empty thinking.
Originals remain read-only for provenance. Old queue and responses are preserved;
continue ONLY in the new queue. Migration script:
`scripts/datasets/publish_turkish_batch02_text_edit.py`.
Receipt and immutable before-migration snapshot are in ignored review-local/batch02/.
New schema and all80 field/prefilled-response values were verified by server readback.

80 new identities:20 public Occam,20 Turkish-SFT,20 Atlas,20 CoT. Occam20 are
completed using the owner's standing prior approval, explicitly noted in responses.
Remaining60 await review. Existing queues, edits and protected20 are unchanged.

Previous source-review schema is superseded. Supply complete Input and Output,
not partial patches. Thinking is optional even for a CoT-source record.
Direct answers without thinking tags are allowed for simple CoT-source questions.
Retain useful verified reasoning separately; do not add reasoning merely because
of source name. Original systems stay visible; export uses the shared versioned
Turkish system and preserves source instructions in provenance.

Same pinned sources as download-manifest.json. Selection excludes validation,
old100 IDs/exact prompts, structural flags, protected12-word overlap and prompt
5-gram containment >=0.35 against old100 and within batch02. Five rows per source
answer-character quartile, preferring underrepresented available categories.
SFT/Atlas lack category metadata, so this does not establish topic balance.

| Source | Count | Raw target tokens | Median | Min-max |
|---|---:|---:|---:|---:|
| Occam | 20 | 1,509 | 51 | 7-470 |
| Turkish-SFT | 20 | 36,190 | 1,987 | 93-2,718 |
| Atlas | 20 | 2,309 | 99.5 | 34-328 |
| CoT | 20 | 21,095 | 896 | 211-2,460 |

Total61,103 raw target tokens, excluding template overhead. NOT token balanced;
recheck after edits. Rejects require replacements. The raw combined prompt/answer
limit3600 leaves template room but does not replace the final4096 rendered check.
Edited protected test prompts/targets separately audited: zero12-gram and prompt
containment hits. String checks are not global/semantic contamination clearance.

Packet SHA256: `078a89e43e6a03d8329829e2a0b1f8023678653ae958b159ebf77ffdcc925312`.
Ignored evidence under review-local/batch02/: candidates80.jsonl, manifest.json,
argilla-receipt.json, edited-holdout-overlap-audit.json. Builder:
`scripts/datasets/prepare_turkish_review_batch02.py --publish`.
All80 full UI fields read back exactly;20 Occam completed and60 pending at creation.
No training-ready160 export or training run has been made.
