# Reusable SFT core + per-model answer packs: plan and to-do (2026-11-22)

Status: in progress. Supersedes the "Phase 2" section of [SELF-DISTILL-PLAN-20261121.md](SELF-DISTILL-PLAN-20261121.md) and
narrows the 2026-11-14 corpus design ([docs/turkish-sft-corpus-design-v01.md](../../../docs/turkish-sft-corpus-design-v01.md))
for this round. Findings behind it: [exp-016](exp-016-self-distill-targets/README.md),
[exp-017](exp-017-understanding-diagnostic/README.md), [exp-018](exp-018-english-guard/README.md).

## Goal

A decent, not over-engineered SFT dataset that (1) teaches LFM3-1.7B better Turkish reading while English, math, coding,
tool calling and instruction following stay level, and (2) can be reused as the starting point for the owner's MoE and
text-diffusion experiments.

## Design (decided 2026-11-22)

- **Core (model-independent, reusable):** prompt groups with EN/TR twins, a checker per group (gold number, unit tests, gold
  tool call, constraint code), source id, license, split, and where it exists a human-written reference solution.
- **Pack (per model, regenerated):** that model's own answers. LFM3's own answers must not be fed to another architecture
  (that is the exp-010 to exp-015 failure again).
- **Why the targets change from exp-016 (hypothesis, fits the logs):** exp-016 trained Turkish prompts on reasoning written
  for the English prompt, kept the shortest sample and dropped answers over 1,500 characters. The base spends about 3x more
  thinking on Turkish math than on English (median 1,581 vs 553 tokens); arm B cut that to 957. New rule: the reasoning for a
  Turkish prompt comes from the model reading the Turkish prompt; keep a random verified sample, not the shortest; no length cap.
- **Mix (2,500 core groups, built 2026-11-22):** math 1,000 (GSM8K train), code 300 (MBPP train/validation), tool calls 300
  (glaive function calling v2), English general replay 300 (Dolly, natural answer lengths), Turkish general 500 (native Atlas
  tasks: 250 with countable constraints, 150 with a context, 100 plain), plus the 100-item math final test. English twins serve
  as replay. Changes against the first plan: the constraint rows come from Atlas (native Turkish word/bullet/sentence/JSON limits,
  checked by code) instead of IFEval-style synthesis, English long-answer replay comes from Dolly, and EN<->TR translation rows
  (planned 200) are deferred until the owner's one-liners exist. See [sft-core-v01/README.md](sft-core-v01/README.md).
- **Review policy:** checkers for the verifiable groups; a 60-row stratified review for each category without a checker (59
  rows see a 5% error rate with 95% probability, dataset guide section 25); no Argilla, no review of every row. No text
  written by Claude enters the core (consumer-terms issue, see `bilingual-pilot-v01/TERMS-RESTRICTION.md`).

## To-do

Phase A: sources, English prompt lists, worksheets (CPU only)
- [x] A1 Write this plan.
- [x] A2 Pin source revisions and record licenses (`sft-core-v01/build-manifest.json`): GSM8K, MBPP, glaive, Dolly, Atlas,
      HumanEval and BFCL (eval side).
- [x] A3 English prompt lists with stable ids, fixed seed: GSM8K train 1,000, GSM8K test 100 (final holdout), MBPP 300,
      glaive 300, Dolly 300, Atlas 500 (`prompts-en.jsonl`, 2,500 rows).
- [x] A4 Overlap checks: GSM8K train vs the 152 eval-v2 items and the 100 holdout (0 exact, 0 near); MBPP vs HumanEval (10
      tasks removed); glaive vs BFCL (function names and queries, 3,072 removed). Not done: a cross-lingual check of the Turkish
      rows against Cetvel/Belebele, and the training-vs-eval overlap for Atlas and Dolly.
