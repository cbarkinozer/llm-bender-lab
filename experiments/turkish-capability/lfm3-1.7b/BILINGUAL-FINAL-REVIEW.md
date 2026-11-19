# Bilingual final evaluation — 2026-11-19

All 35/35 submitted Argilla reviews exported with zero invalid rankings.
The immutable raw snapshot is under `final-eval-v01-local/argilla/`;
SHA256 `81ebbade4783d03f4c0a0d9dfc4c154a261cc9d2f1726366237d1235fbe1a7e0`.
Original notes were not edited. These are owner-submitted, AI-assisted judgments,
not multiple independent human raters. A/B/C were decoded using each group's
private mapping; there is no aggregate best letter.

## Preference outcome

| Candidate | Pairwise preference score | Mean rank | First, including ties |
|---|---:|---:|---:|
| Bilingual checkpoint69 | 59.29% | 1.814 | 17 |
| Original LiquidAI/LFM3-1.7B | 49.29% | 2.014 | 15 |
| Turkish-only checkpoint60 | 41.43% | 2.171 | 8 |

Pairwise scores count a win as 1 and a tie as 0.5 against the other two
candidates (70 comparisons per model). Mean rank averages occupied positions
for ties. First-place counts include ties. These are preferences, not accuracy.

- Bilingual69 vs base: **18 wins / 2 ties / 15 losses**.
- Bilingual69 vs Turkish60: **21 wins / 3 ties / 11 losses**.
- Base vs Turkish60: **18 wins / 1 tie / 16 losses**.

The observed bilingual lead over base is small. A paired task bootstrap
(10,000 draws, seed3407) gives bilingual-minus-base net preference +8.6
percentage points, 95% percentile interval **[-22.9, +40.0]**. Against Turkish60
it is +28.6 points, interval **[-2.9, +57.1]**. These intervals include zero;
neither comparison establishes population superiority. The unit is 35 task
groups, not 140 independent language variants. Small category slices are
exploratory: bilingual leads semantic-role/negation preferences, whereas base
leads comprehension. No category preference is a correctness score.

## Correctness checks separate from preference

Manually inspected the final numeric answers of all 96 arithmetic word-problem
outputs against frozen references. These counts accept required numeric
value(s), independently of language, format, supporting reasoning and units.
They are deliberately **not full-answer correctness**. For the eggs task both
revenue and leftover quantity are required; incompatible final alternatives or
a truncated non-answer are not accepted. Per-item decisions and caveats are
preserved in `analysis/arithmetic-final-value-audit.json`.

| Candidate | TR→TR | EN→TR | TR→EN | EN→EN |
|---|---:|---:|---:|---:|
| Original base | 4/8 | 8/8 | 5/8 | 8/8 |
| Turkish60 | 3/8 | 7/8 | 3/8 | 7/8 |
| Bilingual69 | 4/8 | 6/8 | 6/8 | 8/8 |

Examples showing why numeric matches are insufficient:

- Ratio sharing: base and bilingual TR→TR give 252 while reversing who has
  the largest/smallest share.
- Raise then discount: several answers get 240 but claim that the changes
  cancel, or even that 240 equals 250.
- Tank filling: several answers end with 33 minutes while confusing seconds
  and minutes in their explanation.
- Bilingual eggs TR→TR writes **6 TL**, not 6 eggs, despite matching the numbers.
- Ticket change: every model fails both Turkish-input versions; all three
  solve the English-input versions (62). Translating the output requirement
  alone does not resolve the Turkish-input failure.

Eight separately reported symbolic arithmetic controls are especially important:

| Candidate | Correct final numeric value | Extraction failures | Value-only format |
|---|---:|---:|---:|
| Original base | **8/8** | 0 | 0/8 |
| Turkish60 | **0/8** | 0 | 6/8 |
| Bilingual69 | **0/8** | 0 | 7/8 |

All 24 outputs were inspected. Base explains its work despite the value-only
instruction; both SFT models mostly comply with the short format and give
wrong values. For example, `412 - 7 * 36` gives base160, Turkish60=276 and
bilingual69=276. This is a real final-value regression under this protocol,
not an extraction or formatting failure. It does not imply every kind of
arithmetic regressed: bilingual EN→EN word-problem final values remain 8/8.

## Stopping, length and thinking tags

All runs used the same frozen packet, native template, BF16 engine/packages,
seed and decoding. Thinking was disabled for all models; no output rewriting
or per-model protocol change occurred. Parent hashes and exact merge/reload
checks passed. All 444 outputs are nonempty and backed up locally.

| Candidate | 4096-token limit hits / 148 | Outputs with exposed thinking tags / 148 | TR→TR median tokens | EN→EN median tokens | Symbolic median tokens |
|---|---:|---:|---:|---:|---:|
| Base | 3 | 7 | 223 | 92 | 63.5 |
| Turkish60 | 0 | 26 | 42 | 74 | 2 |
| Bilingual69 | 0 | 1 | 46 | 37 | 2 |

Tag counts examine raw generated text for `<think>`, `</think>`, `<thinking>`
or `</thinking>`; normal terminal `<|im_end|>` is not an error. All SFT outputs
terminate at native EOS. This demonstrates better brevity/stopping and fewer
tag leaks for bilingual69, not production readiness or a proven training-tag
defect. Some base outputs still ramble or exhaust the length budget.

## Decision

**Keep bilingual69 as the leading SFT candidate, but do not call it a successful
general Turkish reasoning model or scale translations yet.** It improves some
preferences and language behavior; Turkish-input correctness remains weak,
and symbolic arithmetic is substantially worse than original base.

The arithmetic result also introduces a specific, post-hoc hypothesis worth
testing cheaply: SFT may have shifted the model toward immediate answers in
this thinking-disabled protocol. The symbolic answers shrink from a median
63.5 tokens to 2. That correlation does not prove that suppressed reasoning
caused the errors, and enabling thinking is not a promised fix.

Recommended next action is a small **inference-only reasoning-mode diagnostic**
for all three frozen candidates: change only native `enable_thinking` to true
on the eight symbolic controls and eight TR→TR arithmetic problems; retain
the existing off-mode outputs, numeric references, token budget and decoding.
Score correctness separately from length, formatting and visible thinking.
This reuses a consumed packet for diagnosis, not an independent final claim.
Register the diagnostic before generation; do not silently replace these results.
No new GPU run or training has been launched.

If reasoning mode does not recover the missing capability, the next causal
training test to consider is the same reviewed SFT recipe/data on **original
base vs CPT parent**, rather than adding thousands of rows. Both current SFT
candidates share the CPT parent, so these results cannot locate the regression
in CPT versus subsequent SFT. A CPT-only inference control could help locate
the stage without replacing original base as the main baseline.

Future tuning needs a new independent final holdout: this packet is consumed.
DPO remains deferred until correctness is acceptable. If a bounded diagnostic
does not justify further work, archive this pilot and prioritize Reflex-1.

## Reproduce local analysis

Run `export_lfm3_bilingual_final_review.py` to preserve a new immutable review
snapshot, then `analyze_lfm3_bilingual_final_review.py` for decoded preference
aggregation and `summarize_lfm3_bilingual_final.py` for generation diagnostics.
All are under `scripts/evaluation/`. Raw responses, private mappings,
per-item numeric adjudications and detailed results stay in the ignored
`final-eval-v01-local` directory. The verified GPU artifact receipt is
`BILINGUAL-FINAL-BACKUP.json`; no pod is required for this analysis.
