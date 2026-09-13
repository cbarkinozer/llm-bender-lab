# CETVEL protocol notes

These notes describe the task selection for the untouched Qwen3.5-4B baseline.
They are tied to CETVEL revision
`6119c517e06cce23aaeac103ce3504c9380655e3` and its lm-evaluation-harness
submodule revision `6e49b1f6910931882a4b3b105794c6faf96b74e5`.

## Official selector reconciliation

CETVEL's model-specific `examples/lm_eval_*_all.sh` files list 20 selectors.
One of them, `turkish_plu_prompt`, is not registered by the pinned checkout.
The repository README, `examples/run_nlu_tasks.sh`, and
`tasks/turkish_plu/turkish_plu_common_yaml` instead define the group as
`turkish_plu`. The frozen candidate protocol therefore uses `turkish_plu`,
which expands to four multiple-choice tasks:

- `turkish_plu_goal_inference`
- `turkish_plu_next_event_prediction`
- `turkish_plu_step_inference`
- `turkish_plu_step_ordering`

The pinned checkout also contains `bilmecebench`, `circumflex_tr`,
`turkce_atasozleri`, and `turkishmmlu` definitions that are absent from the
official all-task examples and the README task table. They are excluded from
this CETVEL baseline so repository additions do not silently redefine the
published comparison suite. They may be added later as a separately named
supplemental evaluation.

## Request types

The selected multiple-choice/log-likelihood tasks are `belebele_tr`,
`exams_tr`, `ironytr`, `news_cat`, the three-task `nli_tr` group,
`offenseval_tr`, `sts_tr`, the two-task `trclaim19` group, the four-task
`turkish_plu` group, `xcopa_tr`, and `xfact_tr`.

The selected generation tasks are `gecturk_generation`, `mkqa_tr`, `mlsum_tr`,
`tr-wikihow-summ`, `wiki_lingua_tr`, `wmt-tr-en-prompt`, and `xlsum_tr`. Their
task-owned stop conditions, filters, and metrics remain unchanged.

`tquad` and `xquad_tr` are legacy Python tasks with mixed requests: each item
issues both `generate_until` for the answer and `loglikelihood` for the
unanswerable alternative, then applies SQuAD-style custom aggregation. They
must receive a separate smoke test because a plain generation smoke does not
exercise their full path.

## Chat-template decision

The native Qwen3.5 chat template is applied once by the harness. The tracked
compatibility patch supplies `enable_thinking=False`. Qwen's non-thinking
serialization includes an empty `<think>...</think>` block; this is expected
template syntax, not generated reasoning. Without the patch, generation tasks
that stop at the first newline can score a reasoning preamble instead of the
answer.

## CETVEL-Lite development gate

Fast iteration uses `--limit 4` over every selected official task/group,
yielding approximately 100 examples after group expansion. The pinned harness
selects the same leading four documents on every run, so comparisons remain
paired and deterministic. This subset is a development signal, not a replacement
for the full benchmark: only promising checkpoints and final candidates receive
the complete CETVEL evaluation.

## Fast development benchmark

The fastest training-loop gate is the first 300 documents of CETVEL's pinned
`belebele_tr` task. This is a deterministic Turkish reading-comprehension
measurement using multiple-choice log-likelihood, so it avoids the long output
generation that dominates CETVEL runtime. Per-item document and prompt hashes
from the untouched-model run define the immutable comparison set. It does not
measure grammar correction, summarization, translation, or free-form question
answering and therefore cannot replace CETVEL-Lite or full CETVEL.

## Paired direct-versus-thinking generation protocol

Thinking cannot be evaluated by the likelihood protocol above because it never
generates a reasoning trace. The separately named
`belebele-turkish-paired-generation-v1` protocol uses the same first 300
documents but generates one answer per item. Direct and thinking runs differ
only in the native chat template's `enable_thinking` value.

Decoding is greedy (`do_sample=false`, reported as `temperature=0`) with batch
size 1 and seed 3407. The answer contract is `FINAL: X`, where X is A-D. Raw
reasoning, final text, parser status, token counts, truncation, latency, GPU
telemetry, software and hardware snapshots, immutable revisions, commands,
per-item inputs, and artifact hashes are retained. A heuristic language label
is exploratory metadata only; conclusions about reasoning language require
manual inspection. This score is compared only with its paired generated-answer
condition, not directly with CETVEL's likelihood score.

### Calibration observations

The first direct calibration used 10 items and a 128-token ceiling. Six items
hit the ceiling and only six answers parsed, so that ceiling is invalid and the
run is retained as a failed protocol calibration. The first native-thinking
calibration was stopped after three 512-token-truncated items. Manual inspection
showed predominantly English reasoning over the Turkish inputs. A one-item
2,048-token calibration then completed correctly after 1,755 generated tokens
and 97.9 seconds without truncation. At that unoptimized rate, 300 thinking
items project to about 8.2 GPU-hours. The final ceiling and inference backend
remain unfrozen pending an optimized-backend parity and throughput check.

### Engine-backed inference investigation

The initial generated-answer calibrations used plain Transformers and emitted
warnings that Qwen3.5's `causal_conv1d` and Flash Linear Attention kernels were
absent. Official Qwen guidance recommends current vLLM or SGLang for Qwen3.5.
An isolated vLLM environment is therefore evaluated separately with a reduced
8,192-token context window suitable for the RTX 4090's 24GB VRAM. Its outputs,
parsing behavior, and one-item throughput must be compared with the recorded
Transformers calibration before it replaces any generated-answer evaluation.
