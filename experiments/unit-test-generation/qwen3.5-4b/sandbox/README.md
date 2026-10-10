# Protected execution foundation

Build and check from repository root:

```sh
docker build -t llm-bender-pytest:integration-v01 experiments/unit-test-generation/qwen3.5-4b/sandbox
.venv/bin/python experiments/unit-test-generation/qwen3.5-4b/sandbox/check_isolation.py
```

The trusted synthetic probe checks read-only production/root filesystem,
disabled network, non-root execution, no home mount and preserved host source
hash. Runs apply process/memory/CPU limits and a 30-second host timeout.
This is an execution foundation, not a completed verifier or Pi sandbox.

Pending: generated-test write controls, independently observed pytest results,
runtime oracle instrumentation, forged-result defenses, semantic bug detection,
task-specific dependencies, raw episode logging and adversarial tests. Never
mount a Docker socket, user home, secrets or private grading data into agent
execution. Pi tool allowlists do not enforce these container permissions.
