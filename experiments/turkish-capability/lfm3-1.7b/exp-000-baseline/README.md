> Current status (2026-11-12): baseline complete and123-file recovery verified; no CPT has run. Owner approved preparation of two separate CPT experiments; follow ../CPT-PAIR-TODO-20261112.md. W&B is training-only; older preparation/off/evaluation-upload notes below are historical. The executed baseline uses pinned vLLM nightly, not the initial Transformers candidate.

# exp-000-baseline

## Status

Preparing data and evaluation only. No weights downloaded, inference performed, training started, or GPU booked. `config-planned.json` is provisional, not a runnable/frozen protocol.

## Goal

Measure the unchanged post-trained LFM3-1.7B and establish headroom before four independent training recipes. No training occurs in this experiment.

## Sources and evidence

Model and four candidate dataset revisions are pinned in `config-planned.json`. `source-inspection-v01.json` records full-table language counts, file hashes, and basic TurBLiMP pair checks. Reproduce from the repository root:

```powershell
python scripts/datasets/inspect_lfm3_sources.py --config experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json --output experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/source-inspection-v01.json
```

Inspection requires pyarrow and downloads source parquet files to memory without executing dataset/model code. Only counts, metadata, and invalid-pair IDs are saved. It does not certify semantics, legal permission, or cross-split independence.

Full-table inspection on 2026-11-09 found zero Turkish-language rows across all splits of structured-extraction (6,806 rows), grounded-qa (4,880), and phone-assistant-tools (3,307). Across 16,000 TurBLiMP pairs, 20 have identical normalized good/bad sentences; there are also 831 duplicate-pair excess occurrences summed within files (these counts can overlap). Duplicate detection preserves sentence case and uses NFC/whitespace normalization. These findings require an exclusion/group policy before sampling; no evaluation packet has been selected yet.

The three LiquidAI task dataset cards list 16 languages without Turkish, with license `other` and no explicit grant in the inspected README. Resolve actual reuse/translation terms before using their content to construct datasets. They are candidates, not approved Turkish training/evaluation data. Alternative: original reviewed Turkish data with explicit provenance. Any synthetic provider terms must be verified before generation.

## Proposed common evaluation

| Capability | Candidate source | Initial target | Scoring |
|---|---|---|---|
| Grammar | juletxara/turblimp, evaluation only | 100 usable pairs per phenomenon (16) | Total sentence log-probability preference; per-phenomenon and macro scores |
| Turkish text | Wikimedia Wikipedia 20231101.tr | 100 reserved articles | Corpus token-weighted NLL and perplexity |
| Other text registers | FineWeb-2 tur_Latn | 100 reserved pages | Same NLL protocol |
| Extraction | Reviewed Turkish examples; source unresolved | 200 | Schema validity, strict exact match, field score |
| Grounded QA | Reviewed Turkish examples; source unresolved | 200, balanced answerability | Answer accuracy, correct refusal, unnecessary refusal |
| Tools | Reviewed Turkish examples; source unresolved | 200 | Verified tool names/arguments; separate clarification/no-tool correctness |
| English regression | Rights-cleared task subset | 100 | Same task scorers |

Counts are proposals, not downloaded/frozen packets. Raw-text source revisions are pending. Treat public datasets as potentially pretrained-on, not guaranteed unseen. Distinguish task generalization from broad Turkish proficiency.

## Preparation checklist

- [x] Create separate model track; pin model and inspected dataset revisions.
- [x] Implement source-table inventory and pair sanity checker.
- [ ] Review source inspection results, reuse terms, and Turkish task-data strategy.
- [ ] Audit TurBLiMP invalid/duplicate pairs; freeze exclusions independent of model scores. Preserve the full exclusion accounting. Do not treat automatic checks as linguistic validation.
- [ ] Build separate development/final evaluation packets with stable IDs and hashes. Split related documents, translated variants, entities/templates and duplicate groups together where applicable. Never train on benchmark content or derivatives.
- [ ] Freeze corpus revisions, document splits, length handling and cross-source duplicate checks. Use disjoint windows with explicit context policy and token-weighted loss, not mean batch perplexity.
- [ ] Validate scorers with correct/wrong/malformed/missing/extra outputs. Check Turkish dotted/dotless-I normalization; do not silently fold distinct strings.
- [ ] Resolve all runtime versions; inspect pinned remote modeling code before executing it. The notebook's package pins are candidates until import/load tests pass.
- [ ] Freeze official chat template, non-thinking mode initially, decoding, per-task output budgets and token handling. Log length stops and repetitions. Raw-text likelihood uses no chat wrapper.
- [ ] Save a separate diagnostic development set. Final results must not guide data/hyperparameter edits; version any prospective protocol change.
- [ ] Prepare a 4090 smoke test, measure memory/throughput, estimate cost and then request GPU access.
- [ ] Run unchanged-model baseline; save raw outputs, per-item scores, termination, timings, memory, environment, W&B IDs and verified local backup.

## Planned training data after baseline

2. SFT: reviewed Turkish document/schema/JSON pairs; completion-only labels checked after tokenization.
1. CPT: cleaned Turkish Wikipedia training articles, initially 3,000 subject to actual token count; whole-document separation from all evaluation text.
3. DPO: reviewed Turkish grounded-QA prompt/chosen/rejected pairs. Use pure sigmoid DPO for the initial recipe; cookbook DPO also adds SFT loss and must not be mislabeled.
4. GRPO: Turkish requests, small fixed tool catalog, verified gold calls and independently tested rewards. Empty calls alone cannot establish correct clarification or a correct direct answer. Report rollout-token cost and reward/held-out-metric divergence.

