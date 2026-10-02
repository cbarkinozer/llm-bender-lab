# GPU run v1 — 2026-10-02

Status: training and development generation completed; blind human review pending.
No quality improvement or zero-hallucination claim is supported yet.

Review: [50 blind pairs in Argilla](http://127.0.0.1:6900/dataset/580bd5b7-2f05-4f02-8fa5-9e9ba719cf91/annotation-mode).
Choose A/B/tie and pass/fail for each answer's task completion. Use the item's
expected mode and pass condition; flag applicable failures, not shortness alone.
Dataset name: `exp-008-development-v2-blind-v1`, workspace `sft-review`.

## Provenance and recipe

Source commit: `163cfa4f027487fa09295b0e961bc31d9b472edc`.
Frozen config SHA-256: `e654b37a5dcd87f66812e6d2594f7379c485d44ad6fa4b93aacc569e9e177092`.
Training SHA-256: `cbfbf3252ec99d7d5912e569de0d3872ebeef4609a42c7e9244f326f757607b6`.
Development SHA-256: `9e48512243e31a65ed8d800bdcc8bb4bf45da8995902bacfda730d996900643e`.
Base/tokenizer: `unsloth/Qwen3.5-4B`, revision
`3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.

The standalone pilot uses 100 corrected examples, 20 per family, not the older
958-row dataset. Three epochs, LR 1e-4, BF16 LoRA rank/alpha 16, effective batch
8, sequence length 1024, seed 3407, assistant-only loss, no packing. Both data
composition and volume change versus exp-006; this is not a single-variable
comparison or evidence of broad retention. Benchmark questions never enter training.

## Gates and training

- Representation: 100 rows, lengths 40–148 tokens, mean 80.36; zero truncation.
- Assistant mask: 50 valid target tokens in the inspected batch; checks passed.
- Smoke: 20 steps, average loss 2.182195; finite logged losses and gradients.
- Tiny overfit: 100 steps on 32 rows; first two logged losses average 2.1025,
  last two average 0.048915. Gradient spikes reached 185.9 and recovered with
  finite values. Preserve this diagnostic; do not describe the run as anomaly-free.
- Full: 39 optimizer steps / three epochs, 82.2506 seconds, average loss
  1.941578596; first logged loss 2.574, final logged loss 1.568.
  Maximum logged gradient norm 1.366; all logged values finite.
- Peak allocated/reserved VRAM: approximately 8.83 / 8.922 GB.

W&B was authenticated using only the local `.env` API key passed through SSH
stdin, never committed or printed. Only the full run used online reporting.
[W&B run](https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/0ca0a1a8)
was verified through the API as `finished`, with seven loss-history points and
summary global step 39.

## Environment and setup recovery

RTX 4090 (24 GB), driver 595.71.05, Python 3.11.16, torch 2.7.1+cu128,
triton 3.3.1, transformers 5.5.0, trl 0.24.0, accelerate 1.10.1,
datasets 5.0.1, unsloth 2026.9.6, unsloth_zoo 2026.9.5, FLA 0.5.2,
causal-conv1d 1.7.0 matching CUDA 12 / torch 2.7 / CXX11 ABI true.
Exact package freeze and setup logs are retained in the support archive.

Persistent venv `/workspace/.venvs/qwen-fast`; caches under `/workspace`.
Removed incompatible optional TorchAO and xformers. Installed the established
runtime dependencies separately, then Unsloth/Zoo with `--no-deps` because
resolver metadata conflicted with the validated datasets version. Imports and
all runtime gates subsequently passed. Bundle clone needed an explicit switch
to `main` (future clones should use `--branch main`). W&B ID creation used
`secrets.token_hex(4)` rather than unavailable `wandb.util.generate_id`.

## Evaluation and artifact retention

Both base and candidate generated 50 aligned, nonempty responses under identical
greedy, thinking-disabled settings (maximum 256 new tokens). The randomized
blind review includes item-specific anchors and preserves a sealed identity
mapping, which must remain hidden until human decisions are exported.
The development benchmark is diagnostic, not an independent final test.

Adapter weights SHA-256: `b1fa6c38af549044fc72f77a6df994d793ca99eadc3b4b14c5fadfa2de139406`.
Base output SHA-256: `e9322e5423dd0c6877249b1438456b4e67fdfaf9abc37c70f068946958fa9e8f`.
Candidate output SHA-256: `d4cf3dc1cff366b01fbb0a5d31d4ae3f1c6b9930cf39512193bc288438c01a51`.
Blind CSV SHA-256: `a3d759ad440626c5add0cd07cf86c0207cab45a2cea6f31b7e7ae5778e240d4b`.
Adapter config has `revision: null`; the actual cached base revision was checked
against the pinned config. Always reload with the explicit pinned base revision.

Remote artifacts: experiment `results/` under `/workspace/repos/llm-bender-lab`.
Local durable archives: `C:\Users\cbark\Documents\llm-bender-artifacts\exp-008-generalization-sft`.
Results archive SHA-256: `b7f738368ac7f43484dac12cd9afb14283a6668470d748f0db89dc91121872dd`.
Support archive SHA-256: `6f953ca19da24b748994fbc468f4f77b56ddf9c9642c8b147bb701f69ef658d0`.
Both local archive hashes were verified against the remote copies before handoff.
Support includes exact environment, setup failures/recoveries, orchestration
scripts, pipeline logs and the local W&B run. Model weights and raw answers
remain outside Git. The Vast instance is not stopped automatically.

### Backup audit follow-up

The local backup now also contains `exp008-source-at-run.tar.gz` (exact tracked
source/data/configs at the run commit) and a verified standalone
`exp008-repository.bundle` with complete history through `08d15d9`.
A local backup README records their SHA-256 hashes and recovery instructions.
Checkpoint 39 includes optimizer, scheduler, RNG, trainer state and training
arguments; runtime backend/environment snapshots and actual chat template are
also retained. Selection was the predeclared final epoch, not benchmark tuning.

One archive issue was found: W&B `debug-core.log` was an absolute Linux symlink
outside the archived run directory, which Windows tar could not restore.
Its actual target was downloaded separately as `support/wandb-debug-core.log`
(SHA-256 `2368cd5db08d89bffa1388f436dc80aaf0b2812da8e83ba5280c36823570c99b`).
Other support entries are extracted locally; exclude that symlink on Windows.
The original verified archives remain unchanged.

Pinned base weights remain a Hugging Face download dependency; they were not
duplicated into this backup. This supports procedural reconstruction, not a
claim of tested bitwise reproducibility or a fully offline base-model archive.
