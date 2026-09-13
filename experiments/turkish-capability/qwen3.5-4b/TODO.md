# Turkish Capability TODO

The immediate objective is to measure the untouched Qwen3.5-4B model. Dataset
construction and fine-tuning begin only after the baseline protocol is frozen
and its results are saved.

## Phase 1 — Baseline environment

- [x] Select `Qwen/Qwen3.5-4B` as the starting model.
- [x] Pin the model and tokenizer revision.
- [x] Pin the CETVEL repository revision.
- [x] Pin CETVEL's `lm-evaluation-harness` submodule revision.
- [x] Select an RTX 4090 host with enough VRAM for unquantized BF16 inference.
- [x] Create the isolated Python environment on the GPU host.
- [x] Detect and record that the template's PyTorch 2.4.1 is incompatible with
      Transformers 5.17 before downloading model weights.
- [x] Install the pinned PyTorch 2.6.0/CUDA 12.4 compatibility stack.
- [x] Detect inherited system-package/cuDNN loader conflict before model download.
- [x] Install and validate the matching cuDNN wheel inside the active environment.
- [x] Detect the inherited Torch 2.4.1/Torchaudio 2.4.1 binary mismatch before
      model download.
- [x] Install and validate Torchaudio 2.6.0 with the pinned Torch stack.
- [x] Validate the complete Torch/Torchaudio/Torchvision/CUDA import stack.
- [x] Expand persistent `/workspace` storage to at least 40 GB (80 GB
      recommended) before resuming model and dataset downloads.
- [x] Verify PyTorch, CUDA, Transformers v5, and the evaluation harness versions.
- [x] Capture the GPU, CUDA runtime, Python, OS, and package versions in the
      smoke preflight manifest. Capture the host driver version with the full run.
- [x] Ensure model, dataset, package, and Torch caches live under `/workspace`.
- [ ] Preserve the repository Git commit and dirty diff used by the remote run.

## Phase 2 — Freeze the CETVEL protocol

- [x] Inventory every task exposed by the pinned CETVEL revision.
- [x] Reconcile the task list with the repository README and official examples;
      replace their invalid `turkish_plu_prompt` selector with `turkish_plu`.
- [x] Classify each selected task as multiple-choice/log-likelihood or generation.
- [ ] Confirm the native Qwen3.5 chat template is applied exactly once.
- [x] Inspect the rendered prompt for multiple-choice, generation, and the
      legacy mixed generation/log-likelihood request path.
- [x] Determine Qwen3.5's actual default thinking behavior in this backend.
- [x] Choose non-thinking mode because CETVEL generation tasks stop at the
      first newline and otherwise score reasoning preambles instead of answers.
- [ ] Freeze task-specific generation parameters and stop conditions.
- [ ] Freeze batch size, padding behavior, precision, and inference backend.
- [ ] Confirm CETVEL data is evaluation-only and excluded from all training data.
- [ ] Change `turkish-cetvel-v1.yaml` from `draft` to `frozen`.

## Phase 3 — Evaluation smoke tests

- [x] Load the exact model revision in BF16 without quantization.
- [x] Run one `belebele_tr` item to test log-likelihood scoring.
- [x] Save its serialized prompt, raw model values, parsed answer, and score.
- [x] Run one `gecturk_generation` item to test generation and parsing.
- [x] Save its serialized prompt, raw output, parsed answer, and score.
- [x] Check for duplicated chat templates, unexpected reasoning text, repetition,
      truncation, and missing termination.
- [ ] Record peak VRAM, warm-up/compile time, and steady-state runtime.
- [x] Resolve compatibility failures found by the smoke tests. The remaining
      slow-kernel warnings affect runtime, not correctness.

## Phase 4 — Full untouched-model baseline

- [ ] Full candidate run started at `2026-09-13T09:32:21Z` on the RTX 4090;
      monitor to completion before checking the items below.
- [ ] Run every frozen CETVEL task with per-item outputs enabled.
- [ ] Preserve the exact CLI invocation and resolved effective configuration.
- [ ] Preserve raw outputs, parsed answers, errors, and aggregate metrics.
- [ ] Record task-level and category-level scores without inventing a single
      aggregate if CETVEL does not define one.
- [ ] Record item counts, failures, parser success, output lengths, and runtime.
- [ ] Inspect a representative sample of Turkish outputs manually.
- [ ] Investigate suspiciously high/low scores and task failures.
- [ ] Hash the final baseline output bundle.
- [ ] Update `exp-000-baseline` results and conclusion.
- [ ] Mark `exp-000-baseline` as `completed` only after analysis is finished.

