# exp-006 GPU run and evaluation handoff

## Current state

Representation check, smoke, tiny-overfit, and full-v1 training passed. Base
and adapter generations for all 50 sealed final-holdout prompts are complete.
The anonymized pairwise review is loaded in the local Argilla workspace and is
pending human annotation. Do not open `blind-mapping-sealed.json` or raw output
files until the Argilla review is submitted and frozen.

Argilla dataset: `exp-006-quality-repair-sft-final-v2` in workspace
`sft-review` (50 records). Annotation URL:
`http://127.0.0.1:6900/dataset/a0fee8a2-6ebf-4935-a61c-9d23ebbd1f19/annotation-mode`.
Use the compact form: select A/B/tie for overall preference, mark task
completion for each, select only applicable policy failures for each, and add
a short note. Length and heuristic flags are diagnostic only.

## Frozen inputs and recipe

- Source commit: `fdc56af70d7fda74f4d230b9c7454f315e7cbc56`.
- Model: `unsloth/Qwen3.5-4B`, revision
  `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.
- Training data: 958 rows, SHA-256
  `bbaab152182318da5aff73a5227b784550933dfac1848037ad86f4cc57a7ebff`.
- Final holdout: 50 items, SHA-256
  `1eb26264e79e0818200d06d959625c31786818c26f9ff2bc6105b69921e135fb`.
- Recipe is unchanged from exp-005: BF16 LoRA SFT, rank/alpha 16/16,
  learning rate 1e-4, 3 epochs, effective batch 8, max sequence length 1024,
  assistant-only loss, packing disabled, seed 3407. Full config and per-run
  snapshots are in `config.yaml` and the result bundle.

## Vast.ai run record

- Provider/region: Vast.ai, Denmark host; RTX 4090 24 GB.
- Driver 595.84 (reported CUDA capability 13.2); runtime Torch
  `2.7.1+cu128`, CUDA runtime `12.8`, Python `3.11.16`, Triton `3.3.1`,
  Transformers `5.5.0`, TRL `0.24.0`, Unsloth `2026.9.6`, Unsloth Zoo
  `2026.9.5`, FLA `0.5.2`.
- The base Vast image did not include the expected usable Torch/Unsloth stack.
  The validated environment was installed into `/workspace/.venvs/qwen-fast`
  with `/workspace/.local/bin/uv`; the exact 111-package freeze is saved in
  the local support archive.
- Vast host startup was provider/host dependent in the preceding attempts:
  the Bulgaria host took about 45 minutes and Denmark about 15 minutes. Do not
  budget this startup delay as training time. For downloads, bundle many small
  result files into one remote tarball first; recursive SCP spent substantial
  time on per-file overhead.
- Template environment variables were not all inherited by the SSH shell;
  cache paths were exported explicitly for commands. The virtualenv has no
  `pip` module, so capture package inventories with `uv pip freeze --python`
  rather than `python -m pip freeze`.
- HF Hub was used unauthenticated. Its warning did not block loading or
  generation.

### Gates and full training

| Run | Result |
| --- | --- |
| Smoke | 20/20 steps; finite loss; ~70.8 sec; train loss about 2.061 |
| Tiny-overfit | 32 examples, 100 steps; loss about 2.439 to 0.057; ~125.1 sec |
| Full-v1 | 958 rows, 3 epochs, 360 steps; 407.6 sec; train loss 1.00197 |

Full-v1 peak recorded memory was 8.85 GB allocated / 8.924 GB reserved. No
NaN, OOM, or failed training step was observed. Several isolated gradient-norm
spikes appeared in logged windows (including approximately 19.5, 112, 1,693,
355.8, and 115.6); following logs recovered and loss remained finite. Keep
these as a diagnostic item for the next run and inspect per-example behavior
if the pattern repeats. Do not describe the run as anomaly-free.

The supplied causal-conv1d wheel imported, but its C++ extension was skipped
under Torch 2.7; record this as an environment/performance limitation if
comparing throughput with a different stack.

### Sealed final generation

Both roles used thinking disabled, greedy decoding, temperature 0, and 256
maximum new tokens against the same frozen holdout. IDs and counts align at
50 each.

- Base output SHA-256: `e299678231a9bba7806be98b45d2376d73a5519be9b1f6f0ca4b7f5cc7cd60b3`.
- Candidate output SHA-256: `a64310b2080fe503288417bab2e1a165542185bf96d4e993729f72e46fe47ce2`.
- Blind review CSV SHA-256: `20d079e47cef23305ada838c7a58367940cdce20989f62cb536258f423522ec5`.
- Sealed A/B mapping SHA-256: `bb948c4db9e895b1ab1f8e4f80c1ae22698eda27dcd8f59955122b83e686d8dc`.
- Adapter weights SHA-256: `54a8ee676e9a6e2a6c4444c3b6488c9673aa037ab1f82db3ddfc33f271d51f52`.
- Argilla import CSV SHA-256: `547234cdd3776145d365ea13566bb337d5a66f54b08a6e358e301c4dcfb08f21`.

The blind file was randomized with seed 3407. Keep the identity mapping private
until human review is frozen. This internal targeted holdout is not the
independent third-party benchmark required for a broader quality claim.

## Tracking and durable files

W&B project: `llm-bender-lab-response-style-control`. The dashboard contains
four complete fine-tuning runs, named by experiment and training-data focus:

| Experiment | W&B run name | Run ID | History source |
| --- | --- | --- | --- |
| exp-003 | `exp-003-initial-style-sft` | `w87rvm0r` | Original online W&B history |
| exp-004 | `exp-004-clean-v2-sft` | `hv5goon2` | 60 original `training.log` measurements backfilled at their five-step cadence |
| exp-005 | `exp-005-targeted-policy-sft` | `o0te4or4` | Original offline W&B events synced from the reproducibility archive |
| exp-006 | `exp-006-quality-repair-sft` | `7rgdgglo` | Original offline W&B events synced after training |

The exp-004 replacement was verified against all 60 loss values in the earlier
backfill (`y830q0ql`) before the earlier run was removed. All four current
runs log `train/loss`, so their curves share the same W&B chart. The exp-006
run records 360 optimizer steps and the original summary
(`train_loss=1.00197`, `train_runtime=407.6059` seconds). Its dashboard URL is
<https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/7rgdgglo>.

Only complete fine-tuning iterations count as experiment versions: the
current exp-006 group contains one complete run, with `run_version=v1` in
its metadata. If the same hypothesis and config are rerun, record the next
version in metadata; a changed hypothesis belongs to a new experiment.
Smoke and tiny-overfit are local preflight gates, not experiment-version runs.
Their W&B runs were briefly synced during recovery, then removed after the
dashboard scope was clarified. Representation-check and base/adapter
generation are preserved by local manifests, not as W&B training runs. No raw
generation text or blind A/B mapping was uploaded to W&B.

The exact 111-package freeze, `nvidia-smi -q`, and original offline W&B files
for the three training modes are in `exp-006-support-complete.tar.gz`. The
sync command used a short-lived `WANDB_API_KEY` in the Vast process; the key is
not saved in the repository or run notes. `exp-006-support-final.tar.gz` is a
superseded audit copy containing temporary metadata-only W&B records that were
later deleted; use the `support-complete` archive as the canonical support
bundle and do not sync the audit copy. The smoke/tiny-overfit offline files
are preserved locally as gate evidence; do not bulk-sync them into the
experiment-version dashboard.

The verified local bundle is under
`%USERPROFILE%\Documents\llm-bender-artifacts\exp-006-quality-repair-sft\`:

- `exp-006-results.tar.gz`: all result runs, adapter/checkpoints, manifests,
  base/candidate generations and run snapshots; SHA-256
  `51d6bd4b083ee2af483d9205e72b6214bc203102248c2a149e1c122d7a79e552`.
- `exp-006-support-complete.tar.gz`: original offline W&B runs, exact package
  freeze, and `nvidia-smi -q`; SHA-256
  `87c073f7fb0f3408603dfd336d82e6e0c75351f86d136497c48d807bbca3dd7f`.
- `exp-006-support-final.tar.gz`: superseded W&B audit archive; SHA-256
  `705100947c6e119873e4a3884291f91158f847e696e0a4405d2b59dbdab7fb1c`.
- Extracted `results/blind-review/argilla-review.csv` is the human-facing
  review file; `blind-mapping-sealed.json` remains private there.

The local Argilla stack and Vast instance can be stopped after confirming this
bundle exists. The Argilla review database must remain running only while
annotation is in progress; export the completed annotations before stopping it.
