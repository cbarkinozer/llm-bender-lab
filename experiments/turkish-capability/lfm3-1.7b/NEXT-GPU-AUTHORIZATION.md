# Next GPU session — owner authorization, 2026-11-19

The owner explicitly authorized all three experiments in one GPU session:

1. Thinking-enabled inference on the frozen candidates, compared with saved
   thinking-disabled diagnostics.
2. Matched bilingual SFT on original LiquidAI/LFM3-1.7B, compared with the
   existing CPT-parent bilingual candidate.
3. A small capability-preservation SFT pilot with verified arithmetic/reasoning
   and English retention examples.

This supersedes earlier wording that experiments 2 and 3 require another
owner decision before proceeding. Routine recipe/data preparation, validation,
smoke tests, inference and artifact backup are within this authorization.
Freeze the concrete recipes and fresh evaluation before running; preserve
experiment controls and keep consumed test tasks out of training. Do not
skip checks to fit an unrealistic one-minute estimate.

Owner's release objective: useful Turkish with measured and acceptable losses
elsewhere, clearly disclosed in the model card. Do not promise absence of
overfitting or catastrophic forgetting before measuring it. Publication itself
has not been requested in this message.

Use the existing local instance key first. Public key can be shared with the
owner; private key remains outside the repository. New SSH endpoint pending.
Download adapters and all necessary small logs/results/manifests after the
session; do not download full weights. Notify the owner once the pod can close.
