# exp-010-tr-only-sft160

## Status
Planned. Not run. No GPU pod, training, publication, commit or push. Blocked on UNRESOLVED-DECISIONS #1-#4 in `../bilingual-pilot-v01/`.

## Goal
Arm A: Turkish-only. Hypothesis test: does aligned bilingual task supervision improve Turkish understanding/output and output-language control versus Turkish-only supervision on the same tasks, without arithmetic/English/stopping regressions?

## Parent Experiment
exp-007-sft160-lr1e4 (recipe parent; its actual config was copied unchanged except the fields below).

## What Changed
Training data composition and (for B) update count, chosen to match supervised-token exposure. Fresh LoRA (r32/alpha64, LR 1e-4, 100 cosine steps, 6 warmup, batch 8) on the 160 `tr-tr` rows (reviewed originals + "Yanıtını Türkçe ver."). 230,440 supervised tokens.

## Base Model
Pinned CPT merge: cbarkinozer/LFM3-1.7B-Turkish-CPT@6f213ec2 on LiquidAI/LFM3-1.7B@0dc4268b. Fresh LoRA, never resumed.

## Dataset
See `config.yaml` and `../bilingual-pilot-v01/README.md`. Plan: `../bilingual-pilot-v01/EXPERIMENT-PLAN.md`.

## Evaluation / Results / Regressions / Conclusion / Next Step
Pending (see EXPERIMENT-PLAN.md).
