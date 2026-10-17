"""One bounded Pi text-generation smoke; never executes model-generated code."""
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

from pi_request_recorder import LocalRequestRecorder

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "experiments/unit-test-generation/qwen3.5-4b/exp-000-baseline"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", default="tomlkit-toml-table-converters")
    parser.add_argument("--with-approved-context", action="store_true")
    parser.add_argument("--context-file", type=Path)
    parser.add_argument("--thinking", choices=["off", "medium"])
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument("--protocol-file", type=Path, help="Require a ready frozen packet and use pinned Stage A settings")
    args = parser.parse_args()
    protocol = json.loads(args.protocol_file.read_text()) if args.protocol_file else None
    if protocol:
        for relative, expected_hash in protocol["source_code_sha256"].items():
            if sha256((ROOT / relative).read_bytes()).hexdigest() != expected_hash:
                raise ValueError(f"Code differs from the frozen protocol: {relative}")
        expected = protocol["generation"]
        if args.thinking is not None and args.thinking != expected["thinking"]:
            raise ValueError("Thinking override conflicts with frozen protocol")
        if args.max_output_tokens is not None and args.max_output_tokens != expected["max_output_tokens"]:
            raise ValueError("Output override conflicts with frozen protocol")
        args.thinking, args.max_output_tokens = expected["thinking"], expected["max_output_tokens"]
    else:
        args.thinking, args.max_output_tokens = args.thinking or "off", args.max_output_tokens or 3072
    if not 1 <= args.max_output_tokens <= 6144:
        raise ValueError("Output cap must be between 1 and 6144 tokens")
    manifest_path = BASELINE / "requirements-pilot/candidate-manifest.json"
    if protocol and sha256(manifest_path.read_bytes()).hexdigest() != protocol["candidate_manifest_sha256"]:
        raise ValueError("Candidate manifest differs from the frozen protocol")
    manifest = json.loads(manifest_path.read_text())
    task = next(t for t in manifest["tasks"] if t["task_id"] == args.task_id)
    packet = Path(task["packet_directory"])
    prompt = (packet / "tests-first-prompt.md").read_text()
    if sha256(prompt.encode()).hexdigest() != task["prompt_sha256"]:
        raise ValueError("Prepared prompt hash changed")
    context_hash = None
    if args.with_approved_context and args.context_file:
        raise ValueError("Choose one context source")
    if args.context_file:
        context = args.context_file.read_text()
        context_hash = sha256(context.encode()).hexdigest()
        prompt += "\nAPPROVED EXISTING PUBLIC API CONTEXT:\n" + context
    if args.with_approved_context:
        context = (packet / "public-api-context.md").read_text()
        context_hash = sha256(context.encode()).hexdigest()
        prompt += "\nAPPROVED EXISTING PUBLIC API CONTEXT:\n" + context
    registry_hash = None
    if protocol:
        registry_path = args.protocol_file.parent / protocol["task_input_registry"]
        registry_hash = sha256(registry_path.read_bytes()).hexdigest()
        registered = json.loads(registry_path.read_text())["tasks"][args.task_id]
        if registered["status"] != "ready_for_stage_a":
            raise ValueError("Task input has not passed preflight or is quarantined")
        if registered["context_sha256"] != context_hash:
            raise ValueError("Public context differs from the frozen task packet")
        if registered["effective_prompt_sha256"] != sha256(prompt.encode()).hexdigest():
            raise ValueError("Effective prompt differs from the frozen task packet")
        if (packet / "pilot-v01-run.json").exists():
            raise ValueError("This task already has a recorded pilot attempt; preserve it")
    version = subprocess.check_output(["pi", "--version"], text=True).strip()
    if version != "1.0.3":
        raise ValueError("This smoke is pinned to Pi 1.0.3")
    with urlopen("http://127.0.0.1:18080/health", timeout=3) as response:
        if json.load(response).get("status") != "ok":
            raise ValueError("Model server not ready")
    run = packet / ("smoke-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    run.mkdir()
    if protocol:
        (packet / "pilot-v01-run.json").write_text(json.dumps({"run_directory": str(run), "status": "started",
            "protocol_sha256": sha256(args.protocol_file.read_bytes()).hexdigest()}, indent=2)+"\n")
    (run / "effective-prompt.md").write_text(prompt)
    config_dir = run / "pi-config"
    config_dir.mkdir()
    config = json.loads((BASELINE / "pi-models.integration.json").read_text())
    with urlopen("http://127.0.0.1:18080/props", timeout=3) as response:
        server_context = json.load(response)["default_generation_settings"]["n_ctx"]
    config["providers"]["bender-local"]["models"][0]["contextWindow"] = server_context
    if protocol and server_context != protocol["model_context_tokens"]:
        raise ValueError("Server context differs from the frozen protocol")
    config["providers"]["bender-local"]["models"][0]["maxTokens"] = args.max_output_tokens
    (config_dir / "models.json").write_text(json.dumps(config, indent=2)+"\n")
    system = "You generate Python pytest tests from requirements. Follow the user's requested output format."
    command = ["pi", "--offline", "--provider", "bender-local", "--model", "qwen3.5-4b-q4-k-m",
               "--thinking", args.thinking, "--no-extensions", "--no-skills", "--no-context-files",
               "--no-prompt-templates", "--no-themes", "--no-tools", "--no-session",
               "--system-prompt", system, "--mode", "json", "-p", prompt]
    environment = dict(os.environ, PI_CODING_AGENT_DIR=str(config_dir), PI_TELEMETRY="0")
    started = time.monotonic()
    timeout = False
    with LocalRequestRecorder(run / "http-requests") as recorder:
        config["providers"]["bender-local"]["baseUrl"] = recorder.base_url
        (config_dir / "models.json").write_text(json.dumps(config, indent=2)+"\n")
        with (run / "events.jsonl").open("w") as stdout, (run / "stderr.txt").open("w") as stderr:
            try:
                result = subprocess.run(command, cwd=run, env=environment, stdout=stdout,
                                        stderr=stderr, timeout=240)
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                timeout = True
                exit_code = None
    events = []
    for line in (run / "events.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    messages = [e["message"] for e in events if e.get("type") == "message_end"
                and e.get("message", {}).get("role") == "assistant"]
    text = "\n".join(c.get("text", "") for m in messages for c in m.get("content", [])
                     if c.get("type") == "text")
    (run / "model-output.txt").write_text(text)
    blocks = re.findall(r"```(?:python|py)\s*\n(.*?)```", text, flags=re.DOTALL)
    code = blocks[0] if len(blocks) == 1 else None
    syntax = None
    test_count = None
    if code is not None:
        (run / "generated_tests.py").write_text(code)
        try:
            tree = ast.parse(code)
            syntax = True
            test_count = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and n.name.startswith("test_") for n in ast.walk(tree))
        except SyntaxError:
            syntax = False
    report = {"task_id": args.task_id, "phase": "requirements-to-tests generation smoke",
              "model": "Qwen3.5-4B-Q4_K_M", "pi_version": version,
              "prompt_sha256": sha256(prompt.encode()).hexdigest(), "system_prompt": system,
              "approved_context_sha256": context_hash,
              "protocol_sha256": sha256(args.protocol_file.read_bytes()).hexdigest() if protocol else None,
              "task_registry_sha256": registry_hash,
              "recorded_requests": recorder.requests,
              "server_and_pi_context_tokens": server_context,
              "config_sha256": sha256((config_dir / "models.json").read_bytes()).hexdigest(),
              "thinking": args.thinking, "max_output_tokens": args.max_output_tokens, "timeout_seconds": 240,
              "elapsed_seconds": round(time.monotonic()-started, 3),
              "process_exit_code": exit_code, "timed_out": timeout,
              "assistant_stop_reasons": [m.get("stopReason") for m in messages],
              "usage": [m.get("usage") for m in messages],
              "python_block_count": len(blocks), "syntax_valid": syntax,
              "test_function_count": test_count, "execution": "not run",
              "semantic_correctness": "unreviewed", "baseline_score": None,
              "run_directory": str(run)}
    report["request_settings_verified"] = bool(recorder.requests) and all(
        r["max_tokens"] == args.max_output_tokens and
        (r.get("chat_template_kwargs") or {}).get("enable_thinking") == (args.thinking != "off")
        for r in recorder.requests)
    if protocol:
        report["request_settings_verified"] = report["request_settings_verified"] and all(
            all(r.get(k) == v for k, v in protocol["request_sampling"].items()) for r in recorder.requests)
    (run / "summary.json").write_text(json.dumps(report, indent=2)+"\n")
    if protocol:
        (packet / "pilot-v01-run.json").write_text(json.dumps({"run_directory": str(run), "status": "recorded",
            "protocol_sha256": report["protocol_sha256"]}, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    if timeout or exit_code != 0 or not messages or (protocol and not report["request_settings_verified"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
