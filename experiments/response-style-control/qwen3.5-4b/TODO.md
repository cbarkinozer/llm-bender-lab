# Response-style-control TODO

Updated: 2026-10-03. User approved preparation of the paired A/B design.
No GPU training has started; B still requires human approval of 24 new targets.

## Immediate SFT decisions

- [x] Keep the existing 20-item development set. Use me-049, me-050, me-059,
  me-069, me-070, me-079, me-089 and me-090 as the user's highest-signal items;
  retain the other 12 as lightweight controls. Do not turn these into training
  examples or claim an independent final-test score.
- [ ] Prioritize groundedness, useful reasoning, natural Turkish, selective
  clarification and neutral/non-anthropomorphic interaction over cosmetic style.
  Plain prose remains a desired default; unnecessary bold/headings/emojis are a
  separate style metric, not proof of task failure or reasoning quality. Preserve
  useful lists and explicitly requested Markdown/code/structured formats.
- [x] Preserve the approved reviewed-v2 80/20 files. Broad new validation-set
  authoring and rewriting already-good targets are deferred. User feedback concerns
  generated model answers, not evidence that all reviewed targets are defective.
- [x] Prepare approved paired-run plan: A = exp011, unchanged 80 targets, four
  epochs; B = exp012, retain 56 plus 24 new reviewed scenarios, four epochs.
  This supersedes the earlier same-question target-rewrite proposal. Compare A
  with exp010 and B with A. Cosine duration and B token-exposure caveats are recorded.
- [x] CPU-check original hashes, new-scenario overlap, tokenization, native EOS
  and masks. A local preflight passed; B draft preflight passed but is not trainable.
- [ ] User: review [24 new B answers](http://127.0.0.1:6900/dataset/0e41d340-72a7-4643-a4ec-6c58917873ce/annotation-mode?page=1&status=pending).
  Accept or rewrite each; resolve rejected questions. Existing 56 need no new review.
- [ ] Export/freeze the completed B review, recompute token exposure and commit it.
- [ ] Obtain GPU; run genuine GPU gates, then fresh-base A and B sequentially.
  Download and verify all artifacts before pod termination. No implicit reuse of
  exp010's LR-only smoke/tiny-overfit waiver.
- [x] Inspect saved rendered prompts and label masks. Current
  prepare_training.py masks the entire non-thinking generation prefix, including
  its empty think block; supervised_text samples contain answer + native EOS.
  This is not evidence that thinking capability is preserved, nor proof of collapse.
- [ ] On the next GPU, use a small identical base/adapter thinking-on/off probe
  set; log raw output, final_answer_emitted, native EOS, truncation, repetitions,
  reasoning/final token counts and actual rendered input. Use enable_thinking,
  not Qwen3 slash commands, for Qwen3.5. Keep this diagnostic separate from the
  established non-thinking development comparison.
- [ ] Do not increase rank, batch, LR and duration together. Our existing adapter
  targets include attention projections and MLP gate/up/down projections. No
  evidence currently establishes rank-16 capacity as the bottleneck. FullFT-to-
  LoRA LR multipliers do not multiply our existing LoRA LR; short-run findings
  from other models/objectives remain hypotheses, not universal settings.

## Planned: agentic RL / multi-harness RL

- [ ] Q-010: agentic RL pilot, explicitly requested by the user; backlog, not started.
  Reference: [FineEnvs multi-harness RL introduction](https://huggingface.co/spaces/FineEnvs/multi-harness-rl#introduction).
- [ ] Read the complete implementation/training sections and pin source revisions
  before selecting dependencies or renting a GPU. The introduction was inspected;
  compatibility/resource requirements have not yet been established for our 4B model.
- [ ] Start with one sandboxed, objectively verifiable task family and one harness;
  establish a frozen-weight baseline before RL. Define task success, tool-call
  validity, stopping, timeouts, cost and reward-hacking checks.
- [ ] Compare frozen weights and RL under the same harness and rollout budget.
  Later compare single-harness and multi-harness training with matched budgets,
  unseen tasks and an unseen-harness transfer check. Do not conflate better
  runtime scaffolding or extra inference compute with weight-training gains.
- [ ] Preserve trajectory/tool logs, rewards/verifier versions, configs, model and
  environment revisions, adapters and recovery artifacts. Agentic RL is a separate
  research track, not a replacement for the current Turkish SFT diagnosis.

## Sources and scope

- [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/): checked 2026-10-03;
  distinguish its loss-based SFT experiments and math RL results from our Turkish
  behavioral evaluation. Its fixed-alpha/constant-schedule setup is not our recipe.
- [Official Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B): Qwen3.5
  does not officially support Qwen3's /think and /nothink soft switch.
- Further reading supplied by the user about reasoning collapse, CPT and GRPO
  remains unverified unless an exact primary source is recorded. Do not treat
  those summaries as established diagnoses of our runs.
