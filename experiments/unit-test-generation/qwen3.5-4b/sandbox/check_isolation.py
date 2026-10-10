"""Verify container boundaries using trusted fixtures, not model-generated code."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

IMAGE = "llm-bender-pytest:integration-v01"
CHECK = '''
import json, os, socket
results = {}
for label, path in [('production_readonly', '/workspace/source.py'), ('rootfs_readonly', '/etc/probe')]:
    try:
        with open(path, 'w') as f: f.write('changed')
        results[label] = False
    except OSError:
        results[label] = True
sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect(('1.1.1.1', 443))
    results['network_disabled'] = False
except OSError:
    results['network_disabled'] = True
finally:
    sock.close()
results['nonroot'] = os.getuid() != 0
results['no_home_mount'] = not os.path.exists('/Users')
print(json.dumps(results))
raise SystemExit(0 if all(results.values()) else 1)
'''


def main():
    with tempfile.TemporaryDirectory(prefix="bender-isolation-") as directory:
        source = Path(directory) / "source.py"
        source.write_text("def multiply(a, b):\n    return a * b\n")
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        command = ["docker", "run", "--rm", "--network", "none", "--read-only",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                   "--pids-limit", "64", "--memory", "512m", "--cpus", "1",
                   "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                   "--mount", f"type=bind,src={directory},dst=/workspace,readonly",
                   IMAGE, "python", "-c", CHECK]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        checks = json.loads(result.stdout)
        checks["host_source_hash_preserved"] = hashlib.sha256(source.read_bytes()).hexdigest() == before
        if not all(checks.values()):
            raise RuntimeError(checks)
        print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
