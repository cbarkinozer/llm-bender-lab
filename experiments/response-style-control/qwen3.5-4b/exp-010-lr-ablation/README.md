# exp-010-lr-ablation

Status: user-approved recipe; local preparation, GPU run pending.

Hypothesis: doubling LR from 5e-5 to 1e-4 gives the existing reviewed targets
more behavioral influence without worsening Turkish/task correctness.
Exp009 was rejected by the user for persistent base-style behavior, verbosity,
Markdown/emojis and poor Turkish. Underfitting is a hypothesis, not established.

Only training change: learning rate. Same fresh pinned Qwen3.5-4B base,
same reviewed-v2 80/20 identities and hashes, same labels/tokenization,
two epochs, 20 optimizer steps, effective batch 8, rank/alpha 16, BF16,
seed 3407, cosine schedule, two warmup steps, no packing or replay.
Full configuration is config.yaml (JSON-compatible YAML).
Dataset is referenced, not rewritten or re-split; old 958 rows remain excluded.

Shared implementation: ../exp-009-minimal-edit/train_reviewed.py. Pass this
experiment's --preflight-dir training-preflight-v1; source dataset paths in
the config resolve against that shared runner's exp009 directory.
The shared runner now reads experiment identity from the config for W&B naming;
this changes tracking labels only, not training math.

Before full training: GPU representation, LR-specific smoke/save/reload,
tiny-overfit and W&B checks, evidence gates matching the new config hash.
All diagnostic and full runs start fresh; never continue the exp009 adapter.
Save both epoch checkpoints, effective arguments, CLI/environment, logs,
optimizer/RNG state and source revision. Download and verify artifacts before
pod termination. No credentials in logs, Git or manifests.

After training: generate all 20 development questions for both epoch adapters
using the existing evaluate_adapter.py, Unsloth/Transformers BF16, greedy,
repetition penalty 1.05, non-thinking, no extra system prompt, native EOS and
4096/8192/16384 budgets. Use separate output directories. Existing base answers
remain available; their vLLM backend difference remains explicit. Compare with
exp009 on identical settings. This is not a blind/independent final test.

Primary outcome: user-visible desired behavior, not lower loss or shortness.
Inspect correctness, natural Turkish, necessary detail, formatting/emojis,
unsupported claims, anthropomorphism and clarification loops. Neither checkpoint
is automatically the best. Do not change data/rank/epochs during this LR test.

Rebuild/verify local artifacts: python prepare.py (idempotent, refuses differences).
GPU was unreachable on 2026-10-03 at the last exp009 direct SSH endpoint.
No exp010 training has started; a reachable instance is needed.
