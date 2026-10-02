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

Do not stop the GPU until backup verification and required adapter inference.
