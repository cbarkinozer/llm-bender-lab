"""Generate a TOMLKit implementation through Pi, enforcing the Stage A freeze.

Model output is applied only to a new external worktree and never executed here.
"""
import argparse
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline"
CACHE = Path.home() / ".cache/llm-bender-lab"
TASK = "tomlkit-toml-table-converters"
BASE_COMMIT = "dd05eebc8ed9e30fc6c223088a5a450cb54c1cab"
ALLOWED = {"tomlkit/convert.py": "CREATE", "tomlkit/exceptions.py": "APPEND", "tomlkit/__init__.py": "APPEND"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=["tests-first", "direct"], required=True)
    parser.add_argument("--tests-run", type=Path)
    parser.add_argument("--context-file", type=Path, required=True)
    args = parser.parse_args()
    version = subprocess.check_output(["pi", "--version"], text=True).strip()
    if version != "1.0.3":
        raise ValueError("This diagnostic is pinned to Pi 1.0.3")
    frozen = None
    tests = None
    if args.condition == "tests-first":
        if args.tests_run is None:
            raise ValueError("Tests-first implementation requires a frozen Stage A run")
        freeze = json.loads((args.tests_run / "freeze.json").read_text())
        if freeze["decision"] != "accepted_for_development" or freeze["task_id"] != TASK:
            raise ValueError("Stage A has not accepted this task's suite")
        review = json.loads((args.tests_run / "stage-a-review.json").read_text())
        preflight = json.loads((args.tests_run / "reference-preflight.json").read_text())
        if review["decision"] != "accepted_for_development" or preflight["process_exit_code"] != 0:
            raise ValueError("Stage A review or correct-reference execution failed")
        tests = (args.tests_run / "generated_tests.py").read_bytes()
        frozen = sha256(tests).hexdigest()
        if frozen != freeze["test_sha256"]:
            raise ValueError("Frozen tests changed")
        if frozen != preflight["generated_test_sha256"]:
            raise ValueError("Preflight did not validate these frozen bytes")
    packet = CACHE / "requirements-pilot-v01" / TASK
    requirement = (packet / "requirement.md").read_text()
    context = args.context_file.read_text()
    prompt = """Implement the English requirement in the pinned TOMLKit repository.
Return exactly three fenced Python blocks. Each block's first line must be its
operation header, in this format:
```python
# CREATE tomlkit/convert.py
<complete new module code>
```
```python
# APPEND tomlkit/exceptions.py
<new ConversionError definition only; TOMLKitError already exists>
```
```python
# APPEND tomlkit/__init__.py
<imports and __all__ additions for the new public functions only>
```
Do not repeat or replace existing files. Do not write or modify tests, monkeypatch
pytest, hardcode answers to specific tests or import a reference implementation.
Implement all required behavior, including value/comment preservation and errors.
Use the existing public APIs described below. No reference solution is available.

ENGLISH REQUIREMENT:
""" + requirement + "\n\nEXISTING API CONTEXT:\n" + context
    if tests is not None:
        prompt += "\n\nFROZEN GENERATED TESTS (read-only; do not weaken them):\n```python\n" + tests.decode() + "\n```\n"
    run = packet / ("implementation-" + args.condition + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    run.mkdir()
    (run / "effective-prompt.md").write_text(prompt)
    config_dir = run / "pi-config"
    config_dir.mkdir()
    config = json.loads((BASELINE / "pi-models.integration.json").read_text())
    with urlopen("http://127.0.0.1:18080/props", timeout=3) as response:
        server_context = json.load(response)["default_generation_settings"]["n_ctx"]
    config["providers"]["bender-local"]["models"][0]["contextWindow"] = server_context
    # Equal output allowance for a later paired comparison: tests 3072 + code 3072,
    # or direct code 6144. These development runs are not a frozen benchmark.
    cap = 3072 if args.condition == "tests-first" else 6144
    config["providers"]["bender-local"]["models"][0]["maxTokens"] = cap
    (config_dir / "models.json").write_text(json.dumps(config, indent=2)+"\n")
    command = ["pi", "--offline", "--provider", "bender-local", "--model", "qwen3.5-4b-q4-k-m",
               "--thinking", "off", "--no-extensions", "--no-skills", "--no-context-files",
               "--no-prompt-templates", "--no-themes", "--no-tools", "--no-session",
               "--system-prompt", "You implement Python features from requirements using existing library APIs.",
               "--mode", "json", "-p", prompt]
    started = time.monotonic()
    timed_out = False
    with (run / "events.jsonl").open("w") as stdout, (run / "stderr.txt").open("w") as stderr:
        try:
            result = subprocess.run(command, cwd=run,
                                    env=dict(os.environ, PI_CODING_AGENT_DIR=str(config_dir), PI_TELEMETRY="0"),
                                    stdout=stdout, stderr=stderr, timeout=480 if args.condition == "direct" else 240)
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
    messages = []
    for line in (run / "events.jsonl").read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "message_end" and event.get("message", {}).get("role") == "assistant":
            messages.append(event["message"])
    text = "\n".join(c.get("text", "") for m in messages for c in m.get("content", []) if c.get("type") == "text")
    (run / "model-output.txt").write_text(text)
    blocks = re.findall(r"```python\s*\n# (CREATE|APPEND) (tomlkit/[a-z_]+\.py)\s*\n(.*?)```", text, re.DOTALL)
    report = {"task_id": TASK, "condition": args.condition, "run_directory": str(run),
              "pi_version": version,
              "prompt_sha256": sha256(prompt.encode()).hexdigest(), "context_sha256": sha256(context.encode()).hexdigest(),
              "frozen_test_sha256": frozen, "max_output_tokens": cap,
              "server_and_pi_context_tokens": server_context,
              "elapsed_seconds": round(time.monotonic()-started, 3), "process_exit_code": exit_code,
              "timed_out": timed_out, "usage": [m.get("usage") for m in messages],
              "stop_reasons": [m.get("stopReason") for m in messages],
              "output_block_count": len(blocks), "applied": False, "code_executed": False}
    try:
        if exit_code != 0 or timed_out or not messages or any(m.get("stopReason") != "stop" for m in messages):
            raise ValueError("Incomplete model generation")
        if len(blocks) != 3 or {path: op for op, path, _ in blocks} != ALLOWED:
            raise ValueError("Output did not follow the three-file allowlist")
        base_repo = CACHE / "requirements-reference-preflight" / TASK / "repository"
        # Read original files through git, never from the patched reference tree.
        combined = {}
        for operation, path, content in blocks:
            base = "" if operation == "CREATE" else subprocess.check_output(
                ["git", "-C", str(base_repo), "show", f"{BASE_COMMIT}:{path}"], text=True)
            combined[path] = base + "\n" + content + "\n"
            ast.parse(combined[path], filename=path)
        workspace = run / "workspace"
        subprocess.run(["git", "-C", str(base_repo), "worktree", "add", "--quiet", "--detach", str(workspace), BASE_COMMIT], check=True)
        for path, content in combined.items():
            (workspace / path).write_text(content)
        subprocess.run(["git", "-C", str(workspace), "add", "--intent-to-add", "tomlkit/convert.py"], check=True)
        (run / "model.patch").write_bytes(subprocess.check_output(["git", "-C", str(workspace), "diff", "--binary"]))
        report.update(applied=True, workspace=str(workspace), changed_files=sorted(combined))
        if tests is not None:
            (run / "frozen_tests.py").write_bytes(tests)
            if sha256((args.tests_run / "generated_tests.py").read_bytes()).hexdigest() != frozen:
                raise ValueError("Original tests changed during implementation")
    except (ValueError, SyntaxError, subprocess.CalledProcessError) as error:
        report["application_error"] = str(error)
    (run / "summary.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    if not report["applied"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
