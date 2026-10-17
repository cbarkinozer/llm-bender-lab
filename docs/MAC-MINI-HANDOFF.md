# Mac mini handoff — 2026-10-05

Current: [frozen Stage A v01 and initial review](../experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/requirements-pilot/STAGE-A-V01.md).
TOML defect confirmed; Mashumaro reference passes 72 feature + 30,008 regression
tests. First v01 suite generated and imported to separate Argilla initial review.
No training or accepted test-first implementation episode has run.

Latest development results: [TOML pilot](../experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/requirements-pilot/README.md).
Context increased to 16,384 after finding Pi's 4,096-token reserve. Thinking-enabled
tests pass 16/20 but are rejected; direct code passes 4/60 feature + 964/964 regression
tests. A suspected reference defect is recorded separately. No training or accepted
test-first implementation episode has run.

Newest refinement: [requirements-first TDD protocol](../experiments/unit-test-generation/qwen3.5-4b/REQUIREMENTS-FIRST-PROTOCOL.md).
Compare direct-code and prompted TDD first; validate/freeze tests before writing
implementation, then study separate SFT and SFT+GRPO training. Preserve independent
hidden grading. DeepSWE EDA and a 20-repository candidate shortlist are prepared.

Latest owner direction (2026-10-17): [20-task research plan](../experiments/unit-test-generation/qwen3.5-4b/RESEARCH-PLAN-20261017.md).
Start with ordinary unit-test generation, existing quality/smell taxonomy and
fresh external task evidence; then GRPO and independent broader-SWE transfer.
Record broader-SWE untouched-model baselines before training. No new generation
or training has run; source selection and protected Pi execution remain pending.

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

## Mac session update — 2026-10-05

Owner confirmed llama.cpp Q4 GGUF deployment and supplied their assertion-quality
paper and early thesis. Primary objective is human-reviewed test quality in
Argilla; passing tests and mutation detection are supporting evidence, not
sufficient quality objectives. See unit-test-generation TODO/design notes.
Pi updated to 1.0.3 and Homebrew llama.cpp 0.5.0 installed. Benchmark and
training recipe remain unfrozen. No RL training or GPU rental has occurred.

Local setup continuation: `exp-000-baseline/run-pi.sh` selects the pinned model
through the Pi CLI; direct llama.cpp is the chosen runtime. Argilla development
UI is on localhost:7900 with credentials in the ignored review/.env. Docker
ARM64 is running; the trusted isolation probe passed. Full grading/Pi sandbox
and benchmark task-mode choice remain pending. See benchmark-audit/README.md.

## Paper pipeline continuation — 2026-10-10

Inspected local `slm_test_generation` at commit
`380b7d362f49d43fd55af5b2f7e015d4fa651e97`; its checkout remains unchanged.
The lab now has a pinned adapter, static provenance/source audit and bounded
container import probe. Twelve adapter tests and 100 existing oracle tests passed.
Ten historical smoke fixtures imported successfully; this does not establish
their semantic correctness or temporal freshness. The 300-row audit flagged
60 unresolved revisions, 60 unresolved licenses and one extraction with a missing
closure binding. See `PAPER-PIPELINE-REUSE.md` for findings and contract triage.
Next: verify contracts, finish protected Pi execution, generate a development
pilot and import original suites/evidence into Argilla. No new generation or
training occurred in this continuation.
