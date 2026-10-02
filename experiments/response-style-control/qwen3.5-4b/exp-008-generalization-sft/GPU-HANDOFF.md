# GPU handoff

Execution completed on 2026-10-02 on the user-provided Vast RTX 4090.
This document preserves the pre-run recipe; see `GPU-RUN-NOTES.md` for
actual gates, training, artifacts and the pending blind review.

Use the repository's existing Unsloth environment setup and consult
`docs/environment-setup-gotchas.md` before installing on a new/restarted pod.
The previously validated exp-006 host used a Linux RTX 4090 with 24 GB VRAM.
The local GTX 1650 has 4 GB and cannot run the configured BF16 4B recipe.

The first exp-008 pilot uses only the 100 corrected examples, 20 per family,
from the same pinned base model as exp-006. Existing 958 examples are retained
as a separate historical artifact. Hyperparameters match exp-006: 3 epochs,
LR 1e-4, BF16 LoRA rank/alpha 16, effective batch 8, sequence length 1024,
assistant-only loss and no packing. Both composition and training volume change;
this is a small diagnostic pilot, not a clean single-variable comparison.

From a clean committed checkout and activated compatible GPU environment:

The user's latest instruction is to run smoke first. Check GPU/driver, available
disk and persistent venv before installations. Reuse the validated exp-006
package freeze when available; confirm Torch CUDA/BF16 support, Unsloth import
and the TRL/Transformers stack before downloading model weights. The launcher
explicitly sets HF, pip and W&B cache paths under `/workspace`.

```bash
bash experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/run_gpu_preflight.sh smoke-only
```

This runs structural checks, representation validation and 20-step smoke, then
stops. It does not start full training. Inspect the generated evidence before
continuing with base generation and tiny-overfit. Do not reuse partially failed
result directories as completed gates.

```bash
bash experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/run_gpu_preflight.sh
```

Inspect representation, truncation and label masks, smoke finite losses, and
tiny-overfit loss reduction before full training. Only proceed after all gates pass:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/config.yaml \
  --mode full \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/results/full-v1 \
  --smoke-run experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/results/smoke-v1 \
  --tiny-overfit-run experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/results/tiny-overfit-v1

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/evaluate.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/config.yaml \
  --role candidate \
  --adapter experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/results/full-v1/lora-adapter \
  --output experiments/response-style-control/qwen3.5-4b/exp-008-generalization-sft/results/development-candidate-v1.jsonl
```

Use the frozen rubric for a blinded paired review. Broader quality claims still
need independent evaluation. Export run manifests, adapter, raw outputs and
environment metadata from the GPU host before it is terminated.
