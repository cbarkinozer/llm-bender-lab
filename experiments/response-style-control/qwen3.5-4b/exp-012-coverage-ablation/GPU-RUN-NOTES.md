# Paired execution — 2026-10-03

User explicitly waived smoke/tiny-overfit tests for both runs and requested
uninterrupted SFT, inference, backup and Argilla preparation. New actual-batch
checks and authenticated W&B remain mandatory. Gate files must mark skipped
checks false/waived, not passed. Pre-SFT reload is waived with smoke; successful
post-SFT inference will establish that saved adapters load.

Direct endpoint 212.83.33.57:42073; proxy ssh8.vast.ai:15830. RTX4090 24GB,
driver580.173.02, Ubuntu24.04.4, 80GB disk. Existing local id_ed25519 works.
Instance-only public key is accepted by server, but Windows client initially
failed to sign because Windows generation unintentionally set a quote-character
passphrase; the later SSH fix below repaired it. Do not claim the server key
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

## Observed results

Runtime source: 8b49f72. Exact installed 102-package freeze matches exp010.
Python3.11.16, Torch2.7.1+cu128, Transformers5.5.0, Unsloth2026.9.6.
Both actual-batch checks verified all 100 row representations and padding masks;
21,233,664 trainable parameters each. No diagnostic training was run.

A completed 40 steps / four epochs in219.7631s, mean train loss1.1178216442.
B completed 40 steps / four epochs in128.5674s, mean train loss1.4069858700.
Losses on different training targets are not a data-quality comparison. A's initial
kernel compilation cost makes training runtimes non-comparable as model throughput.
Final adapters and retained checkpoint30/checkpoint40 saved for each arm.

W&B states verified finished, histories and configs downloaded on the pod:
- A: https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/93a090aa
- B: https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/3f3844d7

Primary inference: 20/20 native EOS per arm, zero guard or budget stops. Greedy,
BF16, repetition penalty1.05, no extra system prompt, thinking disabled, batch1,
4096 maximum output budget. Input token IDs, desired targets, template hash and
generation settings match between A/B. Adapter weights are different.
A median output36 tokens, maximum394, total1297; B median29, maximum178,
total905. These describe length/stopping, not correctness or Turkish quality.
Saved base outputs remain contextual references from the old vLLM backend.

Local verified primary output copy:
C:/Users/cbark/Documents/llm-bender-artifacts/exp-011-012-paired/review-results.
Argilla has20 records in exp-011-012-paired-validation-20,
UUID e2c4f7ab-8d50-401f-b68c-7eda6323c264. All fields verified via API, UI HTTP200;
older reviews preserved. Comparison exposes desired_answer, answer_A, answer_B
and termination. No human preference labels have been invented.

Setup: reused pinned requirements; official causal-conv1d wheel took about6m36s
to download but passed its recorded SHA256. No resolver/library/GPU error. New
instance-key public half matched the private half and server accepted its offer;
BatchMode client did not send a signature. Existing user key connected normally.
No claim that the new public key was absent from the server.

## Supporting probes

Completed16 cases: two development prompts me-070/me-079, thinking on/off for
base/A/B (12 cases), plus retained training IDs me-041/me-051 on A/B (four cases).
Raw output, rendered inputs, token IDs, reasoning/final token counts, termination
and final_answer_emitted are preserved. No expanded-budget retries.

Base me-079 thinking-on exhausted4096 tokens without a final answer. A's same
thinking-on probe hit the180-second guard at3238 tokens without a final answer.
B emitted a final answer and native EOS for both thinking-on probes (1091 and
1732 output tokens). All other cases reached EOS and emitted final answers.
This tiny reused development sample does not establish global preservation or
diagnose adapter reasoning collapse; base also failed. Training fit is separate
from validation and no target-match quality score is invented.

## Durable recovery

Local root: C:/Users/cbark/Documents/llm-bender-artifacts/exp-011-012-paired.
Archive exp011-exp012-backup.tar.gz:862,934,687 bytes, SHA256
4706aa58413f60c9f778ebdff34aab459f3192c5de630085a3e9b2b3588cbc1a.
Whole-archive hash matched remotely and locally; safe relative member paths,
no symbolic/hard links; extracted to backup-extracted. All141 indexed files
verified by size/SHA256, both final adapters matched evaluation manifests,
checkpoint30/40 resume states exist, and paired inputs/targets/settings match.

Includes adapters, both retained checkpoints per arm, optimizer/scheduler/RNG,
effective arguments, source configs, invocations, gates/waiver, setup/train/
inference/diagnostic logs, package freeze, hardware, rendered inputs/masks,
raw outputs/token IDs/failures, W&B history/config/summary and dereferenced logs,
exact source bundles/helper files and validated CUDA wheel. Public pinned base
weights remain a download dependency, not an offline/bitwise reproduction claim.
No important run artifact remains only on the pod; GPU can be destroyed.

### SSH fix

Confirmed cause: Windows empty-argument quoting during ssh-keygen creation
accidentally left the new key encrypted with literal quote characters rather
than an empty passphrase. Server had accepted the matching public key, but the
BatchMode client could not sign. Removed unintended encryption interactively
without changing the public key, then verified both direct and proxy SSH using
the instance-only key. Never print private-key contents or store them in Git.
