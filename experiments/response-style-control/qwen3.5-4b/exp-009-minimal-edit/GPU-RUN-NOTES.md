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
