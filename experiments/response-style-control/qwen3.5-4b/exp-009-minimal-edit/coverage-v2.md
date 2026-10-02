# Active coverage map: prompt-selection-v2

V1 remains untouched in `data/`. V2 in `data-v2/` is the active selection for
future base generation. There are still 100 rows, 80 train / 20 validation.
No answer targets have been generated or human-approved.

The complete machine-readable row mapping is `data-v2/coverage-map.json`.
This table makes the behavior checks visible; IDs alone are not outcome evidence.

| Requirement | Train examples | Validation examples | What is checked |
| --- | --- | --- | --- |
| Directness / requested format | me-001–008, me-014 | me-009, me-010, me-100 | Corrected text only, exact number/unit, one-sentence message; no unsolicited wrapper |
| Accurate extraction | me-011–018, me-021–028 | me-019, me-020, me-029, me-030 | Exact requested source fact, entity, quantity and unit despite distractors |
| Faithful summary | me-031–038 | me-039, me-040, me-099 | Main event and conditions; association is not cause, expectation is not certainty |
| Useful explanation | me-041–048 | me-049, me-050 | Enough explanation and practical detail; no universal short-answer rule |
| Selective clarification | me-051–058 | me-059, me-060 | Answer, clarify, or conditionally answer; use clarification and stop asking |
| Groundedness | me-061–068 | me-069, me-070 | Supplied causes versus unsupported causes, motives, diagnoses and certainty |
| Turkish precision | me-001–008, me-071–078 | me-009, me-010, me-079, me-080 | Orthography, suffixes, agreement, exact characters, and near-word meaning |
| Non-anthropomorphism | me-081–088 | me-089, me-090 | No invented personal preference, memory, feeling or attachment; explicit fiction/hypothetical remains usable |
| Neutral acknowledgment | me-085 | me-089, me-090 | Acknowledge without fake emotion, intimacy, reflexive questioning or unwanted advice |
| Consistency / integrity | me-091–098 | me-099, me-100 | No contradiction/repetition; correct negation, constraints and preserved uncertainty |

## Priority: similar words, not only characters

- `me-071`: **doktor / doktora**, unchanged historical qualification question.
- `me-072`: **yönetim / yöntem**, unchanged historical approval question.
- `me-075`: **tasarı / tasarım**, unchanged historical award/source question.
- `me-076`: **deneyim / denetim**, unchanged historical three-year requirement.
- `me-078`: **artırım / aktarım**, unchanged historical Friday/Saturday schedule.
- `me-079` (validation): **vergi / veri**, unchanged historical rules question.

These six rows directly probe near-word/term discrimination. Character-focused
rows are a smaller part: `me-073` **kır/kir (ı/i)**, `me-074` **kar/kâr**, and
`me-080` (validation) **hala/hâlâ**. Grammar correction provides additional suffix,
tense and syntax coverage. No exhaustive language-mastery claim is made.

## Question-loop coverage

- `me-052` and `me-053` share the headphone scenario and are both train.
  The first lacks the relevant information; the second includes clarification
  and an answer saying the current headphones work and meet the user's needs.
- `me-054` and `me-055` share the job-choice scenario and are both train.
  The resolved conversation supplies salary, schedule, priorities and equal
  remaining conditions. Re-asking those questions is a failure.
- `me-059` (validation) is a different presentation-scheduling conversation,
  with reason, attendees, room and readiness supplied. It must receive an answer.
- `me-060` (validation) still tests genuinely missing context. Resolved cases
  must not teach the opposite overcorrection of never asking a question.

All assistant messages inside these inputs are explicitly authored **context**,
not copied historical answers, base-model generations or approved SFT targets.
Future training must mask them and supervise only the final human-edited answer;
masking compatibility remains a pre-training gate.

## Transparent provenance of the revision

V2 changes 13 v1 slots, rather than rewriting the whole dataset:

- 87 historical prompts remain verbatim from v1.
- 4 slots are reselected unchanged historical prompts (3 near-word probes and
  the attachment question `gen-077`).
- 2 historical prompts receive explicit output-format instructions.
- 3 historical openings receive authored clarification/resolution context.
- 4 prompts are newly agent-authored: 3 character contrasts and 1 explicit
  personal-preference probe. They are labeled as new, not falsely attributed
  to the thousands-row corpus.

Thus 91 prompts are entirely historical/verbatim, 5 are historical transformations,
and 4 are new. Exact origins, source hashes and transformations are in every row.

## Leakage checks and manual resolutions

`audit_v2.py` verified 100 row identities, all artifact hashes, provenance bindings,
the exact 80/20 split and 8/2 per category. It checks full conversations **and each
turn**, including assistant context. There are 97 declared scenario groups.

- 1,600 cross-split row pairs checked: no exact prompt/turn match and no near
  flag at sequence similarity >= 0.60 or token Jaccard >= 0.45.
- No shared scenario group or historical source identity across train/validation.
- Against the same 348 local project benchmark rows: no exact or near match at
  sequence similarity >= 0.78. No benchmark outputs or blind mappings opened.
- The two within-train repeated openings above are intentional, linked and
  remain on one side. They are not presented as independent scenario examples.
- The within-train me-042/me-045 planning-phrase flag remains disclosed from v1.

The changed prompts were read in full, and the three closest train neighbors for
each validation prompt were reviewed again. No shared underlying scenario was
identified across splits. In particular, validation presentation **scheduling** is
not a paraphrase of the training relational reaction to a bad **presentation**;
shared topics alone are not leakage. The aunt/ongoing-journey contrast is not a
slot-swapped snow/profit passage. Tax/data, experience/audit and increase/transfer
are distinct word contrasts, not alternate questions on one shared source passage.

These are zero **detected** overlap findings, not proof of universal semantic
independence. The 20 questions are validation, not an independent final test.
No comparison to old adapters is planned; historical training overlap is intentional.

## GPU generation readiness

`generation-config.json` pins the active JSONL hash, base/tokenizer revision and
settings. `generate_base.py --dry-run` passes locally without loading Torch,
Unsloth, a model, or using CUDA. Runtime GPU smoke is still required.

Start with 4,096 new tokens. If the native EOS/end-of-turn has not appeared and
the allowance is exhausted, rerun the same input at 8,192, then 16,384. Preserve
every attempt; never append or force EOS to conceal a length-limit termination.
Rows still incomplete are flagged and excluded from the later annotation import.
This does not force the model to produce a long answer: native EOS stops it early.

Official parameter reference:
<https://huggingface.co/docs/transformers/main_classes/text_generation>.
The effective model-native stop IDs/tokens, raw token IDs, special-token output,
stop reason, template, package versions, config/input hashes and run metadata will
be captured on GPU. No run has been performed for this phase.