Each training arm starts from the original pinned model. Run the entire frozen suite on every checkpoint, not only its trained task. Training hyperparameters, seeds, lengths, counts and compute budgets are not yet approved/frozen. Track training versus evaluation costs separately; equal epochs are not equal compute.

## Results and next step

No model scores yet. Finish data feasibility and scoring before inference. Do not publish hypothetical gains or GPU runtime as measured results.

## CETVEL reuse update, 2026-11-11

Owner selected CPT first, then SFT, DPO and GRPO. Each arm still starts independently from the original model. The existing extraction/tool data proposals do not block the first CETVEL baseline.

Restored historical exp003 cohort: 500 rows, 100 per task; exact historical packet SHA256 verified. Receipt: `cetvel-restoration-v01.json`. Source text remains ignored in `data-local/`; the external source cache is outside Git. This cohort was previously inspected and is comparison/development evidence, not a pristine final test. Preserve it from training, including translated/paraphrased derivatives.

Historical comparator is **unsloth/Qwen3.5-4B**, revision `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`, without Occam adapter. Its completed manifest, not the stale prepared-status config, establishes completion. Actual raw Qwen outputs are absent from this checkout; recover them before any paired per-item analysis. Aggregate results alone cannot establish paired differences.

New runner: `scripts/evaluation/evaluate_lfm3_cetvel.py`. Sequential Transformers, BF16, native chat template, thinking disabled, greedy, repetition penalty 1.05, 4096 output and 8192 context budget. These match historical semantic settings; different tokenizer/backend/model sizes prevent bitwise parity and directly comparable perplexities. Do not copy Qwen EOS IDs. Custom code review, native-template inspection, dependency/load validation and diagnostic scorer validation remain pending. Runner has only CPU syntax validation so far, not GPU validation. It records partial progress on failure and does not retry or truncate inputs. It records EOS/length, exact repeated-token blocks and a cooperative 180-second per-item guard. Guard checks run between generation steps and cannot interrupt a hung CUDA kernel. Guards require diagnostic GPU validation; broader semantic repetition still needs inspection.

Restore command:

```powershell
python scripts/datasets/restore_cetvel_comparison.py --cache-root C:/Users/barkin/.cache/llm-bender/cetvel --output-dir experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/data-local
```

Next: review pinned remote Python and chat template; validate output-field compatibility with existing CPU scorers; validate termination safeguards; resolve/pin runtime; validate tokenizer lengths on all 500 rows before requesting GPU. Use a separate diagnostic subset for debugging, not this cohort to tune prompts. No training, model-weight download or GPU inference has occurred.

## Active preparation outcome, 2026-11-11

This section supersedes earlier pending-data notes. CPU preparation is complete for the first baseline/CPT pair. No actual-model scores, GPU inference or training exist yet.

- CETVEL:500 rows, historical exact file SHA verified; five task scorers passed positive/invalid-output controls on100 rows each.
- Native LFM3 tokenizer: all500 fit8192 context with4096 output; max3490 input tokens, mean250.084, population standard deviation330.153.
- TurBLiMP:1600 cleaned evaluation pairs,100 per file;20 identical pairs and830 remaining duplicate-pair occurrences excluded globally. This differs from the earlier831 within-file duplicate count because identical-pair exclusions are applied first. See full exclusion IDs in `turblimp-manifest-v01.json`.
- Active CPT data is **v02**, not v01:3000 Wikipedia training articles,100 Wikipedia dev,100 Wikipedia eval and100 FineWeb eval. v02 adds protection against the selected TurBLiMP sentences. v01 is retained as superseded preparation, never an alternate training arm.
- Pinned Wikipedia/FineWeb files total about606MB and are cached outside Git; selected source text stays in ignored `data-local/`. Filters and overlap checks reduce risk; they do not certify semantic independence or balanced subject domains.
- `cpu-preflight-v01.json` confirms pinned tiny architecture forward/generation and scorer schema. `training-cpu-preflight-v01.json` confirms TRL wrapped packing, all-token labels and38 nonempty LoRA gradient tensors on a random tiny model. Actual-model GPU checks remain mandatory.
- `source-runtime-review-v01.json` records model-code hashes, inspection scope, licenses and the failed old-Transformers probe. Candidate GPU dependencies, setup and commands are in `GPU-RUNBOOK.md`.

Raw token exposure and split integrity are in `cpt-token-profile-v02.json`. GPU gate flags must be written from observed results and bound to the active model/data manifest; do not prefill success. Training script supports separate smoke and tiny-overfit modes and starts each from the original checkpoint.

Do not infer a Turkish gain from Wikipedia training loss alone. Compare Wikipedia/Web NLL, grammar preference and task metrics separately. Do not compare Qwen/LFM3 perplexity directly across tokenizers. Source-specific public publication remains separate from private experimental use.
# Current training plan, 2026-11-12

Baseline results above remain historical. Owner approved two NEW independent CPT
experiments: exp-001-wiki-cpt (existing 2.202M Wikipedia) and exp-002-mixed-cpt
(10M total, same Wiki plus official FineWeb2 train). Follow
[the current pair checklist](../CPT-PAIR-TODO-20261112.md), not older training
commands targeting this baseline directory. No CPT has run yet.
