# Reflex weight-space-programming comparison

Status: planned. No model evaluation or training has started.

Test whether the WSP backbone improves Reflex decision quality under the original training recipe. The user will provide a Vast.ai GPU; the exact original data/trainer backup is on their Mac mini or laptop.

## Comparison

1. Untouched original Qwen and untouched WSP: same generative decision prompts and runtime. This measures usefulness before training.
2. Released Reflex-1: restore its original backbone, adapter and decision head as a reference.
3. Fresh WSP decision model: train fresh LoRA and decision head on exactly the original mixture and recipe. Never attach the old adapter as a substitute for retraining.
4. A fresh original-base training control, using the same stack and seed, is needed to attribute any training gain to the starting weights rather than environment differences. Compare the WSP checkpoint with both this control and released Reflex-1.

An untrained random decision head is only an initialization diagnostic, not a useful zero-shot baseline. The WSP card reports reduced long-thinking loops; decision scoring does not generate those chains, so transfer is an empirical question.

## Artifacts and provenance

The sources directory contains revision-pinned upstream cards, model/adapter configs, routing schema and release manifest. sources/manifest.json records URLs and SHA-256 hashes. Source claims are historical evidence, not measurements from this experiment.

Original base: unsloth/Qwen3.5-0.8B at 23c69c53358a07516b5827588b3fdb12ae78fd65.
WSP: RikiyaT/Qwen3.5-0.8B-weight-space-programming at d1671a178705bcab7644806d23c535517f35723b.
WSP parent: Qwen/Qwen3.5-0.8B at 2fc06364715b967f1860aea9cf38778875588b17.
Released Reflex-1: cbarkinozer/Reflex-1 at 252a00c22cebca07c7ff4d6f99be15863c7faab2.

Audit original Unsloth versus official parent weights/tokenizer before calling this an edit-only ablation. Their configuration metadata differs; matching architecture is insufficient evidence of identical weights.

## Original recipe to recover

Released recipe: 1,562 training rows: 781 phone + 391 typed-decisions + 195 BANKING77 + 195 CLINC150. Rank/alpha 16, seed 3407, base LR 2e-4, effective batch 32, max sequence 4096, 120 optimizer steps. Original selected artifact: combined-balanced-scratch-120step-s3407/checkpoint-100. W&B run 66wubl55.

Recover exact row order, split files, source hashes, trainer, executed config, decision-head LR, optimizer/scheduler/warmup/precision, microbatch/accumulation, validation cadence/selection and calibration procedure. Public phone data alone cannot reconstruct the exact general mixture. config.json nulls are unresolved facts and must be recovered before execution. JSON is used as the explicit experiment config format.

## Evaluation and release

Use identical frozen schemas, options, cohort IDs and runtime/precision/hardware within each comparison. Measure phone accuracy/macro-F1 and per-route recall; retain general typed-decisions/BANKING77/CLINC150 scores, probabilities, calibration, errors, truncations and resource measurements. Separate generative baseline tables from decision-head tables. Historical A32 scores are context; GPU timings cannot be compared with them.

Select checkpoints using original equal-domain validation procedure; do not force checkpoint 100. Calibrate only on the independent calibration split. Existing published tests are regression cohorts. Define regression tolerances before running; preserve per-item outputs and report paired bootstrap intervals. New independent final data and deployment checks are required before a Reflex-1.5 release claim. No improvement has been measured yet.

## Next action

Recover experiments/unsloth-qwen35-08b-decision from Mac mini or laptop, including scripts, original JSONL datasets, configs and small manifests/results. Preserve existing checkpoints on that machine; no need to transfer large model weights initially. Once Vast SSH is supplied, inspect GPU and persistent disk, recover/pin the runtime, verify loading/edit tensors, then pass matched baselines, data audits, smoke/save-reload and tiny-overfit gates before production training.

## Recovery update

Commit 675e0334e82b6058c15b6b6c9af19955f589c714 recovered original data inputs and launch_combined_120.sh. All 11 recovery-manifest file hashes, byte counts and declared row counts verified locally. Phone input has 781 training rows; general input is the 2,240-row pool from which 781 were sampled. Exact sample selection/order still requires tools/train_combined_routing.py from the backup. Launch confirms microbatch 2 and accumulation 16. The archived phone test has 88 rows and must not be mistaken for the separately frozen 180-case release regression cohort.

Original backup: C:/Users/barkin/Documents/GitHub/pocket-agents-lab/runs/decision-followups-vast-20261013/reflex-decision-artifacts-20261013.tar.gz. Request archive members reflex-decision/tools/, trainer local dependencies, sanitized executed run configs/environment records, and logs/combined-balanced-scratch-full.log. Exclude .env, tokens and credentials.
