# CPT pair GPU session â€” 2026-11-12

Owner provided `ssh -p 17103 root@77.235.122.199`. RTX 4090, 24,564 MiB,
driver 595.99.02, Python 3.12.3, 80 GB overlay. No persistent external mount was
established. Treat all remote storage as ephemeral.

Source checkout: `c61c433` plus recorded working-tree patch. Private transfer
archive SHA256 `86270f42d6b0810cdbdbbec92cec27977e134b1ae97a124e309e871bb47f3cc5`;
all 211 members verified remotely before extraction into
`/workspace/llm-bender-lab`.

The training runner now writes an actual first-step LoRA gradient/frozen-embedding
audit. `audit_lfm3_gpu_gate.py` creates each manifest-bound gate only after both
real diagnostics complete, labels/gradients pass and tiny-overfit eval loss drops
at least 2%. Diagnostic adapters never initialize full training.

Training environment: `/workspace/.venvs/lfm3`; native inference environment:
`/workspace/.venvs/lfm3-vllm`. Setup logs: `/workspace/setup-logs`. Secret credential
is outside the repository; never copy it into recovery artifacts.

Status: both actual-model diagnostic gates passed. Tiny-overfit eval losses:
Wiki 2.833569 -> 0.015403; mixed 4.087702 -> 0.127189. All actual labels,
finite/nonzero LoRA gradients and frozen embeddings passed. Full Wiki training
started (W&B run aze747zg); mixed follows from a fresh original checkpoint.
Measured full-sequence throughput about 6,300 raw/packed tokens/s, ~2.6 s/update;
A has 135 planned updates. Native inference dependencies and CUDA/BF16 passed.
Full training/evaluation completion and local recovery are NOT yet verified.
Do not close the pod on the basis of this note.

Execution order adjustment: train and merge both models while the isolated
inference environment installs, then evaluate each. Compute held-out raw-text
loss and grammar before the longer CETVEL generation pass; packets/scoring and
generation settings remain fixed. No simultaneous GPU training/evaluation.

Recovery may omit regenerable merged weights after completed merge/load/eval
checks. The bundle must retain adapters, pinned base identity, saved environments,
merge source and exact hashes of the omitted files in reconstruction receipts.
Optimizer states, diagnostic artifacts, raw predictions and logs are retained.

Follow `CPT-PAIR-TODO-20261112.md`. A and B independently start at the original
pinned checkpoint. Reuse the completed baseline, keep inference out of W&B,
preserve failed attempts and verify all recovery archive members locally before
declaring the GPU safe to close.

Owner stopped sequential evaluation on 2026-11-12 because of excessive runtime. Evaluation wrapper, queued finalizer, stage process and owned vLLM engine were terminated. Both trained adapters and partial outputs remain on the pod; Wiki training backup is verified locally. No batched or repetition-penalty change has been applied. Full recovery is still pending; do not assume the pod is safe to delete.

Owner approved a new fast screening protocol: balanced 100 items (20 per task), batch size 4, repetition penalty 1.15, greedy, same 4096-token output/8192 context. All base/A/B generations rerun under this protocol, separate fast100-v02 folders. Pilot b1 versus b4 completed 5/5: 11.58 vs 3.73 seconds, only 1/5 token-identical. No claim of exact output equivalence; first b4 pilot had a late-abort acknowledgement bookkeeping error, fixed and successful retry retained. Scope is exploratory. Staged policy: screen with 100, extend the same fixed IDs to 200 for promising checkpoints, use 500 for finalists; never mix decoding settings. Historical sequential A output is task-ordered, so first 200 does not cover all five tasks. Both trained runs/logs/optimizer states are being downloaded as lfm3-cpt-ab-trained-20261112.tar.gz; merged weights remain reconstructable from pinned base and saved adapters. New raw predictions and metrics must also be recovered before closing the pod.

COMPLETED: both independent CPT runs, matched fast100 for all3 models, all text/grammar scores, W&B verification and local recovery passed. 416+126 archive members verified. GPU idle0%,1MiB, no generation process. Safe for owner to close. See CPT-FAST100-RESULTS.md and cpt-local-recovery-v02.json. No next training run started.
