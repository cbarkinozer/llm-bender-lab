# Running Occam 2

2026-10-29: the [failure-guided revision](FAILURE-GUIDED-REVISION.md) supersedes
the generic draft selection. These scripts remain infrastructure; held-out
baseline/full training are disabled while `data_selection_ready` is false.
Do not use the older external Colab v1/v2 ZIPs to bypass this revised plan.

Start from this model directory. Keep weights, tokenized data and run outputs
outside Git. Python3.11+ required. A compatible working GPU environment must be
tested and frozen before full training. No paid compute is provisioned by these files.

## Local preparation (already exercised)

```sh
python pipeline.py build
python pipeline.py prepare --output /EXTERNAL/occam2/prepared-v1 --max-length 1024
HF_HUB_OFFLINE=1 python -m unittest discover -s . -p test_pipeline.py -v
python audit_overlap.py --output /EXTERNAL/occam2/overlap.json
```

`prepare` downloads only tokenizer/config files for the pinned original model.
It reads only train targets for encoding, saves exact supervised-text previews,
and refuses any truncation. Review the previews and token report.

The preparation was exercised in the existing external export environment with
Transformers5.20.2, tokenizers0.23.3, Jinja2 3.1.6, PyTorch2.14.1,
PEFT0.21.2 and Accelerate1.15.0. Those observations are not a CUDA environment lock.
The training host should retain its CUDA-compatible PyTorch installation, install
the pinned model libraries, and record `pip freeze`, driver and GPU details.

## CUDA baseline, diagnostics, training, candidate

Use a BF16-capable CUDA GPU (for example L4/A100); this recipe deliberately
rejects T4/FP16 and Mac MPS rather than silently changing precision.
The native reference kernels can be slow without optional causal-conv1d and
flash-linear-attention; optimized-kernel installation is a separate host setup
decision. The local CPU integration check does not establish 4B CUDA memory fit.

```sh
python evaluate.py --backend hf --split dev --output /EXTERNAL/occam2/dev-base
python evaluate.py --backend hf --split test --output /EXTERNAL/occam2/base
python evaluate.py --backend hf --split regression --output /EXTERNAL/occam2/base-regression
python train.py --mode smoke --prepared /EXTERNAL/occam2/prepared-v1 --output /EXTERNAL/occam2/smoke
python train.py --mode tiny --prepared /EXTERNAL/occam2/prepared-v1 --output /EXTERNAL/occam2/tiny
```

Inspect both diagnostic manifests, finite losses and saved/reloaded training-prompt
output. The tiny gate requires at least20% loss reduction on eight training cases;
this is a gradient/learning check, not proof of semantic memorization or test gain.
If diagnostics fail, stop and diagnose before training. Infrastructure fixes must
retain their traces. If protocol or recipe changes after held-out baseline feedback,
use a new holdout; do not mine test errors to improve training targets.

```sh
python train.py --mode full --prepared /EXTERNAL/occam2/prepared-v1 \
  --baseline /EXTERNAL/occam2/base/evaluation-manifest.json \
  --smoke-evidence /EXTERNAL/occam2/smoke/run-manifest.json \
  --tiny-evidence /EXTERNAL/occam2/tiny/run-manifest.json \
  --output /EXTERNAL/occam2/sft
python evaluate.py --backend hf --split test --adapter /EXTERNAL/occam2/sft/adapter \
  --output /EXTERNAL/occam2/candidate
python evaluate.py --backend hf --split regression --adapter /EXTERNAL/occam2/sft/adapter \
  --output /EXTERNAL/occam2/candidate-regression
```

Every run gets a fresh output folder; no automatic overwrite or incorrect-answer
retries. The30-step final checkpoint is preselected. Save manifests, adapter,
checksums, raw outputs and scoring outside ephemeral GPU storage before shutdown.

## Review

Only after both runs, score final answers against `data-v1/test-keys.jsonl` using
the frozen [scoring rules](exp-001-thinking-sft/data-v1/README.md). Review all20
pairs. Keep initial judgments, assisted adjudication and any repairs separate.
Report correct/partial/wrong counts, paired fixes/regressions, truncation,
Turkish reasoning adherence, unsupported claims, tokens and latency.

```sh
python review.py prepare --base /EXTERNAL/occam2/base \
  --candidate /EXTERNAL/occam2/candidate --output /EXTERNAL/occam2/review
# Fill semantic_score and review fields in ratings.json; keep mapping.json hidden.
python review.py summarize --review /EXTERNAL/occam2/review
```

The review script refuses mismatched runtime/settings, changed output hashes,
missing IDs and incomplete ratings. A/B ordering is randomized reproducibly.

## Optional local Mac development diagnostic

Start a dedicated llama-server with the existing untouched Q4_K_M artifact,
thinking enabled, reasoning-format deepseek, context8192 and parallel1, then:

```sh
python evaluate.py --backend http --split dev \
  --gguf /LOCAL/PATH/Qwen3.5-4B-Q4_K_M.gguf \
  --output /EXTERNAL/occam2/dev-local
```

This is not the primary BF16 baseline. HTTP held-out evaluation is disabled to
prevent accidental comparison of quantized baseline with native adapter weights.

## Colab

`Occam2-Thinking-SFT.ipynb` runs the same scripts, not a separate recipe. Upload
the whitelist ZIP made by `make_colab_bundle.py`, select a BF16-capable GPU,
and use Drive for retained artifacts. Free T4 sessions do not meet this recipe.
No GPU session is started by generating the notebook or bundle locally.
