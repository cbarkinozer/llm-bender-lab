# E/F evaluation protocol v1 (pre-output)

## Completed review and future manual-focus partition (2026-10-04)

All32 v3 records submitted and exported read-only to `human-review-v3/`.
Sixteen items have pass for every model; sixteen have at least one partial/fail.
The all-pass items are not literally identical outputs across all four models;
some still have a distinct preferred answer. All-pass does not imply no preference
signal or permanent mastery. User requested reducing repeated annotation effort.

`human-review-v3/manual-review-partition.json` records a versioned future manual
focus16 and regression-watch16. No records are deleted from Argilla, frozen inputs
or validation loss, and no evaluation items move to training. Keep full32 inference
and historical full32 denominators; report a focus subset separately as an
outcome-selected diagnostic slice, never as a directly comparable full score.
Prioritize focus16 for manual review; check changed outputs and new failures on
watch16. Reuse a previous grade only for unchanged prompt/output/settings with
provenance; never automatically grant pass to a new generation. Periodically
re-review the watch set. This is a manual workload policy, not a generation change.

Full32 pass/partial/fail: base17/11/4, C23/3/6, E24/3/5, F26/3/3.
Old20: base8/8/4, C12/3/5, E12/3/5, F14/3/3. New12: base9/3/0,
C11/0/1, E12/0/0, F12/0/0. No broad accuracy or statistical significance claim.
Fourteen ties retained without invented tie allocations; see raw notes in the
per-item export. Original API snapshot with response/user provenance stays external.

## Active user-requested simplified grades v3 (2026-10-04)

The user clarified that simplification must retain per-output pass/partial/fail.
Active queue: `exp-015-016-simple-grades-32-v3`, dataset
`ff9f4e4c-796b-4595-aa33-0229137b6258`. Five required questions: single best-output
selection P/Q/R/S/tie/neither, and one pass/partial/fail grade each for P/Q/R/S.
Optional notes; when selecting tie, specify the tied subset in notes. This
conditional note rule is guidance, not enforced by the UI. Missing tie subsets
remain ambiguous and must not be converted to invented model wins.

Grades prioritize correctness/usefulness: pass=correct and sufficient;
partial=partly correct with important omissions/problems; fail=wrong, unsupported,
contradictory or fails the task. Consider natural Turkish and appropriate length
when preferring answers; Markdown alone is not a semantic failure. Do not report
separate Turkish/style pass rates from a single combined grade.

Same32 inputs/references,128 outputs and private per-item positions; no inference
change. Both prior queues preserved, zero saved responses at v3 creation; external
read-only snapshot taken. This usability-driven post-output protocol supersedes
v2 and the detailed v1 grades. Report per-output grades/preferences, old20/new12,
category slices and me089 sensitivity with small-sample limitations.

## User-approved simplified review v2 (2026-10-04)

After inference, the user found the detailed annotation interface too complicated.
Active review now uses `exp-015-016-simple-comparison-32-v2`, dataset
`5d0f657e-0abe-49cf-865b-d2800028a273`: one required best-output multi-selection
and optional notes. Multiple selected positions mean that exact subset is jointly
best; `neither` must be selected alone. Prioritize correct/useful content, natural
Turkish and appropriate length; reference wording need not match exactly.

The same32 prompts, references, untouched output strings and private balanced
P/Q/R/S mapping are retained. Category/group/termination fields are omitted from
the UI only; all remain available in frozen inference artifacts. The me089 warning
is retained. No extra generation, data repair, checkpoint or model selection.
Original detailed queue is preserved, not deleted or overwritten. It had zero
saved responses when v2 was created; a read-only snapshot is stored outside Git.

This is a documented post-output scoring-protocol change requested for usability,
not a performance-driven change. Report overall preferences and optional qualitative
notes by category and old20/new12, plus me089 sensitivity. Do not invent separate
semantic/Turkish/style pass rates from preferences or optional notes. The detailed
v1 rubric below is historical; v2 does not collect its per-output grades. Overall
preference alone cannot establish a semantic gain or measure absolute accuracy.
If separating style from substance remains unclear, retain that uncertainty rather
than claim the content hypothesis has been confirmed.

