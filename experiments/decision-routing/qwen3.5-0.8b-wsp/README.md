# Reflex weight-space-programming comparison

Status (2026-11-20): GPU environments prepared; WSP generation smoke passed; model-card evaluation queue launched. No fine-tuning or completed benchmark comparison yet. See [EXECUTION.md](EXECUTION.md).

Test whether the WSP backbone improves Reflex decision quality under the recovered original training recipe. A lower rate of long thinking loops need not improve decision-head routing; this is an empirical comparison.

## Execution order

1. Evaluate untouched WSP and the original Qwen parent on MATH-500, GSM8K and IFEval using the author's think35 protocol. Preserve four samples per MATH-500 problem, two per GSM8K/IFEval prompt, thinking enabled, temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5, 32,768-token cap, seed 0 and BF16. Strict math grading and IFEval prompt-level grading remain primary.
2. Train fresh WSP and original-base decision models using the same recovered mixture, recipe and seed, after baseline, smoke/save-reload and tiny-overfit gates pass. Select by equal-domain validation; do not force checkpoint 100.
3. Compare both trained arms with released Reflex-1 on frozen routing cohorts and inference examples. Measure generative retention where supported. An untrained random decision head is an initialization diagnostic only.

## Pinned artifacts

- Original training base: unsloth/Qwen3.5-0.8B at 23c69c53358a07516b5827588b3fdb12ae78fd65.
- WSP parent: Qwen/Qwen3.5-0.8B at 2fc06364715b967f1860aea9cf38778875588b17.
- WSP: RikiyaT/Qwen3.5-0.8B-weight-space-programming at d1671a178705bcab7644806d23c535517f35723b.
- Released Reflex-1: cbarkinozer/Reflex-1 at 252a00c22cebca07c7ff4d6f99be15863c7faab2.

The sources directory preserves revision-pinned upstream cards/configs and hashes. These are historical claims, not measurements. The preflight directory records benchmark revisions, environment freezes, recovered mixture and tensor audits. The original Unsloth and official parent snapshots have identical tensor keys and values; The tokenizer metadata differs; matched training uses the original metadata for both arms, recorded in preflight/training-view-manifest.json. WSP differs in exactly the two advertised MLP tensors, with matching published hashes.

## Recovered recipe

Original data inputs are in datasets/reflex-1 (recovery commit 675e0334e82b6058c15b6b6c9af19955f589c714). All recovered file hashes verified locally and on the GPU. The recovered pocket-agents-lab tools/train_combined_routing.py reproduces 1,562 ordered rows: 781 phone, 391 typed-decisions, 195 BANKING77 and 195 CLINC150. Its materialized SHA-256 is recorded in preflight/training-mix-manifest.json. The 2,240-row general training file is the sampling pool, not the final mixture.

Rank/alpha 16, dropout 0, seed 3407, LR 2e-4, microbatch 2 with accumulation 16, sequence length 4096, 120 optimizer steps, 4-bit loading, BF16 computation, adamw_8bit, cosine schedule, warmup 10, weight decay 0.01. Evaluate/save every 20 steps and select highest equal mean of phone/general validation accuracy. Original release selected checkpoint 100. Fit calibration only on the independent calibration partition. Preserve the joint decision head along with LoRA.

The archived phone test contains 88 rows and differs from the separately frozen 180-case release regression cohort. Existing published tests are regression cohorts; never use them for checkpoint selection. The recovered log named combined-balanced-scratch-full.log ends at step 80, so it does not establish a complete original 120-step execution trace.

## Evaluation and release

Keep schemas, options, cohort IDs/order, runtime, precision and hardware matched. Report phone accuracy/macro-F1 and per-route recall, typed-decisions exact-record/per-question accuracy, BANKING77 and CLINC150 metrics, calibration, errors, truncations and resource use. Separate generation and decision-head results. GPU timings cannot be compared directly with historical A32 timings.

No improvement or Reflex-1.5 release claim is established. Retain per-item outputs, report paired uncertainty, and use independent final data before a release decision.

## Remote operation

Work root: /workspace/reflex-wsp. Evaluation and training environments are separate persistent venvs. run_card_suite.sh serializes parent smoke, WSP benchmarks and parent benchmarks using a lock; it stops on failure. run_card_eval.py saves every generated sample in atomic compressed batches and supports resuming completed batches. Batch scheduling and max_num_seqs differ from the upstream unbounded call and are held equal across arms; exact sampled strings need not match the author's hardware.

The scripts use the pinned upstream evaluation repository at /workspace/repos/lm_understand-logs. The unused missing loop-detector import is disabled explicitly; boxed extraction/math-verify remain upstream. IFEval uses pinned Google official checkers, with the author's rule that unfinished thinking has an empty answer. Preserve prepare.log and retry logs: the initial download attempt hit a missing upstream __init__.py, fixed by creating an empty package initializer. No training starts automatically from the benchmark shell script.