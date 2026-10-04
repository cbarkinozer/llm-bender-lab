# exp-002-cetvel-tiny: pinned base versus final exp016/F

## Status and question

Completed2026-10-04:100 base +100 final F outputs, task-native scoring,
prompt/config parity verification and62-file verified local recovery.
GPU recovery complete. Blind human20 review completed and exported20/20.
See `REPORT.md` for results and interpretation; `results-v1/` retains evidence.
Source-bearing questions/raw generations remain local and Git-ignored pending
source-specific redistribution review; no files deleted. Full review receipts/notes
remain local; public labels omit private review metadata. Builders/source pins,
metrics, hashes, per-item labels and human grade summaries are versioned.
Regenerate questions with prepare.py before clone-side CPU tests. Full raw evidence
remains in the verified local recovery, not the proposed SFT Dataset Hub package.
Does the F behavioral adapter retain or improve performance on external Turkish
generation tasks relative to its actual pinned starting model? Evaluation only,
no training, no W&B upload. This is not an official full CETVEL score or proof of
general Turkish improvement.

## Existing mini and selection

Found the historical CETVEL-mini at exp000 results/cetvel-generation-suite/
20260914T065945Z:700 items, not500. Old cohort used task-specific first-row ranges,
not a representative random sample from all CETVEL splits. New100 pilot uses20
seeded-random inputs each from GECTurk, TQUAD, XQuAD-TR, EN-to-TR WMT and MLSum-TR.
It preserves original documents, targets and prompts. It contains no MCQ, NLI,
classification or MMLU tasks. QA is represented by two separate leaf tasks.

`data-v1/manifest.json` freezes original dataset revisions, pool/file hashes,
selected inputs and deterministic selection seed. Selection never uses old
answers or scores. Historical baseline outputs have already been inspected;
this is an external-task diagnostic pilot, NOT a pristine unseen final holdout.
No blanket data redistribution license is asserted; retained excerpts are local
evaluation artifacts, not a new dataset publishing release.

`data-v1/leakage-audit.json` screens all100 against F104 training prompts:
zero exact or near-string candidates (character similarity >=.75 or five-word
shingle containment >=.5). Checks preserve Turkish characters/case. These are
screening results, not proof of semantic independence or pretraining provenance.
Never train on these rows, their targets or paraphrases. If later training choices
use the results, keep this100 explicitly as development data. A300/500 confirmation
must use additional, not previously inspected rows/source groups from full splits;
do not market a pilot-inclusive500 aggregate as an independent confirmation.

## Comparable generation

Current run uses the user-approved fast-backend option: vLLM0.30.0, Torch2.13.0
cu130, Transformers5.18.0 on RTX4090/driver595.71.05 (CUDA maximum13.2).
Both arms share one BF16 engine, active request cap8, context8192, eager execution,
prefix cache disabled, text-only loading; same data/prompt and4096 output cap.
Maximum input1487 leaves sufficient room at8192; no input truncated. This overrides
the original HF batch1/32768 plan below for BOTH arms, not just one. Runtime
manifests retain exact engine/config/package settings; no exact HF equivalence
claim. Saved HF runner remains a fallback, never mix its outputs with vLLM arms.

Termination compatibility: model config EOS248044 (endoftext) differs from
tokenizer EOS248046 (im_end). Earlier HF comparison stopped at248044 and included
im_end inside outputs. vLLM must therefore disable its implicit renderer EOS
(`ignore_eos=True`) and explicitly stop only on model EOS248044; record stop_reason
to verify it. The first probe caught an incorrect assumption that tokenizer EOS
equals model EOS before any generation; corrected using model config, not by
quietly shortening answers. Preserve failed and corrected probe logs.

Upstream verification also established both safetensors shard SHA256 values are
identical between our pinned Qwen and Unsloth repos; repo names/revision strings
alone do NOT imply different learned weights. Config/tokenizer/template files do
differ. Rerun base because generation caps/stops and execution protocol changed,
not because Unsloth necessarily re-trained it. Match F's original repository
serialization for this pair.

