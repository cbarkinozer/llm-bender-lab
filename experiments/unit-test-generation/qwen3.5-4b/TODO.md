# Python unit-test generation TODO

## Current decision

- [x] Record scope: Python/pytest unit-test generation only; no production fixes.
- [x] Record Mac mini M4/24 GB, Pi, llama.cpp, Q4 deployment preference.
- [x] Preserve Occam result and publication notes; no more Turkish SFT now.
- [x] Create planned baseline and portable Mac handoff, without inventing results.

## On the Mac — no GPU rental needed yet

- [ ] Finish/publish the Turkish blog; optional parallel paperwork, not RL data.
- [ ] Clone/pull repository and read `docs/MAC-MINI-HANDOFF.md`.
- [ ] Inventory macOS/architecture/free memory, Pi and llama.cpp versions.
- [ ] Choose and pin the exact 4B GGUF Q4 variant/hash and native template.
- [ ] Confirm Pi tool calls and thinking on/off end to end with raw request logs.
- [ ] Build isolated test-only workspaces; protected source/grader, no secrets/network.
- [ ] Select independently sourced, licensed deterministic Python task families.
- [ ] Freeze grouped train/dev/test split and contamination checks before rollouts.
- [ ] Implement verifier correctness, assertions, mutation scoring and anti-cheating checks.
- [ ] Test verifier against empty/skipped tests, incorrect assertions, source edits,
  grader access, mutant timeouts, equivalent mutants and forged exit codes.
- [ ] Freeze prompts, allowed tools, context, sampling, time/token/tool budgets,
  seeds, repetition/EOS policies and measurement/aggregation rules.
- [ ] Run paired frozen 4B thinking off/on; preserve all successes and failures.
- [ ] Optionally run 9B thinking-on on the same tasks as a larger reference.
- [ ] Inspect trajectories and reward distribution; diagnose zero-success tasks.

## Only after baseline

- [ ] Select/pin compatible agentic RL stack; validate the Pi rollout/training bridge.
- [ ] Record one verifiable-reward hypothesis and explicit compute/regression budgets.
- [ ] Prepare training-only rollouts/task environments and native thinking/action masks.
- [ ] Request GPU only after compatible recipe and estimated cost/memory are known.
- [ ] Train one conservative 4B LoRA RL pilot and compare against the same starting model.
- [ ] Verify export/merge/quantization and re-evaluate actual Mac Q4 deployment.
- [ ] Record held-out correctness/mutation score, tool validity, latency/tokens,
  regressions, costs, failures and complete recoverable artifacts.

## Deferred, not prerequisites

- [ ] 9B-to-4B verified reasoning/trajectory distillation as a separate experiment.
- [ ] Local MLX quantized LoRA exercise; architecture/export feasibility first.
- [ ] Multi-harness transfer after one working harness and verifier baseline.
- [ ] Occam v2: faithful summaries, de/da, correct-input preservation; fresh holdout.
