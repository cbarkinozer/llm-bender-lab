# Paired execution — 2026-10-03

User explicitly waived smoke/tiny-overfit tests for both runs and requested
uninterrupted SFT, inference, backup and Argilla preparation. New actual-batch
checks and authenticated W&B remain mandatory. Gate files must mark skipped
checks false/waived, not passed. Pre-SFT reload is waived with smoke; successful
post-SFT inference will establish that saved adapters load.

Direct endpoint 212.83.33.57:42073; proxy ssh8.vast.ai:15830. RTX4090 24GB,
driver580.173.02, Ubuntu24.04.4, 80GB disk. Existing local id_ed25519 works.
Instance-only public key is accepted by server, but Windows client initially
failed to sign despite valid unencrypted matching key; do not claim server key
was absent. Credentials and private keys are never copied into experiment logs.

Reuse exp010/setup_training.sh unchanged, including historical venv name
/workspace/.venvs/exp010-train and exact requirements-exp009.txt. This directory
name is not an experiment identity. No vLLM. Caches under /workspace.
Source commit, package freeze, logs, hardware, gate evidence, arguments and all
retained checkpoints must be captured in the local paired artifact backup.

run_pair.py trains A then B from fresh pinned weights independently, then runs
bounded non-thinking evaluation for each. Primary candidates are final epoch4;
40 optimizer steps each. Diagnostics do not initialize either scheduled SFT.
The old planning/CPU documents describe gates before this explicit waiver;
this execution note records the new user authority without editing frozen data.
