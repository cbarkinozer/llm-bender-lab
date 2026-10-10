"""Import original smoke reference functions in a bounded, networkless container."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

IMAGE = "sha256:9e8975db7a63f480425b84d2a89f4395c4550172470f92ea968dec2ae244625a"
PROBE = '''
import contextlib, importlib.util, io, json
from pathlib import Path
rows = []
for task in json.loads(Path('/workspace/manifest.json').read_text()):
    stream = io.StringIO()
    result = {'id': task['id'], 'function': task['function']}
    try:
        spec = importlib.util.spec_from_file_location('reference', '/workspace/' + task['filename'])
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            spec.loader.exec_module(module)
        result['importable'] = callable(getattr(module, task['function'], None))
    except BaseException as exc:
        result.update(importable=False, error_type=type(exc).__name__, error=str(exc))
    result['import_output'] = stream.getvalue()
    rows.append(result)
print(json.dumps(rows))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; refusing to overwrite")
    rows = [json.loads(line) for line in args.tasks.read_text().splitlines() if line.strip()]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError("Tasks must be nonempty and uniquely identified")
    with tempfile.TemporaryDirectory(prefix="bender-preflight-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        manifest = []
        for index, row in enumerate(rows):
            source = row['production_code'].encode()
            if hashlib.sha256(source).hexdigest() != row['production_sha256']:
                raise ValueError(f"Source hash mismatch: {row['id']}")
            filename = f"reference_{index}.py"
            (root / filename).write_bytes(source)
            manifest.append(dict(id=row['id'], function=row['function'], filename=filename))
        (root / 'manifest.json').write_text(json.dumps(manifest))
        name = "bender-preflight-" + uuid.uuid4().hex
        command = ["docker", "run", "--rm", "--name", name, "--network", "none", "--read-only",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
                   "--memory", "512m", "--cpus", "1", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                   "--mount", f"type=bind,src={root},dst=/workspace,readonly", IMAGE, "python", "-c", PROBE]
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
            results = json.loads(process.stdout)
        finally:
            # A host timeout must not leave its container/descendants running.
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=15)
        for row in rows:
            index = next(i for i, x in enumerate(manifest) if x['id'] == row['id'])
            if hashlib.sha256((root / f'reference_{index}.py').read_bytes()).hexdigest() != row['production_sha256']:
                raise RuntimeError("Reference code changed during preflight")
    result = {"image": IMAGE, "tasks_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
              "rows": results, "importable": sum(r['importable'] for r in results),
              "total": len(rows), "semantic_correctness": "not-established",
              "note": "Imports do not verify the behavioral contract. No source/interface repair applied."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ['importable', 'total', 'semantic_correctness']}))
    if result['importable'] != result['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
