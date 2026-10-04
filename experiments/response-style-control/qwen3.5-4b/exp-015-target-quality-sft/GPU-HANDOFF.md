# E/F execution handoff — 2026-10-04

Authorized pod: direct81.27.69.180:52991, fallback ssh7.vast.ai:36350.
RTX4090 24564MiB, driver565.77 (nvidia-smi maximumCUDA12.7).
Existing project SSH key authenticated; private key and W&B credential are not
part of source/artifacts. Pod is not terminated automatically.

Pinned C/D setup script reused without resolving newer packages. Managed
Python3.11.16, Torch2.7.1+cu128, Transformers5.5.0, Triton3.3.1,
Unsloth2026.9.6, official hash-verified causal-conv1d wheel. CUDA availability,
BF16 and Unsloth import passed on this driver; this does not yet prove training.
CUDA12 minor-version compatibility is being tested by actual model execution,
not inferred solely from nvidia-smi's reported maximum toolkit version.
Standalone setup source/config/log preserved under /workspace. Its relative
requirements lookup was satisfied at /exp-010-lr-ablation/requirements-exp009.txt;
the file is the exact previous freeze. No vLLM installed.

Run reviewed configs only. `run_pair.py` creates
`/workspace/exp015-exp016-runs`, never overwrites, receives W&B key through stdin,
detaches with credentials only in process memory, and removes WANDB_SERVICE*
before trainer children. Outputs stay outside the clean source worktree.
Do not print credentials, copy .env, or capture full process environments.

Canonical base/C32 generation precedes E/F full training. C adapter comes from
the locally verified prior recovery, not a freshly trained substitute. Each arm
uses fresh model processes; F is not initialized from E. Genuine representation,
3-step smoke, 40-step16-example diagnostic overfit and saved-smoke-adapter
reload/finite forward pass are required. No earlier user's waiver is inherited.
Diagnostic runs have no W&B reporting and do not count as experimental outcomes.

Later user instruction on the same2026-10-04 explicitly waives smoke/tiny for
this pair. E's genuine checks were already completed and E SFT was running;
parent orchestration only was SIGSTOPped to prevent launching F diagnostics.
E training continued uninterrupted, finishing40steps/4epochs in110seconds.
Original parent terminated after E finished; state-aware resume skips completed
base/C/E stages, performs F actual masking, reuses this pod's genuine E reload
proof for identical base/LoRA/implementation, waives F smoke/tiny without claiming
they passed, and validates final F adapter by inference. No training restart,
checkpoint selection or hyperparameter/data change. Source revisions and original/
resumed pipeline logs are preserved separately. New waiver policy is restricted
to E/F smoke/tiny only; masking/W&B/reload are not waived.

Full E/F each40 optimizer steps, checkpoints/eval every10, final40 preselected;
trainer asserts actual global_step40. Added runtime exposure trace records actual
training microbatches/supervised tokens, excluding evaluation/collator diagnostics.
Trace does not claim bitwise deterministic training. All32 evaluation outputs
use evaluate_models.py with identical frozen protocol, prompt token/render parity
checked by launcher. Native-EOS failures remain failures, not hidden retries.

CPU test suite12passed, approved-data hash/representation checks passed; no GPU
training result yet at creation of this handoff. After completion preserve all
logs, config/masks/template/token IDs, W&B history/summary, checkpoint optimizer/
scheduler/RNG states, adapters, source bundle and setup freeze. Download externally
and verify file/archive SHA256 before telling user GPU is safe to delete.
Blind comparison mapping must not be shown in Argilla; review semantic quality,
Turkish and style separately. Human review is still needed to conclude hypotheses.
