# SWE agent — Gemma 4 E4B (Kaggle Gemma 4 Developer Agent)

Domain: `swe-agent`. Base model: `gemma-4-e4b-it-qat-w4a16-ct` (the only E4B variant the competition allows).
Created 2026-11-21. Competition: https://www.kaggle.com/competitions/gemma-4-developer-agent
(final submission 2026-12-02, entry/merger deadline 2026-11-25).

## Goal

Raise the SWE-bench-style pass rate (patch applied, hidden pytest tests pass) of Gemma 4 E4B inside the
competition harness (offline, ~5.5 min/task, 12 h total, tools fixed by the harness).

The goal is **learning well-known methods, not winning**. Target: reach roughly 60-80% of the best
known E4B public score, using only approaches other participants and papers report as working.
Reference points (public LB, 2026-11-19): small-model (E2B/E4B) leaderboard top = 0.12, most teams
0.08-0.10; best overall (31B) = 0.24. So the working target here is about **0.07-0.10**.
Absolute scores of 0.6-0.8 are not realistic for any model in this harness (teachers like DeepSeek V4 Pro
solve ~48% locally; union of 4 runs ~59%) and are not the target.

Rules of engagement: skip anything others report as failed (graph tools, multi-agent critics,
big-teacher SFT with tiny data, long thinking), prefer popular recipes, few experiments, standard
hyperparameters. Judge deltas over several seeds, never one run.

## Data and scope facts

- Public set: 129 tasks, **Python only, 4 repos** (fastapi, rich, requests, httpx). Hidden test set is
  built by a similar pipeline. Multi-language is irrelevant for this competition.
- Files: `tasks.jsonl` (problem_statement, hints_text, patch, test_patch, base_commit), `snapshots/*.tgz`,
  `wheels/` (offline deps), `graphs/` + `embeddings/` (not used), `docker/`, `HARNESS_README.md`.
