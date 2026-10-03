# C/D execution — 2026-10-03

New user instruction explicitly waives smoke/tiny-overfit for this C/D pair and
requests uninterrupted SFT,20-question inference per arm, comparison and verified
recovery. Pre-SFT diagnostic adapter reload is waived with smoke, not passed.
Actual-batch masking and authenticated W&B remain mandatory. Saved adapter
reload will be verified by post-SFT inference. No diagnostic adapter initializes SFT.

Proxy ssh3.vast.ai:19764 accepted existing user key. Initial noninteractive host
trust check failed; first-contact accept-new recorded host key, then login worked.
Direct endpoint supplied:83.27.30.232:43254. Prior observation: RTX4090 24GB,
driver580.178.04,80GB available disk. Recheck at setup; no vLLM installation.

Reuse exp010/setup_training.sh and pinned requirements. Historical venv name
exp010-train is not the experiment identity. C4epochs/40steps, D6epochs/60steps,
same frozen80 rows, fresh pinned base independently. Descriptive W&B run names
come from reviewed configs, no full prefix. Secrets stay in stdin/process memory.

Current status: launch preparation. No training/inference success claimed yet.
Record actual outcomes, stop reasons, fixes and verified backups here and in journal.
