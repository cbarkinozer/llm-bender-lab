# Mac mini handoff — 2026-10-05

## Resume here

Read [unit-test-generation plan](../experiments/unit-test-generation/qwen3.5-4b/README.md)
and its [TODO](../experiments/unit-test-generation/qwen3.5-4b/TODO.md).
The owner chose **Python unit-test generation only**, not general bug fixing,
production-code implementation or more Turkish SFT. Primary deployment: Mac mini
M4, 24 GB unified memory, Q4 GGUF, llama.cpp, Pi coding agent. RL is preferred
for the next learning pilot; the environment/verifier baseline comes first.

Continue prompt for the next assistant:

> Read AGENTS.md, docs/MAC-MINI-HANDOFF.md and the unit-test-generation plan/TODO.
> Occam is closed. Inspect this Mac's Pi/llama.cpp environment and prepare a
> frozen 4B thinking-off/on pytest-generation baseline with read-only production
> code, protected verifier and grouped holdout. No RL training or GPU rental yet.

## Repository transfer

Git commits do not sync by themselves. Ensure the Windows handoff commit is on
GitHub (`git push origin main`), then on the Mac use an existing clean checkout:

```sh
git pull --ff-only
```

Or create a fresh checkout in a chosen projects directory:

```sh
git clone https://github.com/cbarkinozer/llm-bender-lab.git
cd llm-bender-lab
git status --short
```

Do not reset/overwrite local edits. If pull cannot fast-forward, inspect divergence.
The existing Windows adapters/recovery directories and `.env` are not in Git.
Never copy credentials into these notes or publish them; configure needed tokens
locally via login/secret storage. The local baseline need not use W&B/HF write keys.

## What is available without transferring Windows artifact folders

- Occam adapter: https://huggingface.co/cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora
- Dataset: https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT
- Selected weight revision: `1a8a07ff2a29f51a2b6a635a8c219191a7377996`.
- Dataset revision: `947850d484c71f657dbec2bb7e3d356cb5fb23e3` (104 train / 20 reused dev).
- Both repos verified public on 2026-10-05. Public visibility is not a rights audit.
- Current public cards are snapshotted in `docs/publication/OCCAM-MODEL-CARD.md`
  and `OCCAM-DATASET-CARD.md`; model README may have a newer commit than weights.
- Turkish journey draft: `docs/publication/BLOG-TR.md`.
- Publication/auth/verification notes: `docs/publication/PRIVATE-UPLOAD-20261005.md`.

No need to download Occam weights for the new baseline; use the untouched model.
Git has configs, scripts, metrics and journals, not full historical GPU archives.
Original Windows archives/weights remain outside Git; public HF releases do not
replace all historical training/benchmark logs. Preserve those archives separately
if needed. Publication helper scripts contain Windows paths and perform writes:
do not rerun them to resume this Mac project.

## First session on the Mac

1. Read relevant experiment/evaluation/dataset/reproducibility guides in AGENTS.md.
2. Inventory architecture/macOS, available memory, Python, Pi and llama.cpp versions;
   no installs/downloads selected on Windows. Pin working versions after inspection.
3. Locate any existing 4B/9B GGUFs rather than redownload blindly. Record actual
   repository/file/revision/hash and Q4 variant; inspect template and tool parser.
4. Verify Pi can generate a valid tool call through llama.cpp, and thinking really
   switches at the backend/template. Do not assume a Pi UI toggle guarantees it.
5. Measure one-model-at-a-time memory/latency under bounded context. The advertised
   model context size is not the chosen agent context or a 24 GB memory guarantee.
6. Build test-only sandbox and independently validate task contracts/correct code.
7. Freeze licensed tasks, grouped splits, mutation grading and total rollout budgets.
8. Run frozen 4B off/on; only then optional 9B reference and RL feasibility work.

Avoid reusing Occam greedy/non-thinking settings without a new agent protocol.
Keep thinking tokens within explicit total budgets; preserve raw model/tool outputs,
rendered prompts, code diffs, test/grader reports, failure categories and resource use.
No test-set feedback in rewards/teacher generation; dev and train roles are explicit.

## Training distinctions to preserve

- Executable reward on 4B's own attempts = proposed RL path.
- Copying verified 9B trajectories = distillation/SFT, a different objective.
- More thinking tokens = inference compute change, not a weight-training gain.
- Frozen Mac Q4 rollouts are not automatically on-policy GRPO training data.
- Q4 GGUF deployment does not imply llama.cpp Q4 training support. Current native
  training example is WIP and FP32-limited; MLX quantized LoRA is a separate format.
- Main expected RL training path is compatible original weights on rented NVIDIA,
  followed by conversion/quantization checks and fresh Mac deployment evaluation.
- MLX local training is an optional later learning exercise; Qwen architecture/export
  support, memory and adapter conversion still need verification.

## Completed versus pending

Completed: Occam exp016/F selection, external paired500 and blind human30,
recovered essential artifacts, adapter/dataset uploads and file hash verification.
The public model card includes three actual cherry-picked development comparisons;
those are not training targets or fresh independent evaluation evidence.

Pending: owner finishes blog and provenance/provider-terms review; local deployment
loading verification; new unit-test task corpus/verifier, baseline and RL stack.
No unit-test-generation training has run. Do not invent benchmark scores or mark
the new planned experiment ready before artifact/task/protocol checks.