## Questions and comparators

Primary E vs C: necessary target repairs at identical80 prompts/40steps.
Primary F vs E:24 new scenarios added under the same40step budget.
Both compared with untouched base under the exact same inference path/settings.
Do not call C's narrow gains a general groundedness gain: all A/C/D still
turn me039's future action into an unsupported price-change commitment.
No overall winning model established by the previous non-blind20 review.

## Items and gates

20 unchanged original development items, plus12 independently authored diagnostic
controls, two per six skills. Not an independent final accuracy estimate.
Approve/freeze control prompts/reference/rubric before any compared outputs.
Train/validation/control remain separate; controls never enter optimizer,
validation loss, replay, best-checkpoint selection or data-generation seeds.
No model results used in writing control references. Preserve historical targets
and me089 warning; report aggregate with and without089.

## Canonical generation

Same pinned base/tokenizer/template, no extra system prompt, enable_thinking=False,
BF16, HF/Unsloth for all four arms, batch1, greedy, repetition_penalty1.05,
seed3407, max_new_tokens4096; native EOS and existing180s/exact-loop failure guards.
Rerun base; do not silently reuse old vLLM base as exact-backend comparison.
Rerun C on new controls; regenerate C on old20 under current canonical code and
compare saved C outputs for reproducibility. Explain any changes, do not erase
historical results. Pin evaluation code/runtime and preserve rendered prompt/token
IDs to verify per-item parity between arms. Do not change decode to help one arm.
E/F final scheduled step40 adapters; no validation-selected best checkpoint.

## Blind human review

Four positions P/Q/R/S, not persistent experiment IDs. Use seeded balanced
per-item permutations: each model appears8 times in each position across32 items.
Keep true mapping outside visible UI fields/guidelines and reveal after review.
No run IDs, adapter names or prior grades shown. Reference may be available,
but evaluate valid alternative answers by the rubric, not exact wording.
Identical outputs must receive identical substance grades.

Each output: semantic correctness/usefulness pass/partial/fail; natural Turkish
pass/partial/fail; separate style compliant/partial/noncompliant. Cosmetic
Markdown alone is not semantic failure. Awkward phrasing and fabricated content
are different errors. Listening formulas such as "anlıyorum" are not inherently
fabricated emotion; judge actual claims. No evaluator AI treated as ground truth.
Select best output(s) through multi-select P/Q/R/S, or explicit neither;
selecting multiple indicates those are jointly best. No generic ambiguous tie.
Optional notes explain decisive evidence, missing mechanism/condition or conflict.

## Reporting and exploratory decision rule

Report raw per-item outcomes and paired gains/losses, category/skill slices,
old20 versus new12 separately, semantic/Turkish/style separately, and ties without
splitting ambiguous historical ties into invented wins. Few items per slice means
descriptive counts, not stable category accuracy. Record EOS, timeout/truncation,
semantic repetitions, p10/median/p90/max output tokens and total tokens.
Keep single reviewer/seed and repeated-development/nonblind-style-recognition
limitations explicit. Randomization reduces label bias, not every source of bias.

An intervention is only a promising follow-up candidate if paired semantic gains
outnumber losses on its intended skills and new controls do not contradict that
direction. Review Turkish, instruction and repetition regressions separately;
new destructive advice, fabricated factual certainty or sustained loops block
promotion even if aggregate rises. A cosmetic-only gain does not support the
content hypothesis. Mixed/no changes support neither hypothesis; do not increase
epochs automatically. Small positive counts warrant replication, not success claims.

## Outstanding implementation

GPU execution/baseline and C inference, balanced blind comparison importer and
raw-output/termination checks follow approved data freeze. No comparison UI with
model outputs exists yet. Current Argilla queues are DATA review only.
