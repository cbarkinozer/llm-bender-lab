# Recovered Reflex-1 training records

Recovered from the archive named in recovery-manifest.json. Original archive-relative paths are retained beneath this folder. The adjacent logs/combined-balanced-scratch-full.log was also copied from the local backup's logs directory; its source is recorded separately.

- tools/: original training, mixture preparation, evaluation scripts and helpers, including train_combined_routing.py.
- environment-freeze.txt: saved package versions and exact Unsloth/Unsloth Zoo Git revisions.
- runs/: saved JSON run manifests, metrics, calibration and adapter/head/tokenizer configs, and checkpoint trainer states for smoke and full runs.
- combined-balanced-scratch-120step.log: log for the 120-step run. combined-balanced-scratch-full.log belongs to the earlier full run; both are retained with their original names.
- runs/combined-balanced-scratch-120step-s3407/run-manifest.json: actual mixture, seed, effective batch size, learning rate, runtime, and W&B run identity.
- runs/combined-balanced-scratch-120step-s3407/checkpoints/checkpoint-100/trainer_state.json: best checkpoint selection and training history.

The launcher is preserved here and in the parent dataset folder. It uses the original /workspace paths; dataset inputs are archived in the parent folder. These files are archival evidence, not a newly executed or validated GPU environment. Python sources were syntax checked; JSON records were parsed and recovered bytes verified by SHA-256. Model weights, optimizer binaries, caches and authentication logs are not included. No claim is made that every resolved TrainingArguments default was saved; inspect the source TrainingArguments constructor together with the saved launcher and manifests.
