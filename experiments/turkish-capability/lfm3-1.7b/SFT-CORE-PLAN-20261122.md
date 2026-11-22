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
- [x] B2 Base model sampled (2026-11-22): 1,600 English prompts k=4, Dolly 300 k=4, Atlas 500 k=8, then 1,000 Turkish math
      problems and the 100-item final test in both languages k=4 (thinking on, 8,192 tokens).
- [x] B3 Verification rates (any verified sample per group, thinking on): math EN .96 / TR .79, code .89, tools .98, Dolly 1.0,
      Atlas .96; thinking off is weaker (code .60, TR math .61). Natural lengths are the drift baseline of exp-019.

Phase C: Turkish prompts (needs the owner's translations)
- [x] C1 Worksheets filled (math train 1,000, final test 100, wrappers 8) by OpenAI Codex, AI-reviewed (not owner-reviewed);
      the 300 MBPP and 300 tool one-liners are still empty (deferred), see `sft-core-v01/DATASET-CARD.md`.
- [x] C2 Validated independently: 0 errors in the delivered sheets. Found c-mathtest-0068 (meaning-changing translation) and
      three items with English thousands format (read as decimals in Turkish): recorded as a sensitivity subset, data unchanged.
- [x] C3 Sampled on the Turkish prompts (see B2). The fallback with the English twin's answer was dropped: it would teach
      Turkish prompt -> English reply.

Phase D: build the pack
- [x] D1 Pack built: 2,909 rows (tr->tr, en->en only; no cross-language rows in v1), thinking on 81.5%.
- [x] D2 Trainer audits on all rows: prompt masked, EOS supervised, no truncation (max 7,935 tokens), tool names in the prompt.
      Not done: duplicates/overlap check of Atlas and Dolly against the eval sets.
- [x] D3 Length drift 1.00 to 1.06 on most cells, 1.14 for Turkish math (kept answers longer), the opposite of exp-016.
- [ ] D4 60-row stratified review of the Atlas rows (owner reads) and the 40-answer blind sheet
      (`exp-019-sft-core-pack/results/writing-review/`, naturalness and task scored apart).

Phase E: training and evaluation
- [x] E1 exp-019: CPT-merged parent + LFM3 pack, one seed (364 steps, 17.6 min). See `exp-019-sft-core-pack/README.md`.
- [ ] E2 exp-020: same data on the original LFM3, running on the pod (shows how much the dataset carries without our CPT).
- [x] E3 Gates G1 to G7 of exp-019 (thinking on): all pass (Turkish math reading .752 vs base .691 and arm B .612).
- [x] E4 Fresh test, 100 GSM8K test items, AI-reviewed translations (not owner-checked): Turkish .770 vs base .7625, English .930
      vs .9375, no difference. The never-solved items were not scored separately.
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
