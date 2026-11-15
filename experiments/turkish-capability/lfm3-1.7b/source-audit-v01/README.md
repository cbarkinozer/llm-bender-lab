# Turkish SFT source audit v01

2026-11-14. **Audit complete for this bounded intake phase; no source or row is
accepted for training by this report.** All four datasets were downloaded at
immutable revisions, checked for file integrity and scanned structurally.
Agents reviewed 142 complete training records purposively: 38 Occam, 25 SFT,
42 Atlas and 37 CoT. These are qualitative observations, not corpus error rates,
independent human validation or a ranking based on a representative trial.

**Decision:** use complementary, individually reviewed selections. Occam is a
useful behavior seed, Atlas is the main candidate pool for short task diversity,
CoT needs item-by-item problem/solution verification, and SFT-v1.0 should be a
small, carefully checked explanation source. None should be concatenated in full.
No source by itself meets the general-coverage contract.

## Source identity and full-corpus measurements

| Source | Revision | Rows | Median assistant content tokens | Candidate role |
| --- | --- | ---: | ---: | --- |
| [Occam](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/tree/947850d484c71f657dbec2bb7e3d356cb5fb23e3) | 947850d484c71f657dbec2bb7e3d356cb5fb23e3 | 104 train + 20 dev | 37.5 | Precision, uncertainty, clarification, appropriate response scale |
| [Turkish SFT v1.0](https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0/tree/5a5a852ab9067866d72ed92381205518feaae5fb) | 5a5a852ab9067866d72ed92381205518feaae5fb | 5,579 | 2,401 | Selective explanations, interpersonal/practical writing |
| [Atlas](https://huggingface.co/datasets/AlicanKiraz0/Turkce-Atlas-Instruct/tree/c387738c5deacbb35667ab4057930adc34e647e8) | c387738c5deacbb35667ab4057930adc34e647e8 | 336,146 | 93 | Structured extraction, summaries, grounded tasks, transformations |
| [CoT](https://huggingface.co/datasets/AlicanKiraz0/Turkish-CoT-Instruct-Dataset/tree/3473e6c6350564d5a7000faf3ff140e9c4b9d1f2) | 3473e6c6350564d5a7000faf3ff140e9c4b9d1f2 | 4,868 | 1,021.5 | Verified reasoning configuration; math, logic, constraints |

**346,717 records scanned**, including Occam's 20 development rows for descriptive
inventory only. Per owner clarification, Occam data comes **only from this
pinned public HF release**. No older local Occam data or drafts were ingested.
Its existing development rows remain development, never training candidates.

Token counts use the pinned LFM3 tokenizer, revision
`0dc4268b561499c648c7ba7c9466bf3d8d01517a`, SHA-256
`7e226e34bface23ccf6e495d157bf77186c1c30a7659880e1a8994db528c3701`.
[Pinned tokenizer file](https://huggingface.co/LiquidAI/LFM3-1.7B/resolve/0dc4268b561499c648c7ba7c9466bf3d8d01517a/tokenizer.json).
They cover raw role content with special tokens disabled, **not native chat
serialization or audited supervised-token exposure**. Occam multi-turn assistant
content totals include earlier turns; its source final-answer-only policy must
be preserved by an eventual training exporter.

SFT has 298 rows above 4,096 raw user+assistant+system tokens. CoT has 293 above
4,096 and 29 above 8,192. Template tokens add overhead; these are not actual
truncation counts. Later models need their own tokenization/objective checks.

## What each source contributes, and what to filter

### Occam: preserve a useful behavior seed

Observed strengths: exact entity/number selection, Turkish lexical distinctions,
negation, joint conditions, calibrated uncertainty, selective clarification,
context/memory boundaries and appropriately detailed practical answers. It is
not simply a short-answer corpus: some useful answers are substantially longer.

Limits: only 104 training examples, mostly short inputs; modest summary
compression and a few overly absolute troubleshooting/explanatory statements.
The complete public release contains only five multi-user-turn conversations.
It does not establish broad coding, mathematics, translation or long-context
coverage. Retain its original metadata and source split. Historical provenance
gaps in the public card remain documented limitations, not permission to import
other local versions.

### Atlas: broad short-task pool, not automatically faithful

Useful inspected examples include grounded summaries, JSON/table extraction,
precise lists, arithmetic, morphology and practical plans. The full source
contains substantial explicit task wording for summaries, context-grounded
responses and JSON, but lexical counts are not validated capability labels.

Concrete defects: three entire targets are only `S:` (lines 80293, 205957,
261622); some responses invent facts or causal certainty; one arithmetic item
confuses margin with markup. Bare utterances sometimes receive unsolicited
proofreading despite no editing instruction. Several grammar explanations
misstate rules. Template repetition and certainty should be reviewed by family.

The audit's normalized comparison finds 700 repeated-prompt groups, 1,022 excess
rows and up to 11 responses per prompt. All 700 groups have distinct normalized
answers. Distinct answers are **not automatically contradictions**; compare
their meaning before retaining alternatives or choosing one. Counts differ
from the card's literal comparison because normalization changes equivalence.

No actual interlanguage translation was confirmed in the bounded targeted
inspection: wording such as çevir also includes table conversion or rewriting.
Do not count 4,082 lexical hits as 4,082 bilingual translation examples.

### CoT: worthwhile reasoning material, verification mandatory

All 4,868 assistant responses contain an opening think tag. The source has 14
declared domains, 13 reasoning labels, four difficulty labels and eight formats;
these are intended taxonomy, not independently established competence/difficulty.
Five records have two opening think tags and only one closing tag; withhold
them as-is. A broad English-phrase heuristic flags 183 rows, which is **not** a
validated English-reasoning count.

Among 37 fully reviewed items across all domains, the agent proposed 13
conditional selections, 16 repairs and eight discards. No extrapolated defect
rate follows. Independent calculations found both correct arithmetic and bad
derivations, underdetermined puzzles, unsupported numerical claims and
reasoning/final-answer inconsistencies. A correct final answer cannot rescue
an incorrect worked solution. Some prompts themselves need rejection/repair.

Keep reasoning as a planned separate configuration. Store permitted worked
solutions separately from final answers, verify both, and map to each model's
native format later. Do not make duplicated long reasoning plus long finals
the default response style for every task.

### Turkish SFT v1.0: high-cost explanation selection

The fixed source system requests academic depth, examples and Turkish context,
so length alone is not noncompliance. Useful inspected cores include templates,
apology/meeting scripts, conceptual explanations and short transformations.

The purposive review also finds substantive numeric/internal contradictions,
unsupported company cases and research percentages, artificial contextual
attachments and incomplete targets (`...`, `**S`, or a heading alone). One
record contains a replacement character. Claims without evidence were marked
unverified, not automatically false. Do not train the model to imitate
unsupported scholarly authority.

Six normalized duplicate-prompt groups account for nine excess rows with
different targets. There are no exact prompt+answer pair duplicates under the
defined normalization. The 2,401-token median answer makes source/task/token
balancing particularly important. Prefer a small verified selection; do not
solve quality problems by blindly truncating or automatically shortening answers.

## Coverage decisions for the reusable core

| Capability | Best current candidate contribution | Remaining work |
| --- | --- | --- |
| Grounded QA and summaries | Occam precision + selected Atlas tasks | Remove invented details, check evidence/causal scope; independently author longer contexts |
| Instruction/structured output | Atlas extraction + Occam constraints | Validate schemas and exact constraints; diversify system/task wording |
| Turkish editing/lexical precision | Occam seed + selected Atlas morphology | Make editing intent explicit; verify rules and minimal changes, include unchanged controls |
| Explanations/practical writing | Small verified SFT/Atlas/Occam selections | Appropriate depth without fabricated facts, authority or universal claims |
| Reasoning/math | Verified CoT + selected Atlas arithmetic | Check premise validity, intermediate steps, unique solvability when claimed, final result |
| Bilingual translation | Not established adequately by this audit | Acquire/author independent EN↔TR examples and verify fidelity |
| Multi-turn | Five public Occam conversations only | Add independent follow-ups, corrections and clarification families |
| Executable coding | Not established by technical-topic labels | Add runnable problems with checks; separate advice from executable correctness |
| Long-context tasks | Not established by long answers | Add licensed/original longer documents and evidence-dependent questions/summaries |
| Creative writing/general knowledge | Sparse purposive evidence | Define coverage and independent correctness/constraint review |
| Uncertainty/responsible assistance | Occam + selected contextual items | Balance direct answerable cases, genuine missing evidence and useful clarification |

All examined sources other than Occam are strictly system/user/assistant triples.
Do not manufacture a multi-turn coverage claim from three-message formatting.
Do not claim general coverage from CoT's balanced domain metadata or Atlas size.

## Duplication, benchmark and provenance boundary

No exact normalized user-prompt groups cross the four sources. No exact full
user-message/prompt matches to the inspected CETVEL500 protected material were
found. A supplemental scan found no contiguous normalized 12-word prompt
overlaps with the known cohort's prompts/source passages or Occam dev user
turns (excluding expected dev self-matches). These narrow negative results
**do not clear semantic, translated, paraphrased or unknown-benchmark overlap**.
Answer-only copies, prompt substrings shorter than the threshold, canonical
problem variants and other benchmark corpora remain untested.

Declared licenses: Occam/CoT Apache-2.0, SFT/Atlas MIT. Retain source-specific
license evidence and attribution; do not relabel a combined corpus wholesale.
The [card review](source-card-review.md) records missing upstream/generation
provenance and distinguishes audit selection from training/redistribution
eligibility. No prohibited use was established. Missing evidence is not proof
of misuse; the source cards do not independently resolve every upstream right.
Continue authorized content review, recording gaps before a release decision.

## Current review allocation: 80 train / 20 held-out test

Owner review policy updated 2026-11-14: Occam's public data was already reviewed
and approved by the owner; no duplicate review is required. Applied submitted
keep/pass/pass/good/appropriate responses to 15 untouched training Occam records
and five test Occam records, with explicit prior-owner-approval notes. Preserved
five existing submitted Occam training reviews, including two edits. All 25
selected Occam records are completed. Other records and responses were verified
unchanged; pre-change snapshots are in ignored `review-local/`.

Both Argilla guidelines now define ratings as applying to the corrected answer
when decision=edit, or the original when decision=keep. Keep decision=edit after
repair and provide the complete replacement; good/appropriate ratings are valid
for that repaired version. CoT replacements include both worked solution and
final answer. This policy does not retroactively change any owner ratings or
overwrite frozen source packets. See `owner-review-policy-receipt.json` and
`scripts/datasets/apply_turkish_owner_review_policy.py`.

Owner requested a 100-record starting pool, maintaining the source balance.
The original 60 records remain training candidates; 20 additional training
candidates and 20 separate test candidates were added. Each of the four sources
contributes **20 train + 5 test**. Occam still comes exclusively from its pinned
public HF training file; its original validation set remains separate.

- [Review 80 training candidates](http://127.0.0.1:6900/dataset/e5e5a740-263d-40f9-84a2-cbeb6f6e0747/annotation-mode)
- [Review 20 held-out test references](http://127.0.0.1:6900/dataset/5f6aff9b-a5c5-4854-b670-6468c18a1b59/annotation-mode)

Existing records and responses were verified unchanged after append. New test
rows were excluded from the earlier purposive samples. Additional rows span
answer-length quintiles within each source after structural/duplicate screening;
equal source counts do not imply equal capability or token exposure. All additions
still require owner review. Rejected or unusable items need replacements within
their assigned split and source; the 80/20 allocation is not 100 accepted items.

The frozen [100-record manifest](review-100-manifest.json) records split IDs,
packet hashes, selection and limitations. Source-bearing packets remain ignored
under `review-local/review-100-{train,test}.jsonl`. `source_split=train` records
upstream origin; `assigned_split` determines our downstream use. Test items,
their corrections and variants must never enter training. Do not use test
results for checkpoint selection or iterative tuning; reserve separate dev data
when that begins. Reference-quality review can occur before the test is frozen.

Checks found 100 unique normalized prompts and no train/test five-word-gram
containment at or above 0.35. Added prompts had no protected 12-word matches.
These are lexical checks, not semantic/cross-lingual family clearance. Manual
family and provenance review remains a pre-training gate. Public-source items
are not guaranteed unseen during pretraining. Twenty test items are a pilot,
not a reliable broad-capability benchmark.

Reproduce with `python scripts/datasets/expand_turkish_review_100.py`; append
with `--publish`. Existing frozen packets are hash-checked and not overwritten;
publication skips existing IDs and verifies existing record/response snapshots.
See [upload receipt](argilla-review-100-receipt.json).

## Historical 60-record calibration packet

Prepared **60 unapproved source-review records**, 15 per source, at
`review-local/calibration-60.jsonl`. All derive from source training files; none
from Occam validation, local Occam drafts or the 500 evaluation examples. Source
messages are preserved with repository revision, file line, native ID where
available and hashes. All are pending, human_reviewed=false, training_eligible=false.

The [manifest](calibration-60-manifest.json) contains the 60 source IDs and packet
hash, but no copied source text. This balanced **review allocation is not the
training mixture**. It intentionally offers potential keep/edit/reject examples,
including flawed originals. Agent reviews cover a subset of these exact 60;
every record requires owner review.

**Argilla is live:** [review the 60 records](http://127.0.0.1:6900/dataset/e5e5a740-263d-40f9-84a2-cbeb6f6e0747/annotation-mode).
Dataset `turkish-sft-source-calibration-v01`, workspace `sft-review`, server/client
2.8.0. The existing local Compose stack was started; other datasets were not
deleted or replaced. See `argilla-calibration-receipt.json` for count and hashes.
The server is bound to localhost; the link works on this machine while Docker
and the stack are running. Existing local login configuration remains in use.

The new dataset shows original system/context/task/answer, separate reasoning
and final views when parsable, editable corrected target and keep/edit/reject/unsure.
It collects correctness, grounding, Turkish quality, instruction adherence,
appropriate detail and notes. Owner labels are not prefilled from agent decisions.
Submit responses explicitly; drafts do not count as completed review. Re-review
edited targets; retain source identity and edit provenance. Content acceptance
alone does not clear provenance or leakage.

After calibration, select sources against uncovered capabilities, reserve
independent dev/final families before authoring variants, and expand in small
reviewed batches toward the corpus-design gates. No new teacher generation,
GPU training, dataset publishing or source outreach occurred in this audit.

## Reproduction and storage

Run from the repository root:

```powershell
python scripts/datasets/audit_turkish_sources.py
python scripts/datasets/audit_turkish_source_overlap.py
python scripts/datasets/measure_turkish_source_tokens.py
python scripts/datasets/prepare_turkish_source_calibration.py
python scripts/datasets/publish_turkish_source_calibration.py
```

The token measurement expects the pinned tokenizer JSON in
`raw-local/tokenizer/tokenizer.json`; its immutable URL and hash are recorded
above. The preparation script protects an existing calibration packet from
overwrite; the publisher refuses to replace an existing Argilla dataset.
Inventory scripts regenerate mechanical summaries only; preserve
versioned reports when changing code/pins. Dependencies are existing requests
and tokenizers; no new framework was installed.

`raw-local/` contains pinned source files/cards/metadata; `review-local/` holds
source-bearing samples, indexes and the calibration packet. Both are ignored
by Git. Their files must be downloaded/rebuilt on another machine; **Git alone
does not transfer them**. Version manifests, hashes, audit code and concise
findings. Semantic reports retain review scopes and source-row references and
are agent judgments, not automatically reproducible semantic ground truth.
