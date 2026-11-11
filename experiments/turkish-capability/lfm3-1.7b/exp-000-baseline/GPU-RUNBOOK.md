> Current status (2026-11-11): baseline complete and123-file recovery verified; no CPT has run. Training is deferred by the owner. Follow NEXT-SESSION.md and TODO-20261112.md. W&B is training-only; older preparation/off/evaluation-upload notes below are historical. The executed baseline uses pinned vLLM nightly, not the initial Transformers candidate.

# LFM3 Turkish: baseline then CPT

Prepared on CPU; no actual model benchmark or 1.7B training run yet. Use one
RTX4090 24GB, Python3.12 and a persistent `/workspace` volume. Recommended free
disk: 40GB, including package installation/cache headroom. No local Docker.
Runtime pins are candidates until the Linux CUDA smoke passes. Read the repo's
environment setup gotchas before setup. Do not reuse expired pod endpoints.

## Transfer and setup

Transfer the private, hash-verified source/data bundle; verify its archive SHA256
against the adjacent receipt before extracting under `/workspace/llm-bender-lab`.
It contains copyrighted evaluation/source text for local use, not public release.
No credentials or base weights are included. HF weights are downloaded on the pod
from the pinned model revision. Keep secrets outside the repository/artifact tree.

From the repository root:

```bash
bash experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/setup_gpu.sh
export HF_HOME=/workspace/.cache/huggingface
PY=/workspace/.venvs/lfm3/bin/python
EXP=experiments/turkish-capability/lfm3-1.7b/exp-000-baseline
bash "$EXP/run_baseline.sh"
```

Setup fails on dependency conflicts or missing CUDA/BF16. Preserve logs rather
than silently changing versions. The smoke selects five rows, one/task, for
execution checks only; it is not a model-quality estimate or prompt-tuning set.
Inspect input serialization, output fields, EOS/length/loop/timeout stops and peak
memory. Estimate remaining wall time from observed output lengths and throughput;
no 15â€“20 minute promise is made before this measurement. The model card warns
thinking-off can be inconsistent: record unexpected reasoning text, do not
silently strip it or discard the affected outputs. Native EOS is124900.

## Full unchanged-model baseline

Use a new output folder for every invocation; never overwrite or silently retry.

```bash
RUN="$EXP/results-local/base-v01"
mkdir -p "$RUN"
"$PY" scripts/evaluation/evaluate_lfm3_cetvel.py --experiment-dir "$EXP" --output-dir "$RUN/cetvel" --allow-reviewed-remote-code 2>&1 | tee "$RUN/cetvel.log"
"$PY" scripts/evaluation/score_lfm3_cetvel.py --results-dir "$RUN/cetvel" 2>&1 | tee "$RUN/scoring.log"
"$PY" scripts/evaluation/evaluate_lfm3_text.py --experiment-dir "$EXP" --output-dir "$RUN/text" 2>&1 | tee "$RUN/text.log"
"$PY" scripts/evaluation/evaluate_lfm3_turblimp.py --experiment-dir "$EXP" --output-dir "$RUN/turblimp" 2>&1 | tee "$RUN/turblimp.log"
```

Use `set -euo pipefail` in the coordinating shell so tee cannot hide failures.
Retain incomplete CETVEL outputs in scoring; no manual exclusion. Primary CPT
diagnostics are within-model Wikipedia/Web NLL and TurBLiMP; five task metrics
describe usefulness/retention. No pooled score. NLL tokenization/context policy is
fixed before/after; do not compare tokenizer-dependent perplexity across Qwen
and LFM3. Historical Qwen uses a different backend; its throughput is not a
controlled hardware/backend comparison. Source cohort was previously inspected;
call it a comparison cohort, not an untouched final test.

## CPT diagnostics and training

The recipe follows the Downloads CPT notebook: r64/alpha64, dropout0, nine target
projection names, one epoch, LR2e-4, cosine, warmup fraction.05, sequence2048,
batch2/accum4, wrapped packing, raw-text loss. Explicit changes: fixed revisions,
seed3407, filtered/disjoint documents, final dev evaluation instead of every100
steps, local logging initially. No claim of exact notebook reproduction. Wrapped
packing permits cross-document context, following the notebook; EOS separates
documents. Do not call CPT authored-thinking supervision.

```bash
"$PY" scripts/training/train_lfm3_cpt.py --experiment-dir "$EXP" --output-dir "$EXP/results-local/cpt-smoke-v01" --smoke
"$PY" scripts/training/train_lfm3_cpt.py --experiment-dir "$EXP" --output-dir "$EXP/results-local/cpt-overfit-v01" --tiny-overfit
```

Check actual-model label audit, finite loss/gradients, adapter save and tiny-set
loss decrease. CPU random-model checks do not satisfy these GPU gates. Preserve
diagnostic adapters separately; full CPT starts fresh from the original model.
Only after inspecting actual evidence write `data-local/gpu-gate.json` with true
`baseline_completed`, `training_smoke_passed`, `labels_audited`,
`tiny_overfit_passed`, the pinned `model_revision`, and SHA256 of the active
`cpt-data-manifest-v02.json`. Attach actual baseline/smoke/overfit output paths in
the same file. This file must describe observed checks, never planned success.

```bash
"$PY" scripts/training/train_lfm3_cpt.py --experiment-dir "$EXP" --output-dir "$EXP/results-local/cpt-v01"
```

`wiki_dev` is for diagnostics; `wiki_eval` and `web_eval` never enter training or
trainer checkpoint selection. Read `cpt-token-profile-v02.json` for raw token
exposure; actual packed label tokens/steps must be recorded on the pod. Warmup
and one epoch do not guarantee a particular number of optimization updates.

## CPT evaluation and recovery

Repeat the three full evaluation commands into a new `results-local/cpt-eval-v01`
folder, adding `--adapter "$EXP/results-local/cpt-v01/adapter"` to each generator.
Same500 questions,1600 grammar pairs and200 text documents, same scoring and
decoding settings. Preserve adapter hashes, raw outputs and termination counts.

Before stopping the pod, package this track and all its scripts/results/adapters:

```bash
"$PY" scripts/evaluation/package_lfm3_artifacts.py --repo-root . --output /workspace/lfm3-completed.tar.gz
```

Download archive AND adjacent `.json` receipt. Reopen locally, verify archive
SHA256 and every member checksum, check expected output counts and adapter
presence, then report recovery status. Include setup log, pip freeze and GPU
details under results-local. W&B is currently off explicitly; local logs are
mandatory. A later W&B upload/configuration must preserve run identities and
must not imply that these prepared runs have already occurred.
