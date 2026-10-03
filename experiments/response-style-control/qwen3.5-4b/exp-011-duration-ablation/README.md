# exp-011-duration-ablation — A

Status: trained (four epochs / 40 steps); all 20 primary outputs reached native
EOS. Human comparison is ready; full local backup verification passed.
Execution notes: [paired GPU record](../exp-012-coverage-ablation/GPU-RUN-NOTES.md).

User-approved design, 2026-10-03: train the existing reviewed-v2 80 examples
for four rather than two epochs. Fresh pinned Qwen3.5-4B, LR 1e-4, rank/alpha
16/16, effective batch 8, BF16, max sequence 1024, seed 3407, final-assistant-only
labels, cosine schedule, two warmup steps, no packing/replay. Expected optimizer
steps: 40 instead of exp010's 20. The cosine trajectory extends with the run;
this is the longer-training recipe, not a pure extra-step causal isolation.

Training and validation data remain at exp009/reviewed-v2; no new split or target
edits. All 100 tokenized examples were independently regenerated with the pinned
tokenizer and compared with the saved parent representations. Context/empty think
prefix is masked, final answer plus EOS supervised, zero truncation. This does
not establish preservation of thinking-mode capabilities.

Shared runner: ../exp-009-minimal-edit/train_reviewed.py. Config dataset paths
resolve relative to that runner's exp009 directory. Use this experiment's
training-preflight-v1 directory explicitly. No historical adapter initialization.

Final scheduled epoch-four adapter is the predeclared primary candidate. The
existing shared runner retains the last two epoch checkpoints; save/download
both plus optimizer, scheduler, RNG, effective arguments and logs. Earlier epochs
are not required for primary selection and should not be presented as retained.

Compare with exp010 epoch2-v2 on the unchanged 20 development questions, with
the same bounded Unsloth/Transformers BF16 decoding. See the paired
[evaluation protocol](../exp-012-coverage-ablation/EVALUATION.md). No vLLM install.
Existing base generations used a different backend; disclose this limitation.

GPU actual-batch and W&B checks passed. The user explicitly waived repeat smoke,
pre-training reload and tiny-overfit for these paired runs on 2026-10-03; skipped
checks remain false/waived, not passed. Saved-adapter reload was subsequently
verified by completed inference. This is a new waiver, not inherited from exp010.

Preparation and handoff live alongside B:
[prepare_pair.py](../exp-012-coverage-ablation/prepare_pair.py),
[GPU-HANDOFF.md](../exp-012-coverage-ablation/GPU-HANDOFF.md).
