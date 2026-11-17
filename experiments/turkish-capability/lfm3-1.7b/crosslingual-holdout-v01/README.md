# Matched language-transfer diagnostic v01

Frozen before inference, 2026-11-17. Twelve prompts: three underlying cases
(arithmetic, grounded uncertainty, faithful sentence generation), each in EN→EN,
TR→EN, EN→TR and TR→TR. Three separate symbolic arithmetic controls bring the
total to 15 prompts per model, 60 primary generations for four models.

This is a tiny diagnostic holdout, not a representative Turkish benchmark.
Only three matched cases are independent; the twelve language variants are not
twelve independent trials. It does not cover spelling correction or the full
range of arithmetic. Symbolic controls still include a bilingual instruction.
Once used to choose training changes, treat it as development data. Keep every
variant, reference and close derivative permanently outside training. A new
independent final test is required for promotion.

Reproduce/verify with `python scripts/datasets/prepare_lfm3_crosslingual_diagnostic.py`.
Existing files must match byte for byte. `manifest.json` pins packet and protected
train/evaluation hashes. Exact normalized prompt overlap was checked against
train160, old20 and dev20; this does not prove semantic independence. References
are illustrative; accept equivalent faithful wording.

Use separate conversations, native template, no few-shot examples, no target or
rubric sent to the model. The user prompt contains the complete task and requested
output language. All four models receive the same packet. Input-language variants
carry the same facts; cross-language generation necessarily also tests translation.
Conditions provide diagnostic evidence, not perfectly isolated causal mechanisms.

Compare pinned untouched post-trained LiquidAI/LFM3-1.7B (not -Base), CPT-only,
exp009 direct-base SFT step60 and exp007 CPT-initialized SFT step60. Match the
historical vLLM settings: BF16/eager/batch4, context8192, max output4096,
temperature0.1, top-k50, top-p1, repetition penalty1.1, seed3407, prefix caching
off, native template thinking disabled, explicit native EOT plus existing loop
guard. Save actual finish reasons, raw text/token IDs and timing. Reconstruct
merged models on GPU only; recover adapters and logs, not full weights.

Record correctness/meaning preservation, instruction/format compliance, requested
language compliance, language naturalness and stopping separately. Numeric results
for controls are 104, 15 and 575; purchase answer is 48. Do not auto-grade prose
against a single reference or count a preference win as a correctness pass.
Report counts by case and language condition, never an inflated pooled sample size.

Create a new Argilla queue with one prompt and four anonymous answers, and only
two required free-text fields: ranking (ties allowed) and reasoning. Randomize
identities independently by record and balance positions (15 records means each
identity appears three or four times per position). Keep key local/ignored.
Hide identities, scores and references. Preserve existing queues and reviews.
Owner may explain that all answers are wrong in the reasoning field. Inspect
pairwise reviews and raw outputs together with deterministic numeric checks.

Separate thinking-on probes may repeat the purchase variants and symbolic controls
for all models. Do not mix them into the thinking-disabled primary comparison;
record total tokens and latency as well as final-answer correctness.

See `../CROSSLINGUAL-NEXT-STEPS.txt` for the operational handoff and conditional
bilingual training pilot. No new inference or training has run for this packet.
