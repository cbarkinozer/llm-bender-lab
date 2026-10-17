#!/usr/bin/env bash
set -euo pipefail
# Integration setup only; final benchmark budgets are not frozen.
model_path="${BENDER_GGUF_PATH:-$HOME/.cache/llm-bender-lab/models/Qwen3.5-4B-Q4_K_M.gguf}"
context_tokens="${BENDER_CONTEXT_TOKENS:-8192}"
expected_sha="00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4"
actual_sha="$(shasum -a 256 "$model_path" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo 'GGUF SHA256 mismatch; refusing to start.' >&2
  exit 1
fi
exec llama-server --model "$model_path" --alias qwen3.5-4b-q4-k-m \
  --host 127.0.0.1 --port "${BENDER_SERVER_PORT:-18080}" \
  --ctx-size "$context_tokens" --parallel 1 --jinja --reasoning-format deepseek \
  --n-gpu-layers 99
