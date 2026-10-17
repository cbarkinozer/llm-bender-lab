"""Independently grade a generated TOMLKit workspace with held-back tests.

No grading feedback is sent to Pi. Reference worktree must already contain the
pinned test patch and conformance submodule; reference code is not mounted.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from preflight_requirement_suite import tree_hashes

DRIVER = r'''
import json, pathlib, shutil, subprocess, sys, xml.etree.ElementTree as ET
mode = sys.argv[1]
if mode == 'generated':
    args = ['/generated/frozen_tests.py']
else:
    shutil.copytree('/grader-tests', '/tmp/tests', ignore=shutil.ignore_patterns('.git'))
    args = ['/tmp/tests/test_convert.py'] if mode == 'hidden' else [
        '/tmp/tests', '--ignore=/tmp/tests/toml-test', '--ignore=/tmp/tests/test_formatter.py',
        '--ignore=/tmp/tests/test_merge.py', '--ignore=/tmp/tests/test_convert.py']
r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-c', '/dev/null',
                    '-p', 'no:cacheprovider', '--junitxml=/tmp/report.xml'] + args,
                   capture_output=True, text=True)
counts = None
p = pathlib.Path('/tmp/report.xml')
if p.is_file():
    suites = ET.parse(p).getroot()
    suites = [suites] if suites.tag == 'testsuite' else list(suites)
    counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ['tests', 'failures', 'errors', 'skipped']}
    counts['passed'] = counts['tests'] - counts['failures'] - counts['errors'] - counts['skipped']
print(json.dumps({'pytest_exit_code': r.returncode, 'counts': counts,
                  'stdout': r.stdout, 'stderr': r.stderr}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation-run", type=Path, required=True)
    args = parser.parse_args()
    run = args.implementation_run.resolve()
    summary = json.loads((run / "summary.json").read_text())
    if not summary["applied"]:
        raise ValueError("No valid model implementation was applied")
    if (run / "independent-grading.json").exists():
        raise ValueError("Preserve existing grading; do not overwrite it")
    workspace = Path(summary["workspace"])
    frozen_hash = None
    if summary["condition"] == "tests-first":
        frozen_hash = sha256((run / "frozen_tests.py").read_bytes()).hexdigest()
        if frozen_hash != summary["frozen_test_sha256"]:
            raise ValueError("Implementation-side frozen tests changed")
    grader = Path.home() / ".cache/llm-bender-lab/requirements-reference-preflight/tomlkit-toml-table-converters/reference-hidden-validation/tests"
    if not (grader / "test_convert.py").is_file() or not (grader / "toml-test/tests/files-toml-1.1.0").is_file():
        raise ValueError("Pinned grader tests or submodule fixtures missing")
    before = tree_hashes(workspace)
    image = subprocess.check_output(["docker", "image", "inspect", "llm-bender-pytest:integration-v01", "--format", "{{.Id}}"], text=True).strip()
    modes = ["hidden", "base"]
    if summary["condition"] == "tests-first":
        modes.insert(0, "generated")
    results = {}
    for mode in modes:
        name = "bender-grade-" + run.name[-20:].lower() + "-" + mode
        cmd = ["docker", "run", "--name", name, "--rm", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
               "--memory", "512m", "--cpus", "1", "--tmpfs", "/tmp:rw,noexec,nosuid,size=128m",
               "--env", "PYTHONPATH=/candidate", "--env", "HOME=/tmp",
               "--mount", f"type=bind,src={workspace},dst=/candidate,readonly",
               "--mount", f"type=bind,src={grader},dst=/grader-tests,readonly"]
        if mode == "generated":
            cmd += ["--mount", f"type=bind,src={run / 'frozen_tests.py'},dst=/generated/frozen_tests.py,readonly"]
        cmd += [image, "python", "-c", DRIVER, mode]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            (run / f"grading-{mode}.stdout.txt").write_text(p.stdout)
            (run / f"grading-{mode}.stderr.txt").write_text(p.stderr)
            result = json.loads(p.stdout) if p.returncode == 0 else {"infrastructure_exit": p.returncode, "stderr": p.stderr}
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=15)
            result = {"timed_out": True}
        results[mode] = result
    report = {"task_id": summary["task_id"], "condition": summary["condition"],
              "implementation_run": str(run), "docker_image_id": image,
              "source_hashes_preserved": before == tree_hashes(workspace),
              "frozen_test_hash_preserved": None if frozen_hash is None else frozen_hash == sha256((run / "frozen_tests.py").read_bytes()).hexdigest(),
              "grader": "pinned DeepSWE test patch; original regression ignore list; ephemeral writable fixtures",
              "feedback_to_model": False, "results": results}
    (run / "independent-grading.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"condition": report["condition"], "source_hashes_preserved": report["source_hashes_preserved"],
                      "results": {k: {f: v.get(f) for f in ['pytest_exit_code', 'counts', 'timed_out', 'infrastructure_exit']} for k,v in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