## Phase 4a — CETVEL-Lite iteration gate

- [x] Define a stable development subset as four items per expanded official
      leaf task (approximately 100 items in total).
- [ ] Run and preserve the untouched-model CETVEL-Lite baseline.
- [ ] Use exactly the same item IDs and protocol for every training iteration.
- [ ] Reserve full CETVEL for promising checkpoints and the final comparison.

## Phase 4b — Fast Turkish development benchmark

- [x] Select 300 fixed `belebele_tr` items as the fast reading-comprehension
      development signal.
- [x] Run and preserve the untouched-model 300-item likelihood baseline:
      29.67% accuracy over 300 items, 111 seconds wall time, 9,288 MiB peak VRAM.
- [x] Freeze the resulting document and prompt hashes for paired comparisons.
- [ ] Use this benchmark for rapid iteration without treating it as a complete
      Turkish-capability score.
- [x] Define a paired generated-answer protocol that can genuinely execute both
      direct and thinking modes over the same 300 Belebele documents.
- [x] Run initial direct and thinking calibrations with greedy decoding; retain
      the invalid 128/512-token truncated runs as protocol-development evidence.
- [x] Confirm native thinking can terminate: the first 2,048-token calibration
      completed at 1,755 tokens in 97.9 seconds.
- [ ] Test an optimized Qwen3.5 inference path and check output/score parity
      before committing roughly 8 GPU-hours to the 300-item thinking run.
- [ ] Freeze `max_new_tokens` after checking truncation and answer parsing.
- [ ] Run all 300 paired items and preserve reasoning, answers, token counts,
      latency, resource telemetry, environment snapshots, and hashes.
- [ ] Compare paired correctness with McNemar statistics and inspect reasoning
      language manually before making any English-reasoning claim.

## Phase 5 — Regression baseline

- [ ] Select an instruction-following benchmark and pin its revision.
- [ ] Select a general-reasoning benchmark and pin its revision.
- [ ] Define how invalid or non-terminating output rate is measured.
- [ ] Confirm the existing 2-point and 5-point regression budgets use scales
      compatible with the selected benchmarks.
- [ ] Run and preserve the untouched model's regression results.

## Phase 6 — Turkish training dataset

- [ ] Define the Turkish sub-capabilities the first dataset should teach.
- [ ] Decide whether reasoning traces must be preserved and freeze the target
      reasoning/direct-answer mixture.
- [ ] Select legally usable, independently sourced data.
- [ ] Record source provenance and immutable revisions.
- [ ] Normalize the conversation schema and native chat-template formatting.
- [ ] Filter malformed, mixed-language, unsafe, and low-quality examples.
- [ ] Deduplicate exact and near-duplicate examples.
- [ ] Check exact, near, source-level, translated, and synthetic overlap with
      every CETVEL evaluation item.
- [ ] Create deterministic train/validation splits with independent seeds.
- [ ] Analyze token lengths and choose the truncation/packing policy.
- [ ] Publish or hash an immutable dataset artifact.

## Phase 7 — First fine-tuning experiment

- [ ] Create `exp-001-lora` with `exp-000-baseline` as its parent.
- [ ] Use Unsloth text-only SFT with BF16 LoRA, not 4-bit QLoRA.
- [ ] Freeze vision layers and enable language attention/MLP adapters.
- [ ] Start with rank 16, alpha 16, 2,048-token context, and batch size 1.
- [ ] Record exact Unsloth, Unsloth Zoo, Transformers, TRL, PEFT, and Torch
      revisions after compatibility validation.
- [ ] Run dataset-format and label/masking validation.
- [ ] Run a forward/backward smoke test.
- [ ] Run a tiny-overfit test and confirm expected loss behavior.
- [ ] Estimate peak VRAM and steady-state step time.
- [ ] Start the full run only after all pre-run gates pass.

## Phase 8 — Post-training comparison

- [ ] Select checkpoints using target metrics rather than validation loss alone.
- [ ] Evaluate the adapter under the frozen CETVEL protocol.
- [ ] Evaluate the same regression suite used for the untouched model.
- [ ] Compare paired per-item outputs and report uncertainty where appropriate.
- [ ] Separate semantic gains from formatting/parser gains.
- [ ] Evaluate the merged/deployment artifact if it differs from adapter mode.
- [ ] Decide whether the hypothesis held and whether regressions fit the budget.
- [ ] Record the next single-variable experiment.
