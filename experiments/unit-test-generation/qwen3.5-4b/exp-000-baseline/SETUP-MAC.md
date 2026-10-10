# Mac integration setup

## Chosen connection

Use standalone llama.cpp with Pi CLI. LM Studio is a useful interactive model
browser, but this experiment uses explicit server arguments and one pinned GGUF.
All model inference runs locally on the Mac's integrated Apple GPU/Metal.

From repository root, start the server in one terminal:

```sh
bash experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/start-server.sh
```

In another terminal, launch Pi with the model already selected:

```sh
bash experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/run-pi.sh
```

For CLI generation with thinking enabled:

```sh
bash experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/run-pi.sh --thinking medium --no-session --mode json -p 'Explain the behavior of the Python function in this directory.'
```

Pi starts in the invoking directory. The wrapper uses a dedicated config,
disables discovered extensions/context and selects read-only tools initially.
Protected test writing/execution will be enabled with the task harness. Current
1024-token per-call allowance is an integration setting, not a frozen benchmark
budget. The server stays foreground; Ctrl-C stops it.

This setup is for integration checks, not a frozen benchmark protocol. Exact
versions and artifact identity are in `environment-mac.json` and
`config-planned.json`. Model weights live outside Git.

Install Pi explicitly:

```sh
npm install --global --prefix "$HOME/.local" --ignore-scripts @earendil-works/pi-coding-agent@1.0.3
pi --version
```

The installed Homebrew llama.cpp 0.5.0 corresponds to commit
`7fe450e19305b828c199d602c23a8337aaa1f03b`, build 11146. Homebrew may resolve a
different release later; verify the manifest rather than assuming `brew install`
recreates this version. LM Studio's existing bundled servers are separate builds.

From repository root, recreate the evaluation environment:

```sh
uv venv --python 3.11.15 .venv
uv pip install --python .venv/bin/python -r experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline/requirements-mac.lock.txt
```

Run `bash start-server.sh` from this directory after downloading and verifying
the pinned GGUF. Default endpoint: `http://127.0.0.1:18080`. Initial context is
8192 with one slot; this is a measured-integration starting point, not a selected
agent budget. No vision projector is needed for text-only tasks.

Pi's installed llama.cpp extension detects thinking support from the server's
template and uses its Qwen template compatibility path. Verify actual requests
and outputs before accepting UI thinking choices as experimental conditions.

Docker CLI exists but the daemon was not running at inspection. Protected
execution and Argilla setup are pending. A Pi tool allowlist alone is not a
security boundary for benchmark code.

## Integration results

Pinned Q4_K_M loaded successfully. Direct thinking off/on and structured tool
calls worked. Pi 1.0.3 completed a read-tool round trip in both modes using
`pi-models.integration.json`, with traces in `results/integration-20261005/`.
This custom endpoint config bypasses router catalog discovery; it does not alter
the owner's global Pi configuration. The first native-provider catalog attempt
listed no models; router integration remains optional pending validation.

Thinking-on traces contain reasoning, but Pi reports `usage.reasoning = 0`; do
not use that field as accurate reasoning-token accounting yet. Total generated
tokens include the reasoning output. Direct 256-token thinking-on arithmetic
truncated in reasoning; tool integration used a 1024-token per-call allowance.
These are synthetic checks, not benchmark scores. A server RSS snapshot was
about 3.5 GiB, not a peak unified-memory measurement.