Both arms fresh-load unsloth/Qwen3.5-4B at revision
3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636. F is the locally recovered final40-step
exp016 adapter; verify weight and config SHA before loading. Do not initialize
base from F or compare against old Qwen/Qwen3.5-4B baseline scores.

Original HF fallback plan (NOT the executed backend): BF16, batch1,
same tokenizer/template, no system prompt, thinking off,
greedy, repetition penalty1.05,4096 output-token budget,32768 context, seed3407.
No prompt truncation permitted. Record raw rendered prompts/input and output token
IDs, EOS, hashes, packages and runtime. Compare arm parity before scoring.
Native EOS is success;180-second wall-time/exact-loop/length guards are explicitly
marked incomplete. No silent decoder changes or W&B run creation.

Unlike historical CETVEL task defaults, we do NOT stop at the first newline or
use small128/256/768 generation caps. This is a documented adapted generation
protocol to inspect real full responses; it is not an official CETVEL ranking.
Extra prose can depress exact/overlap scores without proving content failure.

## Scoring and human check

Reuse scripts/evaluation/score_cetvel_generation.py: GEC exact match plus diagnostic
flags; QA EM/F1; translation BLEU/chrF; summaries ROUGE. Keep per-task results and
per-item scores, termination and output-length statistics. Do not average these
different scales into one accuracy or infer faithfulness from lexical overlap.

Frozen human-review20 subset:4 per task, selected before base/F outputs. Later
create a blind, per-item shuffled base/F queue with pass/partial/fail and preference
plus optional notes. Review grammar, meaning preservation, correctness and brevity;
valid non-reference wording may pass. Audit suspicious automatic misses and
incomplete outputs separately as diagnostics, not part of the random human20.
No external LLM judge configured or called. If added later, pin model/rubric and
store judgments, order swaps and human agreement before trusting it.

Proceed to a larger independent sample when signals are promising and there is
no concerning quality/meaning regression. Tiny mixed results are inconclusive,
not an automatic instruction to tune until100/100. Substantive losses guide
new training scenarios, never reuse benchmark rows. Small per-task20 counts cannot
establish stable general accuracy or statistical superiority.

## Original HF fallback commands (not executed)

Use the existing known-working E/F GPU stack; no extra fine-tune, smoke or tiny
overfit requested. Transfer this repo/code and the verified final F adapter.
Do not upload .env for this evaluation; W&B credentials are not needed.

```bash
python experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/evaluate.py \
  --arm base --output-dir /workspace/cetvel-tiny-runs/base
python experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/evaluate.py \
  --arm F --adapter /workspace/F-adapter --output-dir /workspace/cetvel-tiny-runs/F
python experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/score_pair.py \
  --results-root /workspace/cetvel-tiny-runs
```

CPU scorer needs sacrebleu and rouge-score, matching the existing CETVEL scorer.
Save dependency versions, stdout/stderr, source/config/data snapshot, both
manifest/answers/template bundles and scored outputs before pod disposal. Final F
weights already recovered locally; no optimizer or training checkpoint needed.
Actual benchmark plus scoring took290.56seconds; setup/diagnostics are separate.
Local backup verified before announcing readiness to close GPU.

Local adapter: C:/Users/cbark/Documents/llm-bender-artifacts/exp-015-016-paired/
essential-extracted/exp015-exp016-runs/F/sft-v1/adapter (outside Git).

CPU preparation and tests:

```powershell
& C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/prepare.py
& C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/test_preparation.py
```

Fast-backend command after the adapter/EOS probe passes:

```bash
export HF_HOME=/workspace/.cache/huggingface
export LD_LIBRARY_PATH=/workspace/.venvs/cetvel-vllm/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}
/workspace/.venvs/cetvel-vllm/bin/python experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/evaluate_vllm.py \
  --adapter /workspace/F-adapter --output-dir /workspace/cetvel-tiny-runs
/workspace/.venvs/cetvel-vllm/bin/python experiments/turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/score_pair.py \
  --results-root /workspace/cetvel-tiny-runs
```
