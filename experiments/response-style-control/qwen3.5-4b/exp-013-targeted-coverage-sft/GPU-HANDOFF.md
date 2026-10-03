# C/D GPU handoff — reviewed data frozen, CPU verified

Completion override2026-10-03: C/D SFT,40 primary generations,desired/A/C/D
comparison and local129-file backup verification complete. GPU can be terminated.
See GPU-RUN-NOTES.md. User explicitly granted a NEW C/D smoke/tiny-overfit
waiver after this preparation handoff; false/waived gates are recorded, not passed.
The original plan below is historical and must not be mistaken for pending work.

Status2026-10-03: awaiting user GPU endpoint; no pod assumed alive, no training
or inference launched. No further candidate annotation required.

## Active immutable inputs

- C: exp-013-targeted-coverage-sft/config-reviewed-v1.yaml and training-preflight-v1.
- D: exp-014-targeted-duration-sft/config-reviewed-v1.yaml and training-preflight-v1.
- Shared80-row train: exp013/data-reviewed-v1/train-reviewed.jsonl.
  SHA256 d61bdfab544dc0d3ba5531e74005940d47b6b6af38fba864dbd5ceefcf948d7a.
- Frozen20 validation hash43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429.
- C four epochs/40steps; D six epochs/60steps; fresh pinned base independently.
  No adapter warm start. Same LR1e-4, rank/alpha16/16, BF16, batch1×8,
  maxseq1024, seed3407, AdamW8bit, cosine/warmup2, masked context, EOS labels.
- Final scheduled checkpoints preselected. Target tokens5653/epoch (+5.00% vs A).

`config.yaml` and draft-v1/v2 artifacts remain intentionally blocked history;
never run them. verify_ready.py verifies active data/config/preflight hashes,
retained-row/validation parity and both authorized post-review transformations.

## Environment and launch requirements

Consult docs/environment-setup-gotchas.md, exp010/GPU-RUN-NOTES.md and exp012
GPU-RUN-NOTES.md before setup. Reuse exp010/setup_training.sh and pinned
requirements; verify actual freeze, CUDA/BF16, disk/cache locations and model
revision. No vLLM installation; adapter inference is HF/Unsloth.

Read W&B credential privately from repo .env only when connecting the supplied
GPU. Do not put it in commands, configs, journal, source bundle or captured logs.
W&B run names: exp013-sft-targeted-80rows-4ep and exp014-sft-targeted-80rows-6ep.
Record independent run IDs, source Git revision, package freeze and hardware.

Use shared exp009/train_reviewed.py with explicit active --preflight-dir,
new --output-dir and --mode. Required actual-batch/environment/W&B checks and
smoke/reload/tiny-overfit gates must actually pass, unless user grants a NEW
explicitly scoped waiver. No such C/D waiver exists. False/waived is not passed.
Gate files bind SHA256 of each training-config.json. Diagnostic adapters never
initialize scheduled SFT. The internal --mode full spelling is historical;
W&B display names are sft, not full.

DO NOT launch exp012/run_pair.py unchanged: it hardcodes old A/B experiment
paths,40step expectations and an A/B-only waiver. Use explicit C/D configuration
and gating; do not relabel those historical runs or extend old authority silently.

Train C then D on one GPU, each independently loading fresh weights. Verify
actual final steps40/60 and epochs4/6. Shared runner retains the last two
epoch checkpoints: C30/40 and D50/60, plus final adapters. Retain resume states.

## Evaluation and recovery

Shared exp009/evaluate_adapter.py --bounded for each final adapter: unchanged20,
thinking off, greedy BF16, repetition penalty1.05,4096token cap, no extra system
prompt. Repeat/time guards are incomplete failures, not EOS; preserve attempts
and do not silently escalate budgets. Verify same rendered prompt/settings as A.

Desired/A/C/D comparison in Argilla comes AFTER inference. Existing reviews
and queues must not be overwritten. See EVALUATION.md for substance/preference,
eight anchors, disputed me-089 reference and19-item sensitivity. User approved
only two TRAINING corrections, not a validation-reference rewrite.

Before user shuts down GPU: recover adapters, retained full checkpoint states,
configs/effective args, source snapshot, hardware/package inventory, gate files,
mask checks, training/inference logs, raw outputs/token IDs/stop reasons and
failures, W&B summary/history/local files. Verify archive and per-file SHA256
locally, reload/completeness evidence and explicit public base-weight dependency.
Append actual outcomes/failures/fixes/costs when measured to EXPERIMENT-JOURNAL.md.
