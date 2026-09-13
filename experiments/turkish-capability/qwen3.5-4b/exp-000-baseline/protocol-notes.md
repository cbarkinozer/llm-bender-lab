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
32,768-token context window suitable for the RTX 4090's 24GB VRAM. Its outputs,
parsing behavior, and one-item throughput must be compared with the recorded
Transformers calibration before it replaces any generated-answer evaluation.

### vLLM environment and known workaround

Remote host: 1x NVIDIA RTX 4090, 24,564 MiB VRAM, driver 595.91.07 (reports
CUDA 13.2 capability). The system-installed CUDA **toolkit** (`nvcc`, used for
JIT-compiling custom kernels at runtime) is a separate, older install:
CUDA 12.4.131 at `/usr/local/cuda-12.4`. `uv pip install vllm --torch-backend=auto
--extra-index-url https://wheels.vllm.ai/nightly` resolved:

- `vllm==0.29.1rc1.dev17+gd2d649e67`
- `torch==2.13.0+cu132` (torch's own bundled CUDA runtime, not the system toolkit)
- `flashinfer==0.6.18.post1`
- `transformers==5.17.0`, `tokenizers==0.23.2`

**Known issue:** flashinfer's top-k/top-p sampler is JIT-compiled at first use
via `nvcc`. Because the system `nvcc` is 12.4 but flashinfer's generated CUDA
source uses a fatbin-compression flag (`--compress-mode=size`) only recognized
by newer `nvcc`, the JIT build fails (`nvcc fatal: Unknown option
'--compress-mode=size'`) and the vLLM engine core process crashes on first
sampling call. This is a toolkit/wheel version mismatch, not a model or config
error.

**Workaround (in effect on all vLLM scripts below):** `export
VLLM_USE_FLASHINFER_SAMPLER=0` before starting the server. This routes sampling
through vLLM's non-JIT `topk_topp_sampler` path instead
(`vllm/v1/sample/ops/topk_topp_sampler.py`), confirmed via the server log line
`FlashInfer top-p/top-k sampling disabled via VLLM_USE_FLASHINFER_SAMPLER=0.`
No crash observed since. The permanent fix would be upgrading the system CUDA
toolkit to 12.6+ (or matching 13.2) so flashinfer's JIT path works normally;
out of scope for this baseline task.

Observed cold start (weight load + `torch.compile` + CUDA graph capture, first
server start with an empty compile cache) took ~220s (10:49:23-10:53:03 UTC on
2026-09-13). A later start with a warm `/root/.cache/vllm/torch_compile_cache`
(AOT-compiled artifacts reused, `torch.compile took 0.71 s` vs. 20.89s cold)
still took ~161s end-to-end (11:06:37-11:09:18 UTC) since weight loading and
CUDA graph capture repeat every process start regardless of the compile cache.
Server scripts poll for up to 300s before giving up.

### vLLM one-item parity check (belebele_tr item 0, gold=A)

Run: `scripts/evaluation/run_vllm_qwen35_parity_check.sh`, same semantic
prompt/dataset revision as the Transformers protocol, `temperature=0`,
`--reasoning-parser qwen3` (splits `reasoning`/`content` server-side, unlike
the Transformers protocol's manual `<think>` tag parsing).

| | Transformers (calibration-1-2048-v1) | vLLM |
|---|---|---|
| Mode | thinking | thinking |
| Prediction | A (correct) | A (correct) |
| Completion tokens | 1,755 | 1,995 (1,887 reasoning) |
| Wall time | 97.9 s | 20.0 s |
| finish_reason / truncation | not truncated | `stop`, not truncated |

vLLM direct mode (max_tokens=512): prediction A (correct), `stop`, 123
completion tokens, 4.3 s.

Both backends agree on the answer; token counts differ slightly (expected —
different attention/sampling kernels can diverge in exact greedy-decoding
token sequences even at temperature 0). vLLM is roughly 5x faster on this one
thinking item, which is why the 100-item paired evaluation
(`belebele-turkish-paired-generation-vllm-v1`) uses it instead of projecting
the ~8.2 GPU-hour Transformers estimate.

### vLLM 100-item paired evaluation (items 0-99, thinking cap 2048)

Run: `scripts/evaluation/run_belebele_generation_vllm.sh`
(`BELEBELE_START_INDEX=0 BELEBELE_LIMIT=100`), started 2026-09-13T11:16:32Z,
result dir `results/belebele-generation-vllm/20260913T111632Z/`. Sequential
requests (concurrency=1), `temperature=0`, direct cap 512 tokens, thinking cap
2048 tokens.

| | Direct | Thinking |
|---|---|---|
| Accuracy | 81% | 64% |
| Parser success | 95% | 66% |
| Truncated (hit token cap) | 2% | 39% |
| Mean generated tokens | 187 | 1,691 |
| Mean latency/item | 1.9 s | 16.9 s |
| Wall time (100 items) | 3.2 min | 28.2 min |

Paired (McNemar): both correct 61, both wrong 16, direct-correct/thinking-wrong
20, direct-wrong/thinking-correct 3. Statistic 11.13 (χ²(1) critical 3.841 at
α=0.05) — **statistically significant**, favoring direct mode.

**Initial read, later revised:** this looked like clear evidence that thinking
mode hurts Turkish reading comprehension. But 39% of thinking items were
truncated at the 2048-token cap before reaching `FINAL: X`, and truncated items
are scored as wrong like any other miss. Mean generated tokens for completed
thinking items (1,691) already sits close to the cap. This is a confound: the
result could reflect "thinking needs more tokens than budgeted for this task"
rather than "thinking reasons worse." See the 200-item follow-up below, which
tests this directly.

### vLLM 200-item paired evaluation (items 100-299, thinking cap 4096)

Run: same script, `BELEBELE_START_INDEX=100 BELEBELE_LIMIT=200
BELEBELE_MAX_NEW_TOKENS_THINKING=4096`, started 2026-09-13T12:13:37Z, finished
2026-09-13T13:36:59Z (~83 min wall), result dir
`results/belebele-generation-vllm/20260913T121337Z/`. Deliberately
non-overlapping item range from the 100-item run above (indices 100-299, not
0-199) so this is a fresh sample, not a superset with double-counted items.
Direct cap left at 512 (only 2% truncated previously, no need to raise).

| | Direct | Thinking |
|---|---|---|
| Accuracy | 83% | 84% |
| Parser success | 93% | 85.5% |
| Truncated (hit token cap) | 5% | 15.5% |
| Mean generated tokens | 177 | 2,217 |
| Mean latency/item | 1.8 s | 22.2 s |
| Wall time (200 items) | 6.1 min | 73.9 min |

Paired (McNemar): both correct 155, both wrong 21, direct-correct/thinking-wrong
11, direct-wrong/thinking-correct 13. Statistic 0.042 (χ²(1) critical 3.841) —
**not statistically significant.** Direct and thinking are statistically tied.

**Conclusion:** doubling the thinking-mode token budget (2048→4096) cut
truncation from 39% to 15.5% and flipped the apparent effect — thinking mode
went from "significantly worse" to "indistinguishable from direct." This
confirms the 100-item result was substantially a token-budget artifact, not
evidence that reasoning degrades Turkish reading-comprehension accuracy.
**Do not report "thinking mode is worse at Turkish" from the n=100 run** — that
conclusion does not survive the n=200/4096-cap follow-up.

**Still open:** 15.5% of thinking items are still truncated at 4096 tokens, so
this comparison remains mildly conservative against thinking mode. A further
run with a higher cap (6144-8192) restricted to the still-truncated item
indices would close this gap. Different item ranges (0-99 vs. 100-299) are
also a partial confound alongside the cap change — a same-range, same-cap
rerun would isolate the cap effect more cleanly if this needs to be publication
-grade rather than a development-time observation.

### Concurrent batching is NOT safe at this concurrency on this build — do not use without re-validating

To speed up a planned 500-item follow-up (items 300-799, same 4096 thinking
cap), `evaluate_belebele_generation_vllm.py` gained a `--concurrency` option
(`ThreadPoolExecutor` over the OpenAI client) and
`run_belebele_generation_vllm.sh` a matching `BELEBELE_CONCURRENCY_DIRECT` /
`BELEBELE_CONCURRENCY_THINKING`. A new `validate_vllm_concurrency.py` spot-
checks concurrency=1 vs. the target concurrency on a handful of items from the
same run before the full batch is trusted, per the handoff's original caution
("measure 1-request parity first, then concurrent batching reproducibility
before launching N questions").

**First validation attempt** (concurrency=16, direct mode, 4 items, exact-text
match required): failed — 2/4 items differed in raw generated text (different
token counts, diverging mid-generation), though the two observed cases still
agreed on the extracted `FINAL: X` answer. Exact-text equality was judged too
strict a bar: this project's own sequential vLLM run already disagrees with
the Transformers backend at the token level while agreeing on the answer, so
demanding byte-identical output between concurrency levels was inconsistent
with how the rest of this protocol already tolerates backend-level decoding
differences. Result:
`results/belebele-generation-vllm/20260913T143757Z/concurrency-validation-direct.json`.

**Validator loosened** to fail only on a *prediction*-level mismatch
(different extracted answer or different correctness), reporting raw-text
divergence as informational context instead of a hard failure, and the sample
size raised from 4 to 20 items for more statistical confidence.

**Second validation attempt** (concurrency=16, direct mode, 20 items):
**failed for real** — 2/20 items (10%) had a different extracted answer *and*
different correctness between concurrency=1 and concurrency=16 (indices 314
and 317; one flipped wrong→right, one flipped right→null/wrong). Text
divergence rate was 65% (13/20), confirming batched decoding meaningfully
perturbs generation on this vLLM build (`0.29.1rc1.dev17`) at this
concurrency, likely compounded by the non-JIT sampler fallback
(`VLLM_USE_FLASHINFER_SAMPLER=0`, see above) — not investigated further. A
10% answer-flip rate is not noise that can be waved away: it is comparable to
or larger than the ~1pp direct-vs-thinking gap this whole exercise is trying
to resolve. Result:
`results/belebele-generation-vllm/20260913T144342Z/concurrency-validation-direct.json`.

**Decision: fell back to sequential (`--concurrency 1`) for the 500-item
run.** GPU-hour cost on this host is cheap (~$0.74/hr); the risk of
contaminating the actual measurement with concurrency-dependent answer flips
was judged not worth the wall-clock savings. If concurrent batching is
revisited later (e.g. to speed up a much larger run), re-run
`validate_vllm_concurrency.py` at the intended concurrency first — do not
assume a validated concurrency level from one vLLM version carries over to
another, and consider testing whether the divergence rate drops with a
non-JIT-sampler-free build or a different `--max-num-seqs`/batching
configuration before trusting it.

### vLLM 500-item paired evaluation (items 300-799, thinking cap 4096, sequential)

Run: same script, `BELEBELE_START_INDEX=300 BELEBELE_LIMIT=500
BELEBELE_MAX_NEW_TOKENS_THINKING=4096 BELEBELE_CONCURRENCY_DIRECT=1
BELEBELE_CONCURRENCY_THINKING=1`, started 2026-09-13T14:47:15Z, finished
2026-09-13T18:10:31Z (~3.4h wall, almost entirely thinking mode). Fresh item
range, non-overlapping with both prior runs (0-99, 100-299).

| | Direct | Thinking |
|---|---|---|
| Accuracy | 81.2% | 78.2% |
| Parser success | 92.2% | 82.0% |
| Truncated | 6.2% | 21.0% |
| Mean generated tokens | 183 | 2,269 |
| Mean latency/item | 1.9 s | 22.7 s |

Paired (McNemar): both correct 360, both wrong 63, direct-correct/thinking-
wrong 46, direct-wrong/thinking-correct 31. Statistic 2.545 (χ²(1) critical
3.841) — not significant, but closer to the boundary than the n=200 run, and
nominally favoring direct again. Truncation rose to 21% at the same 4096 cap
that produced 15.5% on items 100-299 — most likely natural passage-length/
complexity variance across this different item range rather than a real
regression, but it means the token-budget confound from the n=100 result
hasn't fully disappeared even at 4096.

### Combined conclusion across both cap=4096 runs (n=700, items 100-299 + 300-799)

Pooling the two independent, non-overlapping samples that share the same
protocol and token cap (excluding the n=100/cap=2048 run, which used a
different, since-corrected cap):

- Direct: 572/700 correct = **81.7%**
- Thinking: 559/700 correct = **79.9%**
- Contingency: both correct 515, both wrong 84, direct-only-correct 57,
  thinking-only-correct 44
- **Pooled McNemar = 1.43** (χ²(1) critical 3.841) — **not significant**
- Pooled truncation: direct 5.9%, thinking 19.4%; pooled parser success:
  direct 92.4%, thinking 83.0%

**This is the answer to the original question.** Across 700 items at a
4096-token cap, direct and thinking mode are statistically indistinguishable
on Turkish reading comprehension (Belebele). There is a small, consistent,
non-significant edge toward direct (visible in 2 of 3 independent samples: a
large gap at n=100/cap=2048 that was mostly a truncation artifact, near-parity
at n=200, and a 3pp direct edge at n=500) but it never clears the
significance bar, and thinking mode's truncation rate (~19% pooled) means
this remains mildly conservative against thinking rather than a clean,
unconfounded comparison. A materially higher cap (8192+) restricted to
currently-truncated items would be the next step if a fully clean comparison
is ever needed; for the purposes of this baseline, the conclusion is: **do
not claim thinking mode helps or hurts Turkish reading-comprehension accuracy
based on this evidence** — it does neither, measurably, at this token budget.

## The CETVEL likelihood baseline (29.67%) is a scoring artifact, not a capability measurement

Investigated why the CETVEL `belebele_tr` likelihood score (300 items,
2026-09-13T10-11-50) sits barely above random chance (25% for 4-way MC).
Checked which of the four options (A/B/C/D) had the highest raw
log-likelihood on every item, independent of gold answer:

- **Option C wins on 290/300 items (96.7%)**, with a nearly constant
  ~3-5 nat gap over A/B/D (mean logprob: A=-21.17, B=-22.82, **C=-18.16**,
  D=-21.44; stdev ~1.1-1.4 for all four, so this is not a few outliers
  driving the mean — it is close to a fixed per-position offset applied
  almost everywhere).
- Gold answers are close to evenly split (A=79, B=79, C=79, D=63). A
  degenerate "always answer C" strategy alone would score 79/300 = 26.3% —
  the observed 29.67% is barely above that floor.
- **Control:** the vLLM generation protocol's prediction distribution on
  the same underlying dataset (500 items, direct mode) is close to
  balanced (A=102, B=136, C=127, D=96) and tracks the gold distribution,
  with no collapse onto any single letter. This rules out "the dataset
  itself is biased toward C" and confirms the collapse is specific to
  raw-logprob multiple-choice scoring on this chat-tuned model, not a
  property of the content or the model's real capability.

This matches a documented, known failure mode of raw-logprob MCQA scoring
on instruction/chat-tuned models: the model's baseline completion
probability for a bare option-letter token can carry a large positional/
calibration bias that has nothing to do with the actual question, because
chat-tuned models are not trained to produce well-calibrated raw
continuation likelihoods for a single letter after a template like this.
`acc_norm` (length-normalized) does not help here, since all four
continuations are the same short letter string, so length normalization
has nothing to correct.

**Consequence:** the CETVEL likelihood-scored `belebele_tr` result cannot
be used as evidence about the model's Turkish reading comprehension. It
is measuring the harness/scoring-method's calibration bias, and this
bias plausibly extends to every other log-likelihood/MC-scored CETVEL
task using the same request pattern (`exams_tr`, `xcopa_tr`, `nli_tr`,
`news_cat`, `ironytr`, `offenseval_tr`, `sts_tr`, `trclaim19`,
`turkish_plu`, `xfact_tr`) — it was not caused by anything specific to
Belebele's content, so there is no reason to expect it is confined to
this one task. CETVEL's *generation*-scored tasks (`gecturk_generation`,
`mkqa_tr`, `mlsum_tr`, `tr-wikihow-summ`, `wiki_lingua_tr`,
`wmt-tr-en-prompt`, `xlsum_tr`) do not pick among lettered options and
are not expected to share this specific artifact, though they have their
own open concerns (chat-template/thinking-mode handling, already flagged
above).

**Before running full CETVEL:** spot-check 2-3 more of the MC/log-likelihood
tasks the same way (does one option dominate the argmax regardless of
content?) rather than assuming the bias is Belebele-specific. If it
reproduces, the MC-task half of CETVEL needs either a debiasing/calibration
step (e.g. contrastive/channel-normalized scoring) or a generation-based
rescoring (model actually writes an answer, parsed like the Belebele
protocol above) before its number means anything — running the full suite
as currently configured would very likely just reproduce this same
artifact across roughly half the task list at GPU-hour cost, without
producing a trustworthy score.

## MC position-bias spot-check: the bias is task-format-specific, not universal

Ran `scripts/evaluation/run_cetvel_mc_bias_spotcheck.sh` (100 items each,
`xcopa_tr`, `nli_tr` [expands to `mnli_tr`/`snli_tr`/`xnli_tr`],
`turkish_plu` [expands to 4 subtasks]) to check whether the `belebele_tr`
position-bias artifact generalizes across CETVEL's other log-likelihood/MC
tasks. Result:
`results/mc-bias-spotcheck/20260913T201657Z/bias-report.txt`.

| Task | Choices | Accuracy | Predicted distribution | Bias flag |
|---|---|---|---|---|
| `mnli_tr` | 3 | 35% | A:100 | **Yes — 100% collapse to A** |
| `snli_tr` | 3 | 35% | A:100 | **Yes — 100% collapse to A** |
| `xnli_tr` | 3 | 44% | A:69, C:31 | **Yes — 69% collapse to A** |
| `turkish_plu_goal_inference` | 4 | 30% | A:32, B:25, C:18, D:25 | No — balanced |
| `turkish_plu_next_event_prediction` | 4 | 40% | A:26, B:21, C:27, D:26 | No — balanced |
| `turkish_plu_step_inference` | 4 | 25% | A:30, B:19, C:27, D:24 | No — balanced |
| `turkish_plu_step_ordering` | 2 | 79% | A:49, B:51 | No — balanced |
| `xcopa_tr` | 2 | 61% | A:52, B:48 | No — balanced |

**The bias is not a universal property of raw-logprob MC scoring on this
model** — it is specific to certain task/prompt formats. All three NLI-style
tasks (`nli_tr`'s three subtasks, sharing the same "TUTARLI/ALAKASIZ/
ÇELİŞKİLİ" 3-way entailment template) collapse hard onto option A, the same
way `belebele_tr` collapsed onto C. `turkish_plu` (4 different subtask
formats) and `xcopa_tr` (2-choice commonsense) show no collapse at all —
their prediction distributions track their gold distributions closely, and
their accuracy numbers (25-79%, with real per-item variation) look like
genuine signal, not an artifact floor.

**Practical consequence for a future full-CETVEL run:** don't blanket-discard
every MC-scored task. Treat `belebele_tr` and all of `nli_tr`'s subtasks
(`mnli_tr`/`snli_tr`/`xnli_tr`) as compromised by this scoring artifact
unless rescored via a generation-based protocol. Treat `turkish_plu` and
`xcopa_tr` as trustworthy as-is. The remaining untested MC tasks (`exams_tr`,
`news_cat`, `ironytr`, `offenseval_tr`, `sts_tr`, `trclaim19`, `xfact_tr`)
have not been spot-checked and should not be assumed either way before a
full run.

### Two more harness/CETVEL task-name collisions found and fixed en route

Getting this spot-check to actually run surfaced two bugs unrelated to the
position-bias question itself, both from the same root cause: CETVEL's
pinned revision predates a `huggingface_hub` version that rejects bare
(non-namespaced) dataset repo ids, and `lm-evaluation-harness` ships its own
built-in tasks that collide by name with CETVEL's custom ones of the same
name — the built-in one (with the stale bare path) is what actually
resolves:

- `xnli`/`xnli_tr` (harness's built-in `xnli` group vs. CETVEL's `nli_tr`
  group's `xnli_tr` subtask) — fixed in
  `patches/cetvel-harness-canonical-dataset-ids.patch`.
- `xcopa`/`xcopa_tr` (harness's built-in `xcopa` group vs. CETVEL's own
  `xcopa` group) — same patch, same fix (`xcopa` → `cambridgeltl/xcopa`).

Also found and fixed a set of bare dataset ids purely within CETVEL's own
task configs (not harness collisions): `exams`, `nli_tr` (mnli/snli
subtasks), `mlsum`, `offenseval2020_tr`, `wmt16` (4 files), `xcopa` (CETVEL's
own copy) — see `patches/cetvel-canonical-dataset-ids.patch`. Checked
`mnli_tr`/`snli_tr`/`turkish_plu` for the same harness-collision pattern
after finding the first two — none found (harness's built-in MNLI task is
named `mnli`/`mnli_mismatch`, not `mnli_tr`; `turkish_plu` has no built-in
harness equivalent at all). Full details of everything hit standing up this
environment: `docs/environment-setup-gotchas.md`.
