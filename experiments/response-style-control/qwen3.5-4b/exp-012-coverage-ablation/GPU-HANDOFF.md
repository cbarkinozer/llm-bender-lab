# Paired run handoff

Current stop: B needs the user's 24-answer review. A is CPU-prepared but no GPU
gates have passed for either new run. No current pod is assumed alive.

## Before renting/using GPU

1. Export completed B review with export_review.py using the CPU tokenizer venv;
   inspect exported targets/token exposure and commit the reviewed source.
2. Verify both original reviewed-v2 hashes and all preflight artifact hashes.
3. Use the existing exp010 pinned setup/requirements and consult
   docs/environment-setup-gotchas.md and exp010/GPU-RUN-NOTES.md first. No vLLM
   installation. CPU tokenizer venv is not the GPU training environment.
4. Bundle/clone the committed repo; record source revision and environment.
   Read local .env W&B key privately when a GPU is available; never put it in Git,
   CLI logs, configs or this handoff. Use descriptive exp011/exp012 sft names.

## GPU gates, then training

Shared runner is exp-009-minimal-edit/train_reviewed.py. For A use
exp-011-duration-ablation/training-preflight-v1; for B use
exp-012-coverage-ablation/training-preflight-v1, never the draft directory.
Every mode needs --preflight-dir and a fresh --output-dir explicitly.

Required sequence per applicable new config/data: representation-check, smoke,
adapter save/reload verification, tiny-overfit and W&B authentication. Record real
gate booleans tied to SHA-256 of training-config.json; no automatic carryover of
the old exp010 LR-only waiver. Diagnostic adapters never initialize scheduled SFT.

Once gates are genuinely satisfied, run --mode full --gates <gate-file> for A
and B sequentially on one GPU, each loading the fresh pinned base. Four epochs,
80 rows, effective batch8, expected40 steps. The internal full CLI label is
historical; W&B display names use sft. Do not adjust LR, rank, batch or decoding
mid-comparison. Verify effective arguments and actual completed step count.

The existing runner saves each epoch but retains the last two checkpoints, plus
the final adapter. The preselected primary checkpoint is the final epoch-four
adapter. Preserve both retained checkpoints; do not claim all four are backed up.

Generate the unchanged 20 questions for each final adapter using
exp009/evaluate_adapter.py --adapter <final-adapter> --output-dir <fresh-dir>
--bounded. Do not retry with 8192/16384 when a loop/budget stop occurs. Consult
EVALUATION.md for comparisons, mode diagnostics and failure reporting.

## Before pod termination

Download adapters, retained checkpoints, optimizer/scheduler/RNG, effective
arguments, source configs, invocation, gate evidence, package freeze, rendered
templates, source bundle, training/inference logs, W&B history/local files,
raw generations/token IDs, masks and failures. Dereference external log symlinks.
Verify SHA-256 remotely and locally and inspect archive completeness before
telling the user the pod can be destroyed. Pinned public base weights remain an
explicit download dependency unless separately archived.
