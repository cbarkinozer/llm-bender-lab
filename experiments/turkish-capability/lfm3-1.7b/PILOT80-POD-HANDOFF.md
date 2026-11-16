## Shutdown readiness

Verified safe to close the pod: adapters, tokenizers, inference outputs, SFT/W&B/setup logs and reproduction files are downloaded. All352 original files match the live pod. Remaining logs, model metadata and exact benchmark packets are in a verified closure supplement. Merged weights were excluded at the owner's request. See PILOT80-BACKUP.json. No optimizer/scheduler resume state existed. The agent has not stopped the pod.

# Pilot80 continuation handoff

Status: both production SFT runs and every matched inference/scoring stage completed.
The detached pair log ends `PAIR COMPLETED`. No GPU work is queued.
Owner blind correctness/instruction-following grades remain pending.

- [Results and limitations](PILOT80-RESULTS.md)
- [Compact metrics](PILOT80-METRICS.json)
- [Verified local backup receipt](PILOT80-BACKUP.json)
- [Frozen comparison plan](SFT-PILOT80-PAIR-PLAN.md)
- [Owner review rubric](PILOT80-REVIEW-RUBRIC.md)
- Offline review: `pilot80-runtime-local/blind-review.html`; export notes as JSON.
  Model identity key is separate in `blind-column-key.json`.

Local recovered adapters are under each experiment's
`results-local/sft/adapter/`. Raw predictions, stage receipts, native-label audit,
merge checks, exact source manifest and runtime package versions are retained in
`pilot80-runtime-local/`. All352 files listed by the archive manifest were
hash-verified, including four external W&B log symlinks fetched separately.
The490,009,340-byte archive is retained in ignored
`preparation-local/pilot80-results-backup-verified.tar.gz`.
The launch source snapshot is `preparation-local/pilot80-source-snapshot.tar.gz`.
Large weights and credentials are excluded from Git. Recovered files were checked
for the configured HF/W&B private credential values without printing them.

Pod: root@1.193.137.204 port36997. Existing local id_ed25519 authenticates.
Repository: `/workspace/repos/llm-bender-lab`.
Train Python: `/workspace/.venvs/lfm3-sft/bin/python`.
vLLM Python: `/workspace/.venvs/lfm3-vllm/bin/python`.
Main log: `/workspace/setup-logs/pair.log`.
Merged CPT and both complete merged SFT models still remain on the pod.
The pod has not been shut down or deleted; nothing was published or pushed.

Next: owner blind review, then reviewed corpus expansion and a separate development
set before further optimization. Optional reasoning was trained; the completed
primary comparison disabled thinking for all three models. A thinking-enabled
comparison requires a separate fixed matched protocol. Do not retrain on the20
holdout examples or select checkpoints from these test responses.

Frozen launch configs retain their original planned status as immutable inputs;
actual completion and exact versions are in the training/evaluation manifests.
Changes are uncommitted; launch code provenance records Git base5bbf3b7 plus the
exact dirty source snapshot. Do not change active frozen artifacts to relabel them.
