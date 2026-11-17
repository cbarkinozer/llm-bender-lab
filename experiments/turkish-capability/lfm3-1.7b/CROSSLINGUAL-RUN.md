# Cross-lingual diagnostic run

Status: completed inference, local recovery and owner review on 2026-11-17.
All 15 rankings valid. See CROSSLINGUAL-DIAGNOSIS.md and
CROSSLINGUAL-OWNER-REVIEW.json. Four models, 60 answers; no new training.
Pod endpoint: ssh4.vast.ai:18506. Detached pipeline PID at launch: 1151.
Remote progress: /workspace/crosslingual-pipeline.log.

All three merges passed save/reload logit parity. Infrastructure smoke passed.
All four runs completed with matching packet and decoding protocol. The small
results archive and all 30 members passed SHA256 verification on the laptop;
see CROSSLINGUAL-BACKUP.json. Setup/download logs, environment freezes,
merge receipts, generation logs, manifests and raw answers are recovered under
the ignored crosslingual-runtime-local directory. Parent pipeline log and
archive are preserved under preparation-local/recover-crosslingual.

Argilla: http://127.0.0.1:6900/dataset/405dc428-6eab-4a2f-8517-6e5f0d56a5b6/annotation-mode
Queue: turkish-crosslingual-holdout-v01 in sft-review. Fifteen records, four
answers each; exact API roundtrip verified. Only ranking and reasoning fields.
Identities vary per record, remain private locally and are not uploaded.
Once owner review is submitted, export immutable reviews and diagnose language
understanding, output-language quality, meaning preservation and arithmetic
before deciding whether to run the conditional bilingual pilot.

Source baseline commit: c8c32f9. New inference-only runner reconstructs CPT,
direct-base SFT and CPT-initialized SFT from pinned parent and recovered adapters,
without requiring optimizer states. Save/reload parity is required per merge.
The baseline vLLM runner and its decoding/loop guard are reused unchanged.
A non-benchmark infrastructure smoke precedes the 60 primary generations.

Runtime and private Argilla mapping are ignored under crosslingual-runtime-local.
The new Argilla publisher preserves old queues and requires only ranking and notes.
The exporter preserves immutable raw reviews and never guesses invalid rankings.
Numerical diagnostics distinguish strict numeric matches from heuristic last-number
candidates; prose correctness and language quality need owner review.

GPU: RTX4090, driver590.48.01. Dedicated SSH key outside the repository.
Model downloads/merges stay on the pod. Recover only small results/logs/manifests;
all original adapters are already safely on the laptop. Required inference
artifacts are recovered; the pod may be closed by the owner. No shutdown issued.
