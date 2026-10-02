# Training run — 2026-10-02 UTC / 2026-10-03 Istanbul

Fresh pinned base, reviewed-v2 only: 80 training / 20 development-validation
rows. No historical adapters, old Turkish dataset, replay, or vLLM used.
Recipe: training-preflight-v1/training-config.json, rank 16, BF16 LoRA,
LR 5e-5, microbatch 1, accumulation 8, two epochs, 20 optimizer steps.
Executed source commit: 2fdff3c.

## Verified gates

- All 100 GPU tokenizations matched local preflight; final-answer-only labels
  and padding masks verified. Trainable parameters: 21,233,664 (0.47%).
- Three-step smoke completed: mean training loss 1.7343841394.
- Smoke adapter reloaded on fresh base: finite masked forward loss 0.6162181497.
  This was a forward check, not a generation/stopping check.
- Tiny-overfit diagnostic (16 training rows, 40 steps, LR 2e-4) reduced
  same-subset evaluation loss from 0.4482119679 to 0.0004388985.
- W&B authentication verified using only the .env key over SSH stdin.

## Full run

Run: https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/d8d2f6dd

Remote output: /workspace/exp009-runs/full-v2

Completed 20/20 steps, 2 epochs, 73.5096 seconds training runtime.
Mean training loss: 1.4711812735. Development-validation loss: approximately
1.102 at epoch 1, 1.018 at epoch 2. Both epoch checkpoints retained.
These losses do not establish response quality or absence of forgetting.
Full adapter generation/reload and base-comparable validation evaluation remain.

## Setup failures and resolution

Direct SSH 212.83.33.56:40044 worked; proxy ssh7.vast.ai:15824 had previously
closed before key exchange. RTX 4090, driver 590.48.01.

Remote uv URL installation stalled on causal-conv1d wheel metadata/download.
Downloaded the identical official wheel with curl, then installed locally.
SHA256: 6d04c5b9c675dd68aa4ece694d3c5d1d79b25326757bae567aeb2edfe1dd5cc2.
Validated Torch 2.7.1+cu128 / Transformers 5.5.0 / Triton 3.3.1 / Unsloth
2026.9.6. First smoke optimizer step took ~95s; later steps ~2–3s.

First full launch (8929dd8c, full-v1) failed before any training step because
the detached child inherited a parent-owned W&B service socket. Launcher now
removes WANDB_SERVICE* variables before spawning, allowing its own service.
Failed output/logs preserved; no recipe changes. Successful retry: full-v2.

## Backup

Archive includes diagnostic and full outputs/checkpoints/adapters, configs,
environment freeze, setup/download/failure/training logs and W&B local files.
Remote: /workspace/exp009-training-backup.tar.gz
Local destination: C:/Users/cbark/Documents/llm-bender-artifacts/exp-009-minimal-edit/training/
Expected SHA256: 019e2d0da066464248d936ddee9f9d0be2e931e8ed94d26c70d7008a1214155b.
No .env or private SSH key included. Source and data are versioned in Git.

## Recovery and validation completed

Final adapter reloaded against the pinned base and answered all 20 frozen
development-validation inputs using Unsloth/Transformers, BF16, greedy,
repetition penalty 1.05, non-thinking, no extra system prompt. All 20 stopped
at native EOS on the first 4096-token budget. No answer/reference was supplied
as input. Backend differs from the existing vLLM base run; this caveat is
explicit in the evaluation manifest, so this is not exact backend parity.

Evaluation source: 43fb431. Remote output: /workspace/exp009-runs/validation-v1.
Local comparison: training/exp009-runs/validation-v1/comparison.csv under the
artifact root. Contains original base, desired and adapter answers side by side.
Adapter SHA256: bc71e59277ed168d626571e636bd24b7154ea4f91327fec7d0908a3bab5a7acf.

Two complete archives downloaded and matched remote SHA256:

- exp009-training-backup-verified.tar.gz: 019e2d0da066464248d936ddee9f9d0be2e931e8ed94d26c70d7008a1214155b
- exp009-evaluation-support.tar.gz: ea9ba94b0665303665494b41add1c8f7b72ccc167e838e7aaa6115ee3024ba52

Single-stream SCP and SFTP connections reset during backup. Split the immutable
training archive into 16 MiB parts, downloaded eight at a time with retries,
checked each hash, reconstructed and checked the complete archive. Incomplete
earlier archive downloads are not valid backups; use the `-verified` archive.

Both archives extracted locally; effective TrainingArguments JSON, training
checkpoints with resume state, tokenizer/chat template, local W&B files, raw
validation token IDs/text/attempts, original source data and scripts retained.
A full source Git bundle is also saved in the local training artifact folder.
Pinned public base weights remain downloadable, not redundantly backed up.
Hardware metadata was captured post-run; exact/bitwise reproduction is not claimed.

Windows tar could not extract Linux W&B symlinks from the original archive.
Downloaded and extracted an additional dereferenced W&B archive, preserving
the actual linked debug-core log as ordinary files. SHA256:
7bfa1be8f866a61b60fe13b4a3e40ceafc0fe5a0d9393ddb44f0dcd7b61d2a1a.
Local: training/exp009-wandb-resolved.tar.gz and training/wandb-resolved/.
All evaluation file hashes and the extracted final adapter hash also verified.

GPU termination is now safe for this run's artifacts. Human quality review and
broader retention checks remain; do not infer quality from EOS or training loss.
