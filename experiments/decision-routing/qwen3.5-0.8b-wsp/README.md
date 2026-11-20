# Reflex weight-space-programming comparison

Status (2026-11-20): Scope corrected by user to the four Reflex-1 routing-table benchmarks. Unrelated generation queue stopped; partial outputs preserved. Parent native routing baseline completed; WSP native baseline completed; corrected routing/training suite launched. No trained WSP candidate result yet. See [EXECUTION.md](EXECUTION.md).

Test whether the WSP backbone improves Reflex decision quality under the recovered original training recipe. A lower rate of long thinking loops need not improve decision-head routing; this is an empirical comparison.

## Execution order

1. Recover the exact published MOBILE_ROUTING9 180-case, typed-decisions 400-record/2000-decision, BANKING77 462-case and CLINC150 450-case cohorts and inference profiles. Evaluate WSP base on those tasks. Preserve the published table as historical evidence, with its distinct phone and general inference profiles explicitly labeled.
2. Train a fresh WSP-based Reflex-1.5 candidate using the recovered Reflex-1 mixture and recipe after baseline, finite-loss smoke, save/reload and tiny-overfit checks. Use validation for checkpoint selection and separate calibration data.
3. Evaluate the candidate and released Reflex-1 on the same routing cohorts under matched GPU conditions. Add WSP base and candidate columns to a local comparison table only when measured. A matched original-base training control can distinguish training-stack variation from the WSP effect.

MATH-500/GSM8K/IFEval are outside the corrected requested scope. The stopped run and its partial outputs remain diagnostic artifacts; do not resume its queue or require it before routing training. A newly initialized decision head is a diagnostic, not a generative zero-shot baseline. The historical general base reference used an unseeded fresh head, so it cannot be reproduced exactly; report a seeded matched parent/WSP pair separately where that profile is used.

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

Work root: /workspace/reflex-wsp. Evaluation and training environments are separate persistent venvs. The stopped run_card_suite.sh is retained as historical code and must not be resumed for this task. run_routing_suite.sh runs WSP/released native decision baselines, matched parent/WSP schema-based phone generation, a 4-bit delta gate, recovered two-step smoke, train-only tiny-overfit/reload checks, fresh WSP candidate training and its routing evaluation. It stops on any failure. run_card_eval.py saves every generated sample in atomic compressed batches and supports resuming completed batches. Batch scheduling and max_num_seqs differ from the upstream unbounded call and are held equal across arms; exact sampled strings need not match the author's hardware.

The scripts use the pinned upstream evaluation repository at /workspace/repos/lm_understand-logs. The unused missing loop-detector import is disabled explicitly; boxed extraction/math-verify remain upstream. IFEval uses pinned Google official checkers, with the author's rule that unfinished thinking has an empty answer. Preserve prepare.log and retry logs: the initial download attempt hit a missing upstream __init__.py, fixed by creating an empty package initializer. No training starts automatically from the benchmark shell script.
## Completed WSP experiment

The trained candidate is named **Reflex-1-WSP-experimental**, not Reflex-1.5. It regressed on three of four routing tasks; the CLINC150 gain is one case. Reflex-1 remains recommended. See [RESULTS.md](RESULTS.md). The publication-ready card is [model-card-updated.md](model-card-updated.md); authentication must be restored before uploading it. Preserve the original release weights.
