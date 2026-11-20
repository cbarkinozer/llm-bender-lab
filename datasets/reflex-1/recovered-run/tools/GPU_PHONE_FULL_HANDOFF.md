# Completed-review phone-routing GPU run

Use `data/prepared/phone-routing-human-reviewed-v2-1080-fixedval-20261013/`:
781 reviewed training, 90 reviewed validation, 90 reviewed calibration, and 88
usable historical test rows. The 90 validation IDs are identical to the
300-review pilot's validation set; they are excluded from training along with
their automatic template groups. The exact source/snapshot and quarantine
IDs are in `manifest.json`. The strict all-row review audit still flags
human scenario/decision inconsistencies; the export excludes those cases.

CPU comparison on the fixed validation set:

| Training data | Character TF-IDF accuracy | Macro-F1 |
|---|---:|---:|
| 200 reviewed training rows (pilot) | 0.800 | 0.806 |
| 781 reviewed training rows (completed) | 0.944 | 0.944 |

These scores do not predict the Reflex-1 fine-tune's result. The complete
baseline report and its per-example errors are bundled for comparison.

`runs/phone-routing-reviewed-v2-full-gpu-inputs-20261013.zip` contains the
reviewed data, training source, setup script, baseline report, and this handoff.
It contains no credentials or model weights. Verify its hash against
`runs/full-gpu-inputs-sha256.txt` after upload.

The Reflex-1 starting checkpoint is **not on this laptop**. Recover the
original `checkpoint-60` backup and verify:

- `adapter_model.safetensors`: SHA-256
  `2eef23b07522d4a371f6e6a5e4e44bdebe29d97b97e066b1ad5e09034ac91cd7`
- `joint_head.safetensors`: SHA-256
  `6904172944df6d142c490fadc9beae6b38d83401b5ee71703b1866672094bd6b`
- `adapter_config.json`: SHA-256
  `397aeb36809aa70abc5896502d1edd0ccc61efc50260f37a61ed0a614f8ea1c2`

After unpacking under `/workspace/reflex-decision` and installing a compatible
CUDA/Unsloth environment (the included `setup_pod.sh` is the prior setup;
verify it on the new host), put those files under `checkpoint-60/` and run:

```bash
cd /workspace/reflex-decision
sha256sum checkpoint-60/adapter_model.safetensors checkpoint-60/joint_head.safetensors checkpoint-60/adapter_config.json
.venv/bin/python tools/train_phone_routing.py \
  --data-dir data/prepared/phone-routing-human-reviewed-v2-1080-fixedval-20261013 \
  --output-dir runs/phone-routing-reviewed-v2-full-smoke \
  --reflex1-adapter checkpoint-60 \
  --reflex1-adapter-sha256 2eef23b07522d4a371f6e6a5e4e44bdebe29d97b97e066b1ad5e09034ac91cd7 \
  --smoke
```

Only after the smoke passes, run the same command without `--smoke` and with a
new output directory. Save exact arguments, package freeze, GPU details,
training/validation/calibration metrics, logs, cost records, and verified
adapter/head/checkpoint backups. W&B is optional for actual fine-tuning only.
Do not use the 88 historical-test rows for checkpoint selection; assess them
once after selecting a checkpoint on validation. The historical test is not a
new independent test, so obtain fresh real-phrase data before claiming
generalization. Follow ReflexModels `EXPERIMENT_CLOSEOUT.md`. Do not publish
Reflex-1 weights without explicit authorization.
