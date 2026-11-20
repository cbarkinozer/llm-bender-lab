# Reflex-1 training dataset snapshot

Recovered byte-for-byte from the local `C:/Users/barkin/Documents/GitHub/pocket-agents-lab/runs/decision-followups-vast-20261013/reflex-decision-artifacts-20261013.tar.gz` backup on 2026-11-20. Original paths were under `reflex-decision/data/prepared/`. The archive remains outside Git; this snapshot preserves the dataset inputs and provenance.

Selected release checkpoint: `combined-balanced-scratch-120step-s3407/checkpoint-100` (see `release-manifest.json`).

The tracked `launch_combined_120.sh` specifies seed 3407, 120 steps, and equal phone/general weights. the source backup folder's `logs/combined-balanced-scratch-full.log` records 1,562 combined training rows: 781 phone, 391 typed-decisions, 195 BANKING77, and 195 CLINC150.

The phone training input contains 781 rows. The general training input contains a pool of 2,240 rows, from which the run sampled 781. These are the recovered source inputs, not a separately recovered materialized 1,562-row combined file. Validation, calibration, phone test data, split manifests, and general source revisions are preserved alongside the training inputs. Keep evaluation splits separate from training.

`recovery-manifest.json` records byte counts, SHA-256 hashes, and JSONL row counts. This is a local archival commit; no dataset publication is implied.
