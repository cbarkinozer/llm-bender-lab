# exp-009 training preparation — 2026-10-02

## User correction during GPU setup

The user explicitly removed vLLM from the current fine-tuning workflow: existing
base outputs are sufficient, train with Unsloth and use the saved adapter later.
The optional vLLM setup was stopped before completion; its scripts remain history,
not required gates. Verify smoke adapter reload using the training environment;
no merged smoke checkpoint or additional inference engine is required now.
Earlier vLLM smoke requirements below are superseded for this run. Do not
regenerate base answers or launch vLLM setup without a new request.

Local preparation passed. No weights downloaded locally, no GPU contacted,
no training or W&B run started. Approved data/QA artifacts are reviewed-v2.
No historical adapter or old 958-row dataset is used in this phase.

## Verified locally

- 80 training / 20 evaluation-only validation rows; explicit identities preserved.
- Parent artifacts hash-verified; final targets nonempty, no bold/headings.
- Every context turn masked, including prior assistant clarification turns.
- Final response only supervised, including native `<|im_end|>`; trailing template
  newline masked. Native template trims outer whitespace, raw targets unchanged.
- Padding labels stay -100. Four offline regression tests passed.
- Train max sequence 514, median 104; validation max 432, median 90 tokens.
- Train supervised tokens per epoch 5,384; validation 1,151 (no gradients).
- Chosen max length 1,024, zero truncations and zero empty supervised spans.
- Cross-split exact/turn/group/source checks passed; content-only near flags zero.
- All 100 inputs, including revised me-088, checked against 348 historical local
  benchmark rows: zero exact/near flags at 0.78. This is detected overlap only,
  not proof of universal semantic independence.

Evidence: training-preflight-v1/report.json, mask-inspection.json, pinned
tokenizer-template.json and separate tokenized artifacts. These files are small
local reproducibility artifacts; no model weights are included.

## Initial recipe

training-preflight-v1/training-config.json is the executable configuration.
BF16 LoRA from pinned Qwen3.5-4B, rank/alpha 16, dropout 0; known transformer
projection modules retained. LR 5e-5, 2 epochs, microbatch 1, accumulation 8,
effective batch 8, cosine scheduler, two warmup steps, seed 3407, no packing.
Expected 20 optimizer steps on one GPU (10 per epoch); small step count reflects
80 rows, not a failed run. Save/evaluate each epoch; do not judge only by loss.
This is an initial conservative hypothesis, not an established optimal recipe
or a guarantee against forgetting. Versus exp008, data/targets, LR and epochs
change together; do not claim a single-variable ablation.

The old exp004 runner cannot be used unchanged: it rejects multi-turn data and
would supervise earlier assistant context. train_reviewed.py instead consumes
explicit labels through a padding collator, without TRL reformatting. Its GPU
integration is not yet validated. Transformers Trainer is used for training,
not generation; inference remains vLLM. API reference:
https://huggingface.co/docs/transformers/main_classes/trainer

## GPU order (fresh adapter/base each time)

Commit the experiment source before remote execution; runner refuses dirty Git.
Install/record the compatible training stack from prior Vast notes; the CPU
tokenizer environment is not a GPU training dependency lock.

1. representation-check: inspect real trainer batch, all-row masks, module
   placement and actual trainable counts; ensure tokenizer/template matches.
2. smoke: three optimizer steps, finite loss, save adapter. Separately reload it
   and test generation through vLLM; no Transformers generate fallback.
3. tiny-overfit: 16 train-only rows, 40 diagnostic steps, LR 2e-4. Compare
   train-only loss before/after. This diagnostic adapter never seeds full run.
4. Verify W&B online connection from .env without printing credentials. Record
   real gate evidence and configuration hash; do not pre-mark checks passed.
5. Full: fresh pinned base, two epochs. Gate file required; runtime package/GPU,
   Git/config, masks and results saved under a new output directory.

Example (on future GPU, not run yet):

```bash
python train_reviewed.py --mode representation-check --output-dir results/representation-v1
python train_reviewed.py --mode smoke --output-dir results/smoke-v1
python train_reviewed.py --mode tiny-overfit --output-dir results/tiny-v1
python train_reviewed.py --mode full --gates results/gpu-gates.json --output-dir results/full-v1
```

GPU gate schema: training_config_sha256 plus boolean actual_batch_masking,
smoke_finite_loss, adapter_save_reload, tiny_overfit_loss_decreased,
wandb_connected. This manually reviewed gate file references observed checks,
not merely successful process exits.

## Evaluation

Compare base and scheduled adapter on the same 20 validation prompts, pinned
template/no extra system prompt/non-thinking, greedy repetition penalty 1.05,
vLLM, native stopping and identical output budgets. Existing base outputs remain
valid for these unchanged validation inputs. Human references are criteria aids,
not necessarily the only acceptable wording. Measure correctness/completeness,
groundedness, Turkish precision/fluency, clarification resolution, formatting,
anthropomorphism, repetition, termination and task-conditional length. Do not
select by shortness alone. Twenty development rows do not establish broad
retention; separate retention evaluation would require its own fixed protocol.

## Local environment / issues

CPU-only env C:/Temp/llm-bender-exp009-preflight, Python 3.12.3,
transformers 4.57.6, tokenizers 0.22.2, huggingface-hub 0.36.2, jinja2 3.1.6.
Pinned tokenizer revision 3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636.
First preflight failed target roundtrip on me-041 because native template trims
trailing whitespace. Corrected verifier to compare stripped outer whitespace;
rerun passed all rows without rewriting source answers. Windows symlink warning
is cache efficiency only; tokenizer downloaded without model weights.

Remaining runtime checks are GPU-dependent and explicitly not claimed passed.