- [x] A5 Constraint rows: reframed. 250 Atlas prompts carry countable constraints (179 word limits, 96 bullet counts, 23
      sentence limits, 2 JSON) checked by `lfm3_sft_constraints.py`. IFEval-style English synthesis and the held-out
      constraint types were dropped to keep the dataset simple; English long-answer replay (Dolly) addresses the length
      hypothesis instead. Constraints the parser does not recognise (for example "tam olarak 3 adım") are not checked.
- [x] A6 Translation worksheets for the owner (`sft-core-v01/worksheets/`, instructions in its README) and the validator
      (`validate_lfm3_sft_core_translations.py`, tested on deliberately broken fake sheets).

Phase B: English-side sampling on the pod (needs the GPU, not the translations)
- [x] B1 Sampler (`generate_lfm3_sft_samples.py`, resumable, k per category), verifier (`verify_lfm3_sft_samples.py`, oracle-tested
      on math, tool calls and MBPP references 300/300) and pod driver.
- [ ] B2 Run on the pod for the base model (started 2026-11-22 15:46Z: 1,600 English prompts k=4, then Dolly 300 k=4 and Atlas
      500 k=8 chained automatically).
- [ ] B3 Report: verification rate per category, natural length distribution (the reference for the length-drift check).

Phase C: Turkish prompts (needs the owner's translations)
- [ ] C1 Owner fills the worksheets: 1,000 GSM8K train and 100 GSM8K test (checked by the owner), 8 wrapper templates, 300 MBPP
      task sentences and 300 tool-query one-liners. The first experiment can start with the math sheets plus the wrappers.
- [ ] C2 Import + validate the translations (digits, names, code, JSON identical).
- [ ] C3 Sample the model on the Turkish prompts (k=4+, thinking on); keep a random verified sample; fallback is the
      model's correct answer to the English twin paired with the Turkish prompt (counted and reported).

Phase D: build the pack
- [ ] D1 Assemble rows (tr->tr, tr->en, en->tr, en->en replay, long-answer and constraint rows) with native chat template.
- [ ] D2 Validation report: token counts, trainable tokens, truncation, EOS, masks, duplicates, overlap with eval sets.
- [ ] D3 Length-drift check: kept-answer lengths against the natural lengths (B3). A shift is a stop signal.
- [ ] D4 60-row stratified review for the categories without a checker (owner reads).

Phase E: training and evaluation
- [ ] E1 exp-019: CPT-merged parent + LFM3 pack, exp-016 LoRA recipe. One seed.
- [ ] E2 exp-020: same data on the original LFM3 (shows how much Turkish the dataset carries without our CPT).
- [ ] E3 Gates for exp-019 (thinking on): Turkish math >= .69 (base); Belebele TR >= .45; TurBLiMP >= .85; >= 98% Turkish
      replies to Turkish prompts; English guard (IFEval, HumanEval, English math, tools) within the exp-018 rule.
- [ ] E4 Fresh test: the 100 owner-checked GSM8K test items, used once. Also score the items the base never solved separately.
- [ ] E5 Second seed for the winner; native 40-answer writing rating (naturalness and correctness separate).

Phase F: release (each needs explicit approval)
- [ ] F1 Publish core dataset (licenses, provenance, card) and model (base-first names), after re-checking provider terms.
- [ ] F2 Decide on more Turkish pretraining text only if E5 shows word-meaning errors remain.

## Threats to validity (tracked)

1. The 152 eval math items and Belebele are development data now; the final verdict uses the fresh 100 (E4).
2. Training translations (owner) differ from eval translations (machine); test on both.
3. Selection bias toward problems the model already reads; report the never-solved items separately.
4. Answer-length drift (D3).
5. Teaching to the guard: hold out a third of the constraint types, dedupe MBPP vs HumanEval and glaive vs BFCL.
6. One training seed until E5.
7. Licensing: re-check arm B's Claude-written Turkish targets, the owner's translation tool terms and the LFM license before publishing.
8. Word-meaning errors need pretraining text, not SFT; decide after E5.
