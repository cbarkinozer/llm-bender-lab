# Vast.ai base-draft inference, 2026-10-02

- RTX 4090 24 GB, NVIDIA driver 580.95.05; direct SSH port 38622.
- Persistent environment `/workspace/.venvs/exp009-vllm`, model cache
  `/workspace/.cache/huggingface`, uv cache `/workspace/.cache/uv`.
- User requires vLLM inference (SGLang alternative); no Transformers/Unsloth
  generation, no training, no W&B. Tokenizer/config utilities are not the engine.
- Frozen v2 prompts remain unchanged: 100 rows, 80 train / 20 validation.
- Initial vLLM 0.17.1 installation loaded Torch 2.10.0+cu128 successfully.
  First smoke failed before inference: Transformers 4.x did not recognize
  `qwen3_5` in AutoConfig. Failed output and setup logs are retained.
- Attempted vLLM 0.18.0 plus Transformers 5.5.0 resolution failed because
  vLLM 0.18.0 declares Transformers <5. No model generation occurred.
- Next compatibility attempt: vLLM 0.20.1 with its declared dependencies.
  Record actual package freeze and smoke outcome before accepting this stack.
- vLLM 0.20.1 installs Torch 2.11.0. The runner must use vLLM's
  `get_config` registry for Qwen3.5 rather than plain AutoConfig on the
  resolved Transformers 4.x stack. The pinned checkpoint has no separate
  `generation_config.json`; derive its generation config from the model
  config, retaining the tokenizer EOS fallback. Both startup failures are
  preserved in smoke2/smoke3 logs and manifests.
- All 100 answers can be edited by the user, but the 20 validation answers
  remain evaluation-only. Never merge validation references into training.
- Download logs, manifests, raw answers and source snapshot before shutdown.
  Do not stop or destroy the paid instance automatically.

## Confirmed smoke and full-run observation

Smoke5 passed on vLLM 0.20.1: me-053 (802 tokens), me-073 (2 tokens),
me-081 (501 tokens), all native end-of-turn. The checker must recognize
`<|im_end|>` (248046) as well as model-config EOS (248044), and inspect
the final token because vLLM can report `finish_reason=stop, stop_reason=null`.
Original smoke4 artifacts retain the initial checker misclassification.

The full greedy run hit 4096 tokens on me-001 in an "Apartmanın değil"
repetition loop. A larger cap is not evidence this loop will terminate.
Do not treat the attempt as a completed review draft. User confirmation was
requested before replacing the frozen decoding protocol with the official
Qwen non-thinking general-task sampling recipe. Preserve failed attempts,
and use one consistent documented recipe across both splits and later comparisons.

Official reference: https://huggingface.co/Qwen/Qwen3.5-4B
(non-thinking general tasks: temperature 0.7, top_p 0.8, top_k 20,
min_p 0, presence_penalty 1.5, repetition_penalty 1).

## User-approved minimal decoding adjustment

The user chose testing a small repetition-penalty increase before changing
sampling. A five-row vLLM diagnostic at **1.05**, with greedy decoding and
all other settings unchanged, completed naturally: me-001, me-021, me-073,
me-079, me-081. Me-001 stopped at 721 tokens rather than looping to 4096.
This is a stopping gate, not evidence of correct answers or no quality harm:
grammar explanations, unsupported additions and needless clarification remain
visible in the base drafts and are deliberately preserved for human review.

The full run uses `generate_vllm.py --repetition-penalty 1.05`, with effective
penalty recorded in `run-manifest.json` and CLI arguments. The original
`generation-config.json` remains the historical 1.0 recipe. Only this one
decoding parameter changed; no sampling switch, prompt edits or split edits.
Use 1.05 for the later base/fine-tuned comparison unless a new protocol is
explicitly approved and both versions are evaluated under it.

## Completion

The penalty105 full run completed at 2026-10-02 13:27:20 UTC: 100 native
stops, zero length-limit retries, maximum 1735 output tokens. Final environment:
vLLM 0.20.1, Torch 2.11.0 / CUDA 13.0, Transformers 4.57.6, tokenizers 0.22.2.
The clean generation source commit is 6ba79eb8ff1a006c6a06b10ebfa4ff875158c6f5.
Local backup hashes were matched to the remote artifacts; 80 train and 20
validation records were imported and re-read from Argilla. No training or W&B
logging occurred. GPU memory returned to 0 MiB. See BASE-RUN-REPORT.md.