- Local machine has a GTX 1650 (4 GB) and ~2.8 GB free on C:. **All inference and the large downloads
  run on vast.ai** (see `docs/environment-setup-gotchas.md` section 14 and the "Vast.ai inference
  backend preference" section). Only small files are downloaded locally.
- Split plan (by repo, since there are only 4 groups): develop on fastapi + requests (+ the 1 httpx task),
  hold out rich (48 tasks). Frozen before any tuning.

## Experiment registry

| ID | Status | Main Change | Target Score | Notes |
|---|---|---|---:|---|
| exp-000-baseline | paused | untouched E4B, organizer config, 3-5 seeds | - | owner paused 2026-11-21; needs a Vast.ai instance + Kaggle token on it |

Planned next (not created yet, one hypothesis each): `exp-001-harness` (training-free harness and
prompt changes), `exp-002-teacher-diff` (larger-model behavior comparison, diagnostic only),
`exp-003-*` weight training only if exp-001 misses the target.

## Research notes: what others did (read 2026-11-21)

Sources: competition discussion threads, public notebooks, arXiv. Numbers are single-run, from
different local sets and harnesses; treat as direction, not truth. Only parts of some papers were readable.

### Works (adopt)
- **Training-free config tuning gets the top public scores (0.20-0.22 on 31B).** The "3 tweaks" notebook:
  40 tool calls (not 28), issue text pinned at the end of the system prompt (survives context
  compaction), one-word answer after `submit_patch`, forced edit by ~12th call, targeted tests only
  (never bare `pytest`), never edit tests, no graph tools.
- **Keep the flat tool surface; put guards behind the tools** (AST/syntax check, snapshots). Halved timeouts
  and cut empty patches ~40% (Japan OpenData Lab, E4B). Wrapping tools in custom nested tools multiplied
  argument errors 1 -> 29.
- **Enforce budgets in code, not prompts.** "Finish in 9 calls" was ignored in 61% of tasks.
- **E4B thinking budget: small (0-1024).** E4B think=4096 scored 10/114 vs 16/114 zero-think; 768-1024 was
  the sweet spot. Do not disable thought output entirely (tool-JSON errors 3 -> 132) and do not shrink
  `max_output_tokens` (4096 -> 2560 doubled edit errors). For 31B the opposite holds: thinking on is
  essential (23 vs ~50 of 129).
- **Measure with repeats.** Same config, temperature 0, 10 runs: 11-15 solved of 114 (SD 1.5). 31B flips
  ~15% of tasks between identical runs. Pass@5 (22.8%) >> pass@1 (~12%): capability exists, selection
  is the bottleneck.
- **Papers that worked at 4B:**
  - Revisiting DAgger in the Era of LLM-Agents (arXiv 2605.12913), Qwen3-4B-Instruct on SWE-bench
    Verified: base 11.2 -> SFT 22.9 -> OPD 23.4 -> DAgger-style 27.3. Student rolls out, teacher labels
    the student's own states (Qwen3-Coder-30B-A3B, SWE-Gym ~2.3K tasks, OpenHands). GRPO from the weak
    base gave only +0.4 (sparse reward).
  - Arctic-SWE (arXiv 2610.24914), Qwen3.5-4B RL: 47.4 -> 62-65 on Verified, but 8xB200, 131K context,
    100 turns. Transferable: curate data and tighten weak tests, gate malformed turns in the reward,
    expect forgetting after the peak (stop early).
  - Failure analyses (SWE-agent, OmniCode, Coherence Collapse): small models fail on tool syntax;
    str_replace-style edits plus lint/syntax check on edit help; many failures happen after the right
    file is found, i.e. edit quality, not only localization.

### Does not work / skip
- **Graph tools** (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`): embeddings are keyed by
  node id so free-text queries return empty; no gain in ablations (31B, 129 tasks); top notebooks forbid them.
- **Critic / arbiter / multi-agent stages** on small models: every layer both fixed and broke tasks.
- **Forcing the agent to write its own repro test first:** 6.0 -> 3.5 (4B).
- **"Prefer the patch that passes existing tests":** ~34% of tasks are spec changes where old tests assert the
  buggy behavior; ~66% already pass before the fix, so passing tests prove little.
- **Small-data SFT/DPO distilled from a 31B teacher** lost to the raw base (4/20 -> 3/20; DPO 1/20). Static teacher
  trajectories are off-distribution for the student. CPT is not expected to help (failures are edit format and
  localization, not knowledge).
- **12B instead of E4B/31B:** slower per task in practice, solved less than half of 31B.
- **LoRA is the only allowed weight change** here, and one paper found LoRA worse than full SFT. Keep that risk in mind.

### Known failure modes of E4B (from other participants)
Wrong file edited (13 of 31 local tasks), whole-file overwrite with `write_file`, `"""` docstrings inside
`old_string` mangled by vLLM's gemma4 tool-call parser (ADK rejects the call, model retries up to 27x),
empty patches, timeouts near 250-330 s, multi-file coordinated fixes almost never solved.

### Harness gotchas
`run_command` is synchronous (run one task per process when timing matters); ADK v1.36 ParallelAgent is
broken; budget on the grader is 5.5 min/task (120 tasks x 5.5 = 11 h). Local timing differs from Kaggle 4xL4:
calibrate (31B: ~900 s per 1M tokens on 4xL4).

## Harness facts (HARNESS_README.md, read 2026-11-21)

- Tools (9): `run_command`, `submit_patch`, `get_status`, `read_file` (150 lines / 10k chars), `edit_file` (3-tier
  exact/flexible/regex match; unique match unless `allow_multiple`), `write_file`, 3 graph tools (unused).
  `submit_patch` and `get_status` are free; others count toward `max_tool_calls`.
- Serving on grader: vLLM TP=4, `max_model_len` 32768, `gemma4` tool and reasoning parsers, max LoRA rank 128,
  submission < 3 GiB. Context compaction at 14,336 tokens (every 15 events, keep 5).
- Defaults: 100 tool calls, 500 turns, 60 min session, 300 s per command. `eval_config.yaml` can override budgets.
- Unsubmitted work is recovered automatically (`git diff`), so a patch exists even on timeout. Test files and
  `pytest.ini`/`conftest.py`/`pyproject.toml` hunks are stripped from the patch. Put scratch files in `/tmp`.
- 3 nudges max when the model ends a turn without a tool call; a cut-off `<|tool_call>` gets a "split the edit" nudge.
- Pass = hidden pytest exit 0 with JUnit: all required tests passed, none skipped. Patch apply has 4 fallback passes.
- Local runner: `swegemma eval --tasks tasks.jsonl --snapshots-dir snapshots --submission-dir ... --sandbox docker|subprocess`
  (subprocess sandbox works without a Docker daemon, useful on vast.ai containers).
- **The harness IS available** (corrected 2026-11-21; first I only checked PyPI): Kaggle dataset
  `metric/gemma-4-developer-agent-wheelhouse` (0.88 GB, 41 wheels, cp312/linux): `swegemma-0.2.11`,
  `adk_submission-0.2.13`, `adk_eval_core-0.1.0`, `google_adk-1.36.1`, `vllm-0.19.1`, `transformers-5.13.1`,
  flashinfer, compressed_tensors, etc. The pinned "Getting Started" notebook (ryanholbrook) installs it with
  `pip install --no-deps --force-reinstall *.whl` (restoring `+cu128` in wheel names) on top of the Kaggle GPU image,
  then calls `swegemma.models.load_tasks`. So we use the real harness; no own harness. Wheels target Python 3.12.
  Docker image `swebench-sandbox:latest` is built from `docker/Dockerfile.public` (python 3.13-slim) with the
  public `wheels/` copied in.
- Hidden test set = ~120 tasks from **private repos** (half public/half private LB split), so the 4 public repos are
  only a proxy: prefer repo-agnostic gains, keep `rich` as an unseen-repo holdout.
- Sample submission (31B + LoRA) uses temperature 0.2, thinking_budget 4096, max_output_tokens 16384, graph tools +
  analyzer sub-agent, 10 tool calls. Its adapters are in `sample_submission/adapters/` (not downloaded).
- Public tasks: fastapi 67, rich 48, requests 13, httpx 1 (httpx is nearly absent, so develop = fastapi + requests,
  holdout = rich). No task has hints. Median problem statement 418 chars.

## Plan

1. Kaggle auth, read `HARNESS_README.md` and `docker/`, download `tasks.jsonl` locally and snapshots/wheels on vast.ai.
2. Local verifier: gold patch passes, empty patch fails, target >=124/129 scorable. Frozen split by repo.
3. `exp-000-baseline`: untouched E4B, organizer config, temperature 1.0, 3-5 seeds, all tasks in the denominator,
   failure classes (empty patch, timeout, bad tool JSON, wrong file, file overwrite).
4. `exp-001-harness`: "3 tweaks" recipe adapted to E4B, small thinking budget, guards behind tools. One change at a time only
   when it moves several tasks.
5. `exp-002-teacher-diff`: same harness with a larger model, compare early behavior (diagnostic, not training data).
6. Weight training only if still short of target: DAgger/OPD-style on E4B's own rollouts, small LoRA, low LR,
   LoRA-scale sweep (0.3-0.7), multi-seed checkpoint comparison. RL last.

## References

- Competition discussion: 760014 (Japan OpenData Lab, 1,800+ E4B trials), 746250 (Ayush Thakur ablations),
  747168 (teacher comparison), 750974 (31B vs 12B vs E4B), 742807 (distillation rules).
- Notebook: "# LB 0.22 | 3 tweaks, 40 tool calls, no training" (bliverrigpdoge).
- arXiv: 2605.12913, 2610.24914, 2602.22124 (SWE-Protege), 2405.15793 (SWE-agent), 2603.24631, 2602.02262.
