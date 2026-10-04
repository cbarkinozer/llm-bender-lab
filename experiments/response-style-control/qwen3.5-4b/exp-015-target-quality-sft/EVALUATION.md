# E/F evaluation protocol v1 (pre-output)

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
