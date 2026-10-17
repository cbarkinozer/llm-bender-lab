"""Run a preserved generated suite against a prepared reference in bounded Docker.

Diagnostic only: no mutation, reward assignment, test repair or implementation.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time


def tree_hashes(root):
    return {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--reference-directory", type=Path, required=True)
    parser.add_argument("--image", default="llm-bender-pytest:integration-v01")
    parser.add_argument("--memory", default="512m")
    parser.add_argument("--timeout-seconds", type=int, default=45)
    args = parser.parse_args()
    run, reference = args.run_directory.resolve(), args.reference_directory.resolve()
    tests = run / "generated_tests.py"
    if not tests.is_file() or not reference.is_dir():
        raise ValueError("Missing generated suite or prepared reference")
    if (run / "reference-preflight.json").exists():
        raise ValueError("Preflight already recorded; preserve the existing result")
    summary = json.loads((run / "summary.json").read_text())
    image = subprocess.check_output(
        ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"],
        text=True, timeout=10).strip()
    before = tree_hashes(reference)
    test_hash = sha256(tests.read_bytes()).hexdigest()
    command = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--pids-limit", "64", "--memory", args.memory, "--cpus", "1",
               "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--env", "PYTHONPATH=/reference",
               "--env", "HOME=/tmp", "--mount", f"type=bind,src={reference},dst=/reference,readonly",
               "--mount", f"type=bind,src={tests},dst=/generated/test_generated.py,readonly",
               image, "python", "-m", "pytest", "-q", "-c", "/dev/null",
               "-p", "no:cacheprovider", "--rootdir=/generated", "/generated/test_generated.py"]
    started = time.monotonic()
    timed_out = False
    # Host timeout is diagnostic; docker stop by unique name ensures no orphan.
    container_name = "bender-preflight-" + sha256(str(run).encode()).hexdigest()[:16]
    command[2:2] = ["--name", container_name]
    with (run / "reference-pytest.stdout.txt").open("w") as stdout, (run / "reference-pytest.stderr.txt").open("w") as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=args.timeout_seconds)
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
            subprocess.run(["docker", "rm", "--force", container_name], capture_output=True, timeout=15)
    report = {"task_id": summary["task_id"], "purpose": "original-suite reference execution diagnostic",
              "run_directory": str(run), "reference_directory": str(reference),
              "docker_image_id": image, "command": command,
              "generated_test_sha256": test_hash, "process_exit_code": exit_code,
              "timed_out": timed_out, "elapsed_seconds": round(time.monotonic()-started, 3),
              "reference_source_hashes_preserved": before == tree_hashes(reference),
              "generated_tests_hash_preserved": test_hash == sha256(tests.read_bytes()).hexdigest(),
              "baseline_score": None, "semantic_correctness": "requires independent requirement review"}
    (run / "reference-preflight.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    print((run / "reference-pytest.stdout.txt").read_text()[-12000:])


if __name__ == "__main__":
    main()
