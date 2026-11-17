> Current status: original pair plus direct-base control completed. All six LoRAs, inference outputs and required logs are downloaded and verified. `BASE-SFT160-BACKUP.json` reports safe to close the pod for adapter-only scope. Four-way Argilla review is ready. No pod shutdown, model publication or Git commit was performed. Earlier pending transfer notes below are historical and superseded.

# SFT160 pod handoff — 2026-11-17

## Current owner scope and active recovery

Owner requested LoRAs only on2026-11-17. The1.6GB resume-state download and old finalizer have been stopped; their older requirements below are superseded. No full/merged model weights were downloaded. Adapter-only archive486,656,682 bytes, SHA256ba5b44d06300b9fe99d71fbf5866313684ccb1c26d17d20e75822ef0594ffa10. Active hidden downloader PID14332; recheck `preparation-local/background-recovery-processes.json`, `download-loras.log/.err`. It verifies four adapter files and all archive members before updating `PILOT160-BACKUP.json` and stopping the temporary TLS transfer service. No optimizer states are required for this owner-approved recovery scope. An optional private Hugging Face staging question is pending because direct transfers stall; do not upload anything there without the owner reply.

Review queue: [blind development20](http://127.0.0.1:6900/dataset/c53bfd4c-b96d-46e4-8919-e8924191e3f9/annotation-mode), text ordering and reasoning only. See `PILOT160-REVIEW.md`; keep the mapping private until review is complete.

Status: both SFT runs and all planned inference completed, exit0; see [results](PILOT160-RESULTS.md). Large training artifact recovery remains incomplete. Two fresh LoRA
runs on the same pinned CPT merge: exp007 LR1e-4 and exp008 LR2e-4,100 updates,
six warmup steps, checkpoints60/100 (epoch3/5 of one five-epoch cosine schedule).
Keep the old160 reviewed training text frozen. Thirty nonempty reasoning examples;
blank thinking stays blank. Separate authored dev20 and frozen selection rubric
are in `sft160-dev-v01/`; the old20 never enters training or checkpoint selection.

The previously validated machine was one RTX4090/24GB, driver580.173.02 advertising
CUDA13.0. Reuse that capability class. The exact historical Torch2.14/vLLM wheel
stack requires a CUDA13-capable driver; check before installing. Allow about80GB
persistent `/workspace` for two environments/caches, parent+CPT and four merged
inference checkpoints. No current hosting price or availability assumption.

SSH public key:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMV2mfmbt2Mf2m73D+4/1uqIsOm8g91HJMbolziF7vqm lfm3-sft160-20261117
```

Private key remains on the owner's laptop at
`C:\Users\cbark\.ssh\id_ed25519_lfm3_sft160_20261117`, outside Git/bundles.
Account-level key changes may not reach an already running pod: install the public
key before provisioning, or add it through the pod console if needed.

## Launch order after SSH is supplied

1. Inspect GPU/driver, disk and existing `/workspace`; do not assume old pod state survived.
2. Transfer hash-verified source bundle with160 rows, dev20, frozen benchmark packets
   and code. Credentials stay outside the bundle/repository and logs.
3. Run `bash scripts/training/setup_lfm3_sft160.sh`, retain setup logs.
4. Source `/workspace/lfm3-sft160-cuda-env.sh`; export persistent HF/pip/uv/W&B cache paths.
5. Run `/workspace/.venvs/lfm3-sft/bin/python scripts/training/run_lfm3_sft160_pair.py --phase preflight`.
   This audits native labels/lengths, downloads and merges the pinned CPT parent,
   generates untouched base dev20/CETVEL100/TurBLiMP before SFT, then runs disposable
   new-data smoke/tiny-overfit and save/reload/generation. No training can bypass gates.
6. Run the same entrypoint with `--phase train`, then `--phase evaluate --thinking-probe`.
   `--phase all --thinking-probe` executes the whole sequence if no stages exist.
   Stage receipts bind commands/artifact hashes and a frozen source/input manifest.
   Failed partial outputs are preserved and require inspection before a clean retry.

Every run independently initializes LoRA on the CPT merge. Untouched LiquidAI at
revision0dc4268b561499c648c7ba7c9466bf3d8d01517a is the comparison baseline;
CPT revision6f213ec25a944dab2fbdeb6d337deb0e0442e638 remains the training parent.
No pilot80 SFT adapter is resumed.

Primary inference: vLLM BF16, eager,batch4,context8192,new4096,temp0.1,topk50,topp1,
repetition1.1,seed3407,prefix caching off, explicit native EOT and prior loop guard,
thinking disabled. Evaluate four checkpoints on dev20/CETVEL100/TurBLiMP. Optional
separate reasoning4 compares thinking off/on with the same output cap; not equal
compute, and not pooled into primary checkpoint selection. No automatic winner
is inferred from loss or whole-answer exact match.

Save adapter/tokenizer, optimizer/scheduler/RNG state, trainer state, first-batch
labels, W&B logs, resolved runtime, merge/reload receipts and raw inference.
Before shutting down: download and verify checkpoints60/100 for both runs plus
logs and inference. Merged weights can be rebuilt; never delete resumable states
until the owner has a verified local copy. No model publication/deployment here.

## Active session

RTX4090/24GB, driver595.99.02, CUDA13.2,80GB workspace. Existing laptop `id_ed25519` authenticates; the new dedicated key was rejected. Source bundle SHA25692ca9d71732b545ce25d6af47e24ecc42223ff255927f5a7056441168a51038e verified remotely before extraction. Repo `/workspace/repos/llm-bender-lab`. Setup log `/workspace/setup-logs/sft160-setup.log`; pair log `/workspace/setup-logs/sft160-pair.log`; final exit code `/workspace/setup-logs/sft160-pair.exit` when finished. Credentials are restricted in `/workspace/private-credentials.json` outside the repo and bundle. Do not include that file in backups.

Runtime and all inference are recovered locally with161 member hashes verified. Training backup is1.6GB and transfers have been slow/resetting; verified chunks are preserved in `preparation-local/sft160-backup-parts`. Temporary authenticated pinned-TLS read-only transfer serves only the two archive files and manifests over the existing8080 reverse relay; token/certificate client config is outside repo under the laptop `.ssh` directory. Its private directory is outside all archives. Stop this transfer service once local backup verification completes. Do not claim safe shutdown before `PILOT160-BACKUP.json` confirms all four complete checkpoints local.

Local background recovery is detached and hidden: downloader PID17648, verification/extraction finalizer PID3624. Recheck current PIDs in ignored `preparation-local/background-recovery-processes.json`, plus `download-https.log/.err` and `finalize-backup.log/.err`. Verified parts survive retries. The finalizer updates `PILOT160-BACKUP.json` to `passed_safe_to_close_pod` only after whole-archive and every member hash matches, all four complete adapter/optimizer/scheduler/RNG checkpoints are local, and the inference archive hash matches. It then stops the temporary transfer service. User model/dataset publication and pod shutdown were not performed.
