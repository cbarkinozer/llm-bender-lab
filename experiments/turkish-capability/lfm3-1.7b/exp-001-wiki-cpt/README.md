# exp-001-wiki-cpt

Status: training complete; matched fast100 screening complete. GPU smoke,
packed labels, LoRA gradients and tiny-overfit gates passed.

Parent/comparison: exp-000-baseline. Start independently from the pinned original
LiquidAI/LFM3-1.7B; never continue from the other CPT adapter.

Hypothesis: 2.202M clean Wikipedia tokens improve held-out Turkish language modeling.

Complete recipe: config.yaml, byte-identical to runner input config-planned.json.
Shared implementation: scripts/training/train_lfm3_cpt.py. This first recipe keeps
embeddings frozen, one epoch, rank64, LR2e-4, raw-text all-token loss, 2048 packing.

Evaluate final epoch against the existing baseline with the frozen protocol.
Report NLL separately by source, grammar, each task score, answer lengths and
termination. No pooled score, no English preservation claim, no automatic selection.
The pair changes quantity and source composition, not a causal source-only ablation.

Results: independent one-epoch training completed in 5.82 minutes.
W&B confirms a finished run and committed adapter. Original sequential evaluation
was interrupted by the owner; use fast100-v02 for matched generation results.
Frozen prospective configs are preserved; actual training details are in
results-local/cpt-v01/training-manifest.json. See ../CPT-PAIR-TODO-20261112.md for launch and recovery.
