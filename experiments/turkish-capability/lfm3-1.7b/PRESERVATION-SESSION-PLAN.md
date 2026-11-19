# Three-experiment GPU session, 2026-11-19

Owner authorized all three; SSH ssh5.vast.ai:38402, RTX4090 24GB. Private research,
no publication or upload of model weights to an external repository requested.
Base and merged weights stay on pod. Preserve adapters, outputs and logs locally.

1. Native thinking-enabled inference: original base, Turkish60, bilingual69 on
   the consumed eight symbolic + eight TR/TR arithmetic prompts. Compare to
   their saved identical thinking-off prompts. Only thinking-mode input changes;
   maximum4096, temperature0.1, top_k50, top_p1, repetition penalty1.1, seed3407,
   batch4, BF16, context8192, explicit native end-of-turn and existing loop guard
   remain unchanged. Inspect actual rendered prefixes: a flag alone is not proof
   that the template changes. Consumed diagnostic, never fresh final evidence.
2. exp-012-base-bilingual: exact reviewed640, order, LR1e-4, r32/alpha64,
   micro2/accum4, 113-step cosine/warmup6 recipe from exp011, but fresh LoRA on
   pinned original LiquidAI base instead of merged CPT. Fixed primary checkpoint69;
   train113 to preserve the same schedule seen by checkpoint69. Checkpoint113 is
   a backup, not another candidate selected on this new test.
3. exp-013-base-preservation: same original parent and optimization, reviewed640
   plus80 fresh verified synthetic rows (40TR/40EN, including40 worked solutions).
   Replace two short row slots each update, and adjust one original slot's length
   to approximately match supervised tokens. This is a data composition AND
   original-row reweighting pilot, not a pure additive-data causal estimate.

Total supervised tokens: control209811, preservation209590 (-0.105%). At primary
step69:125664 versus125642 (-0.018%). Supplement contributes1.95% of target tokens
and25% of row slots; short examples are not equivalent to25% of token exposure.
Every supplemental row appears; exact order/unique coverage in matched-order.json.
No inference result informed these recipes. Empty thinking remains supervised,
as previously owner-decided; existing worked solutions use native thinking fields.

Fresh evaluation:32 prompts (16TR,16EN), with14 numeric cases, two logical
underdetermination cases, and16 general language/meaning/constraint tasks. Same
packet and decoder for original base, historical Turkish60/bilingual69, then both
new primary adapters. Run the baseline BEFORE new training. References remain
local, never in the uploaded packet. This packet has no EN/TR or TR/EN prompts;
it measures monolingual Turkish/English capability, not complete four-direction
translation transfer. Prior four-direction results remain diagnostic context.

Predeclared reporting: numeric value and units, logical correctness, Turkish
meaning/naturalness, requested format/language, English retention, token lengths,
EOS/loops/timeouts/max-length counts. Correct numeric value alone is not full
correctness; examine intermediate contradictions and missing units separately.
Manual prose review accepts equivalent formulations. Show item-level outcomes
and paired counts; language-paired template families are correlated. No aggregate
letter score: blind labels randomize per record and decode with the private key.

Release decision remains owner-reviewed: useful Turkish can justify modest
measured losses, but unresolved basic arithmetic failures and English regressions
must be disclosed with counts/examples, not described as 'no catastrophic
forgetting'. No automatic universal release threshold is inferred from32 prompts.
Do not select checkpoint113 or modify the recipe on this fresh packet and then
continue calling it an untouched final test. One seed is exploratory.

Native label/length/EOT audits, finite-loss save/reload generation smoke and
20-example tiny-overfit checks are required for BOTH new runs. Original-base
bytes are checked even though the reused Trainer directory has the legacy
name cpt-merged. Receipts identify the real parent explicitly. Resolved runtime
uses Python3.11.17 rather than historical3.12; package versions/driver/hardware
are captured, so parent attribution is approximate rather than bitwise causal.

Frozen runtime: preservation-session-v01-local/freeze.json
SHA256 c0853cabaf9a3e2b917baf5ae2b4165c942207517c1686582e6b4b9cc31e85a6.
Transferred input archive SHA256
9885ef0ce8eb738acaef44742608c4e56dad61b73eae984121d75cd22bb42f36.
Source commit and dirty file hashes are recorded; historical results unchanged.

Execution fix01 (before any generation/training): HF Hub2.4 whole-snapshot
completeness rejected an intentionally minimal cache. Use explicit pinned cache
directories with model/adapter SHA checks instead. No recipe, data or decoding
change; failed prepare log preserved. Initial freeze preserved as freeze-initial.json.
Active freeze SHA256 f29a9f9051091e861e2958ae4c429bed44449487ff4ec88ab159ed57aeb0711d.

Execution fix02 (before production training): the inherited tiny-overfit selector
assumed four sources and chose25 after adding a fifth. Keep the same20 original
training examples for BOTH diagnostic runs; actual SFT retains all720 semantic
rows and its unchanged native audit/order. Failed assertion preceded any model
update for that diagnostic. Logs preserved under logs-attempt02. Active freeze:
a1a6c176265dc5687476e5afa0f73b738b72c378042ab51585e5f90f27702e17.

Protocol addendum03, before observing any new-adapter inference: run the two
fixed69 adapters on the SAME eight consumed symbolic controls in both thinking
modes.32 secondary diagnostic outputs, no additional training or checkpoint
selection. Original primary32 unchanged. Active freeze SHA256:
5506599197d37a7adfcaba7783b1a36f33c640621fedb2be4ab933c6d09fe0e8.
