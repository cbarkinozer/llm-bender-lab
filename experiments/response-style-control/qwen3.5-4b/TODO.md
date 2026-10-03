# Response-style-control TODO

Updated: 2026-10-03. Both A/B SFT runs and primary inference completed. Each
trained 40 steps / four epochs; all 40 primary outputs reached native EOS.
Argilla comparison is ready; supporting probes and full backup are completed.

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
- [x] User: review [24 new B answers](http://127.0.0.1:6900/dataset/0e41d340-72a7-4643-a4ec-6c58917873ce/annotation-mode?page=1&status=pending).
  Accept or rewrite each; resolve rejected questions. Existing 56 need no new review.
- [x] Export/freeze B using hash-bound conversational approval; no Argilla responses
  fabricated or changed. Targets unchanged as approved; token exposure remains +22.47%.
- [x] Obtain GPU and train fresh-base A and B sequentially. Genuine actual-batch
  masking and W&B checks passed; user explicitly waived repeat smoke/tiny-overfit
  and pre-training reload for this pair. False/waived gates are recorded honestly.
- [x] Reload both saved adapters and generate the unchanged 20 development
  questions per arm: all 40 reached native EOS, identical primary settings.
- [x] Prepare and verify [desired/A/B Argilla comparison](http://127.0.0.1:6900/dataset/e2c4f7ab-8d50-401f-b68c-7eda6323c264/annotation-mode?page=1&status=pending).
  Existing review queues and annotations are preserved.
- [x] Download and verify all artifacts before pod termination: archive SHA256
  and all141 indexed files verified locally, including retained resume state.
- [x] Review all20 submitted A/B judgments and freeze the response snapshot.
  A preferred7, B5, tie6, neither2; see [experiment journal](EXPERIMENT-JOURNAL.md).
- [x] Prepare C/D12-row draft, blocked configs and CPU tokenization/leakage audit:
  68 unchanged A rows +12 replacements, four versus six epochs; tokens/epoch +3.60%.
- [ ] User: [review shared12 C/D candidates](http://127.0.0.1:6900/dataset/c0dc183f-e552-4a7d-9267-08211b88df94/annotation-mode?page=1&status=pending).
  Accept/rewrite; reject with notes if prompt needs repair. Only one review per row.
- [ ] Export actual reviews, re-audit/re-tokenize and freeze exactly one80-row
  artifact for C/D, then obtain GPU and required run checks. No GPU run started.
- [ ] Resolve disputed me-089 reference with versioned provenance; preserve old
  fields/reviews and report sensitivity without089 until any revision is approved.
- [ ] Append hypothesis, interventions, measured outcomes, user feedback,
  failures/fixes and verified recovery evidence to the journal after every round.
- [x] Inspect saved rendered prompts and label masks. Current
  prepare_training.py masks the entire non-thinking generation prefix, including
  its empty think block; supervised_text samples contain answer + native EOS.
  This is not evidence that thinking capability is preserved, nor proof of collapse.
- [x] Use a small identical base/adapter thinking-on/off probe
  set; log raw output, final_answer_emitted, native EOS, truncation, repetitions,
  reasoning/final token counts and actual rendered input. Use enable_thinking,
  not Qwen3 slash commands, for Qwen3.5. Keep this diagnostic separate from the
  established non-thinking development comparison.
  Completed for me-070/me-079: base and A did not emit a final answer on me-079
  thinking-on before their budget/time stops; B emitted final answers and EOS
  for both thinking-on probes. Two prompts do not establish global preservation.
  Same retained training IDs me-041/me-051 generated for both adapters separately.
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
