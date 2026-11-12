# exp-004-cpt-cont-100m

Continuation from experiments/turkish-capability/lfm3-1.7b/exp-003-cpt-cont-50m. Fresh phase-local AdamW/cosine schedule, peak LR1e-4, warmup5%, rank64; embeddings frozen.
Milestones are nominal cumulative raw-token budgets; exact raw and EOS/packed exposure are recorded.
New FineWeb prose only, no parent-corpus replay. Not an uninterrupted100M run.
Resumable checkpoints every200 optimizer updates, keep last2. No automatic time limit.
Inference postponed by owner; no benchmark run is scheduled.

Training completed; W&B run: https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/311vl5n7. Full results/optimizer states are in results-local/cpt-v01. Inference pending.
