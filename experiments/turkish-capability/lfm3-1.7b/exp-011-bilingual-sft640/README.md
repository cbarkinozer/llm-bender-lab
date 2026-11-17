# exp-011-bilingual-sft640

## Status
Planned. Not run. No GPU pod, training, publication, commit or push. Blocked on UNRESOLVED-DECISIONS #1-#4 in `../bilingual-pilot-v01/`.

## Goal
Arm B: four-direction bilingual. Hypothesis test: does aligned bilingual task supervision improve Turkish understanding/output and output-language control versus Turkish-only supervision on the same tasks, without arithmetic/English/stopping regressions?

## Parent Experiment
exp-007-sft160-lr1e4 (recipe parent; its actual config was copied unchanged except the fields below).

## What Changed
Training data composition and (for B) update count, chosen to match supervised-token exposure. Same recipe on all 640 rows (tr-tr, en-tr, tr-en, en-en), 112 steps (1.4 epochs) to match supervised tokens (229,643, -0.35%). Checkpoints 69 and 112.

## Base Model
Pinned CPT merge: cbarkinozer/LFM3-1.7B-Turkish-CPT@6f213ec2 on LiquidAI/LFM3-1.7B@0dc4268b. Fresh LoRA, never resumed.

## Dataset
See `config.yaml` and `../bilingual-pilot-v01/README.md`. Plan: `../bilingual-pilot-v01/EXPERIMENT-PLAN.md`.

## Evaluation / Results / Regressions / Conclusion / Next Step
Pending (see EXPERIMENT-PLAN.md).
