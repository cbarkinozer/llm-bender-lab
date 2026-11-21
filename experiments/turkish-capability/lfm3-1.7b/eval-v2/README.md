# LFM3 eval v2 (draft, not frozen)

Status 2026-11-21: core families built and CPU-verified; no model has been run on it.
Purpose: decide, with paired statistics, whether a Turkish-adaptation run keeps the abilities that
broke in every earlier SFT (thinking-off arithmetic, tool calling) and whether Turkish improves.
Plan context: [SELF-DISTILL-PLAN-20261121.md](../SELF-DISTILL-PLAN-20261121.md), section 4.

Never train on anything here. The packets are evaluation only (`training_allowed: false`).

## Composition

| Family | Items | Languages | Source | Gold |
|---|---:|---|---|---|
| math (GSM8K word problems) | 152 pairs | EN + TR | `openai/gsm8k` test (MIT) + `malhajar/gsm8k_tr-v0.2` | EN final answer |
| symbolic arithmetic | 60 pairs | EN + TR instruction | seeded generator, exact-fraction check | integer |
| tool calls | 80 pairs (40 simple, 20 multiple, 20 parallel) | EN + TR query, English schemas | BFCL v3 (Apache-2.0) | BFCL possible answers |

Total 584 prompts per (model, thinking mode, seed). `manifest-core.json` lists every pair, source index,
revision, sha256 and audit counts. Packets live in `data-local/` (ignored by Git because the Turkish GSM8K card
declares no license); rebuild with `python scripts/datasets/build_lfm3_eval_v2.py` (byte-identical or it refuses).

Not built yet (still Phase 0): Turkish code family, Turkish checkable-instruction family, TurBLiMP rerun on the
new runner (frozen 1600-pair packet already exists in `exp-000-baseline`), English guard set (IFEval, GPQA
Diamond, HumanEval+, BFCL full subset via lm-eval-harness/evalplus on the pod with the same presets).

## Findings from building it (all verified, 2026-11-21)

- **`malhajar/gsm8k_tr-v0.2` is not clean.** The card says GPT-4 translated and humans verified, but the test split
  has 1317 rows vs 1319 and only 1104 of 1319 English items survive an automatic check (same final answer, every
  question number preserved, no extra numbers); at least five aligned items have a different final answer in Turkish
  (for example 14 vs 16, 81 vs 135, 150 vs 240; only the first ten mismatches were listed). No license is declared. We keep only invariant-clean pairs, so
  the old claim "human-verified" in the plan was too strong. Machine translation is also why this is a math
  benchmark in Turkish, not a Turkish-quality benchmark.
- **The pinned chat template defaults to `enable_thinking=true`.** The generation prompt ends in `<think>` (on)
  or `<think></think>` (off). Any run that omits the flag silently measures thinking on. Both modes are run and
  reported separately; the runner asserts the prompt ending.
- **Tools reach the model through the template** (`tools=` renders JSON lines inside the system prompt). The
  older runner `evaluate_lfm3_vllm_batched.py` does not pass `tools`, so it cannot run this family.
- The upstream model repo has newer commits than our pinned `0dc4268...` (README-only changes). All runs keep the
  pinned revision.
- Tool-call output format is assumed to be the template's own `<tool_call><function=NAME><parameter=K>V</parameter>`
  form (JSON inside `<tool_call>` is also parsed). Unverified for generation: the first GPU smoke must show
  `fmt` is `xml` or `json` for the base model; otherwise add a parser before any comparison.

## Verification already done (CPU)

- `python scripts/evaluation/lfm3_eval_v2_scoring.py --self-test`: extractors, separators (`1.450.000`, `3,5`),
  thinking split, tool-call parser and matcher.
- Builder oracle test: for all 80 tool items a call synthesized from the gold passes and three mutations fail
  (wrong function, renamed parameter, no call); the scorer accepts the gold final answer in both marker styles.
- `python scripts/evaluation/selftest_lfm3_eval_v2.py`: synthetic oracle, degraded and thinking-on runs go through
  scoring, summary and paired comparison with the expected numbers.
- The pinned chat template was rendered locally with tools and both thinking modes (see Findings).

## Protocol (draft; frozen when the first baseline run starts)

- Model: pinned `LiquidAI/LFM3-1.7B` revision from `exp-000-baseline/config-planned.json`; other models by
  merged directory or Hub repo, always with the same tokenizer and chat template.
- Prompts: no system prompt; math asks for `Final answer: <number>` (EN) or `Nihai cevap: <sayı>` (TR); symbolic asks
  for the number only. The scorer reports strict (marker) and lenient (any final number) math accuracy separately.
- Decoding: model-card presets per family (math, symbolic: T=1.0, top_p 0.95, top_k 20; tool calls: T=0.1, top_k 50,
  repetition penalty 1.1); `--preset greedy` is a sensitivity check. bf16, eager, `max_num_seqs` 32, prefix caching
  off, stop on the native `<|im_end|>` id, context 12288, max new tokens 2048 (thinking off) or 8192 (on).
- Seeds: 3407 for screening; 3407, 3408, 3409 for finalists. A run directory holds `run-manifest.json`,
  `answers-seed<N>.jsonl` (raw outputs) and, after scoring, `scores-seed<N>.jsonl` and `summary.json`.
- Statistics: Wilson intervals per cell; paired bootstrap and exact McNemar for model-vs-model; TR minus EN gap with
  a paired bootstrap interval. Reported separately: parse rate, number-only rate, thinking-closure rate, EOS rate,
  max-token hit rate, tool-call error taxonomy.

Smallest effect these sizes can resolve (rough, 95%): math about 5-6 points, tool calls about 8, symbolic about 9.
"Within noise" means the drop is smaller than that, not that it is zero.

## Proposed capability budget (change before the first baseline run, not after)

Compared with the untouched base, same thinking mode and seeds, on the English side:

| Capability | Budget |
|---|---|
| symbolic/en thinking off | point delta no worse than -5 points and McNemar not significant against the candidate |
| math/en, tool calls/en (both thinking modes) | point delta no worse than -5 points |
| thinking-closure rate (thinking on) | no worse than -2 points |
| answer language when Turkish was requested | at least 98% (separate language-ID check) |

Turkish target: math/tr and tool calls/tr improve or the TR-EN gap shrinks; TurBLiMP macro accuracy not below the
previous best (exp014); owner blind review for finalists only. Gate for the Phase 0 baseline: base reproduces
symbolic thinking-off near 8/8 and shows a visible TR-EN gap on math.

## Commands

```text
python scripts/datasets/build_lfm3_eval_v2.py                       # rebuild / verify packets (CPU)
python scripts/evaluation/selftest_lfm3_eval_v2.py                  # CPU pipeline check
python scripts/evaluation/run_lfm3_eval_v2.py --name base-think-off --thinking off \
    --output-dir <runs>/base-think-off --limit-pairs 5              # GPU smoke (5 pairs per family)
python scripts/evaluation/score_lfm3_eval_v2.py score --run-dir <runs>/base-think-off
python scripts/evaluation/score_lfm3_eval_v2.py compare --base <runs>/base-think-off --candidate <runs>/other
```

## Open items

- Owner spot check: 20 random Turkish GSM8K items and the 80 tool queries in `toolcall-translations-tr.json`
  (written by Claude Sonnet 5.5; invariants checked automatically, meaning not).
- Remaining families and the English guard set (see above), then `freeze.json` with all hashes.
- GPU smoke of the runner (not yet executed anywhere).
