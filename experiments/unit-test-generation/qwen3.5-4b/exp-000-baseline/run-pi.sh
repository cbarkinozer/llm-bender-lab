#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
pi_config_dir="${BENDER_PI_CONFIG_DIR:-$HOME/.cache/llm-bender-lab/pi-local}"
server_port="${BENDER_SERVER_PORT:-18080}"
if [[ "$(pi --version)" != "1.0.3" ]]; then
  echo 'This recipe requires Pi 1.0.3; check the environment manifest.' >&2
  exit 1
fi
if ! curl --fail --silent --max-time 3 "http://127.0.0.1:$server_port/health" >/dev/null; then
  echo "Start the model server first: bash $script_dir/start-server.sh" >&2
  exit 1
fi
mkdir -p "$pi_config_dir"
python3 - "$script_dir/pi-models.integration.json" "$pi_config_dir/models.json" "$server_port" <<'PY'
import json, sys
from pathlib import Path
config = json.loads(Path(sys.argv[1]).read_text())
config['providers']['bender-local']['baseUrl'] = f'http://127.0.0.1:{int(sys.argv[3])}/v1'
Path(sys.argv[2]).write_text(json.dumps(config, indent=2) + '\n')
PY
# Keep owner's ordinary Pi configuration separate from this experiment.
# Read-only tools are the integration default until protected execution is ready.
export PI_CODING_AGENT_DIR="$pi_config_dir"
exec pi --offline --provider bender-local --model qwen3.5-4b-q4-k-m \
  --thinking off --no-extensions --no-skills --no-context-files \
  --no-prompt-templates --no-themes --tools read,grep,find,ls "$@"
