# exp-000-baseline

## Status

Planned. Configuration is a non-executable planning record; revisions, GGUF
artifact, tasks and budgets are not frozen. No model has been run on the Mac.

## Goal and hypothesis

Establish whether untouched Qwen3.5-4B can generate executable, mutation-sensitive
pytest tests through Pi/llama.cpp on a Mac mini M4/24 GB. Compare thinking off/on
under matched total allowances before selecting an RL training mode.

## Parent and scope

New unit-test-generation domain; no training or Occam adapter inheritance.
Production code read-only; only generated unit tests may change.

## Model, data and evaluation

Qwen3.5-4B Q4 GGUF, artifact/revisions pending. Grouped task split pending.
Primary proposed measure: mutation detection gated on passing against correct
code; report collection/assertion validity, correctness, tool success and cost.
Optional 9B reference is a separate model-size comparison, not an RL improvement.

## Results / regressions / conclusion

None. Mac feasibility, baseline quality and training compatibility are unmeasured.

## Next step

Follow [Mac handoff](../../../../docs/MAC-MINI-HANDOFF.md), complete the verifier
and artifact/protocol freeze, then run the baseline. Do not train this draft.
