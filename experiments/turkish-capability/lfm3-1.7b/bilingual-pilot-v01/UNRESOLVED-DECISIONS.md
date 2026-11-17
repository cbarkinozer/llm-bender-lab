# Decision list (owner) - updated 2026-11-18

Training stays blocked: `plan/gates.json` is all false and `scripts/training/run_lfm3_bilingual_pilot.py --mode sft` refuses to start.

## Blocking
1. **Provider terms for translated rows - RESOLVED by owner decision 2026-11-18 (risk accepted; recorded in gates.json; not an Anthropic clearance).** (`TERMS-RESTRICTION.md`). Account = Free/Pro/Max/Ultra, so Consumer Terms s.3 item 2 (eff. 2025-10-08) applies. It is unclear whether it covers a research fine-tune of LFM3. Get written clarification from Anthropic/counsel, or replace the translations with human/permitted-source ones. Your approval alone does not clear it. Until then the 480 non-tr-tr rows and the translation files are RESTRICTED. Arm A (tr-tr only) contains no model-translated text and is not blocked by this.
2. **Source eligibility** - per-source missing evidence listed in `SOURCE-ELIGIBILITY.md` (no explicit restriction found for any source). Gate stays false until you record a decision (suggested wording in that file).

## Needs your call (each answer is cheap to apply)
3. **15 flagged originals**: `reports/CORRECTION-REPORT.md` has exact before/after text. Recommendation: FIX 9 (g153, g028, g068, g030, g139, g012, g095, g075, g154), RETAIN 6 (g035 and five legal-citation answers g066, g067, g102, g112, g159), DROP 0. g030 and g139 are verified against the official Constitution text. You decide; nothing applied.
4. (merged into 3; g035 recommended RETAIN because the answer itself flags the ambiguity.)
5. **Empty-think masking - RESOLVED 2026-11-18: keep exp-007 parity, no masking.** The pilot only translates existing reasoning and leaves blank thinking blank (no reasoning invented). Audit note retained for the record:  (audit finding in `plan/audit-*.json`): direct-answer targets start with a supervised `<think></think>` (2 tokens, 0.5% of tokens) although inference already supplies it; plausible cause of the `</think>` leakage. Default keeps exp-007 parity; `--mask-empty-think` is a recipe change for both arms.
6. **g111** has topical overlap with four TQuAD items (Müteferrika's press; no shared task or answer). Keep (default) or drop for a conservative CETVEL comparison.
7. **Arm A form**: tr-tr rows with "Yanıtını Türkçe ver." (default, both arms carry instructions) vs exp-007's exact no-instruction rows as an extra control.
8. **EN system prompt wording** (drops "Turkish"); ASCII-folded Turkish prompts (g011, g098, g131) lose their noise in EN input.
9. **Translation review depth**: inspect `inspection/STRATIFIED-SAMPLE.md` (17 groups); a 5%-error audit needs >= 59 groups.
10. **Evaluation**: scoring method for eval-v01 (scripted key-fact checks vs owner blind ranking); pick a licence-checked English retention benchmark; confirm eval-v01 is scored once, never used to select checkpoints.
11. **Optional B control at exactly 100 steps** (-12% tokens).

## Recorded as unchecked, not passed
TurBLiMP1600 leakage (data not available locally); CETVEL items outside the 500-item audit file; GPU-environment native label audit, smoke, tiny-overfit.
