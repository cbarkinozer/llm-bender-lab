# Bilingual pilot GPU run — 2026-11-18

Host supplied by owner: ssh7.vast.ai:33292. RTX4090 24GB, driver 595.99.02.
Remote repository: /workspace/repos/llm-bender-lab. Source baseline e52fad8 plus
the fingerprinted GPU runner and orchestration changes in this session.

Active dataset remains bilingual-pilot-v01/revisions/v01-corrections-02. Fresh
LoRAs are initialized independently on the same pinned BF16 CPT merge. Existing
terms decisions and private-research scope are preserved; no upstream rights
clearance is falsely claimed. Live, artifact-bound GPU gates are recorded under
bilingual-runtime-local/gpu-gate.json, distinct from historical preparation gates.

Training completed:

| Arm | Rows | Steps | Saved checkpoints | Supervised tokens |
|---|---:|---:|---|---:|
| exp-010 Turkish-only | 160 | 100 | 60, 100 | 208665 |
| exp-011 four directions | 640 | 113 | 69, 113 | 209811 |

Native tokenizer/template/mask checks passed on all 640 variants; exact parent
BF16 merge/reload passed. Corrected smoke passed, including reload parity and
generation. Tiny-overfit used 20 train-only rows, five per source, 40 diagnostic
updates: token-weighted NLL 2.3344284331 to 0.3649971057. These are engineering
checks, not model-quality scores. Two earlier smoke reload-probe failures are
preserved and explained in docs/environment-setup-gotchas.md.

The actual train sampler is sequential over the frozen row order; the actual
first batch is checked against that order. Context/padding are masked; optional
reasoning, native empty-think blocks and EOT stay supervised as agreed. LR,
rank, dropout, optimizer and other recipe parameters stay matched. Config run
names now state the actual 100/113 steps. W&B credentials stay outside the repo.

Development inference completed for all four saved checkpoints:
dev20, the earlier crosslingual15, CETVEL100 and TurBLiMP1600. The exact pinned
untouched-original dev20/CETVEL100/TurBLiMP baseline is reused from pilot160, with
hashes and protocol checks; no CPT-only baseline is substituted. Same vLLM build,
BF16, seed3407, temperature0.1, top-k50, top-p1, repetition penalty1.1, 8192
context, 4096 new-token cap, thinking off, explicit native EOT and loop guard.

Fresh eval-v01 (35 tasks x 4 directions + 8 controls) remains sealed for final
evaluation after checkpoint selection. Do not select checkpoints on that packet.
The development queue will use ranking and reasoning only, with five anonymous
answers (original plus four checkpoints), randomized and position-balanced.

The local queue is now published and all 20 records/raw answers verified:
http://127.0.0.1:6900/dataset/d1ded7a1-12f7-4e64-954a-2b75a079ac41/annotation-mode
Dataset: turkish-bilingual-sft160-dev20-blind-v01. Only ranking and reasoning
are required. A-E identities change per question; the private key stays in the
ignored runtime directory. Existing queues and owner reviews were preserved.

Operations:

- Pipeline log: /workspace/setup-logs/bilingual-pair.log.
- Runtime: experiments/turkish-capability/lfm3-1.7b/bilingual-runtime-local/.
- Training entrypoint: scripts/training/run_lfm3_bilingual_gpu.py.
- Orchestrator: scripts/training/run_lfm3_bilingual_pair.py --phase all.
- Package: scripts/training/package_lfm3_bilingual_artifacts.py --kind training/all.
- Local recovery: scripts/evaluation/recover_lfm3_bilingual.py --kind training/all.

Only four checkpoint LoRA files and small configs/logs/results are recovered.
Full merged weights and optimizer states remain on the pod. Archives and local
results are ignored. BILINGUAL-TRAINING-BACKUP.json records 215 verified files,
including all four checkpoint LoRAs. BILINGUAL-ALL-BACKUP.json records another
305 verified files containing completed inference, scores and operational logs.
Both archives passed SHA256 and per-file verification locally. No full model
weights or optimizer states were downloaded. No publication, push or pod shutdown
is performed. Fresh final inference remains pending checkpoint selection.
