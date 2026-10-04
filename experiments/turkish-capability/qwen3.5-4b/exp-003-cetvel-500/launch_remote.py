"""Detach a setup-waiting coordinator without SSH holding inherited log pipes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/workspace/repos/llm-bender-lab')
HERE = ROOT / 'experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500'
SUPPORT = Path('/workspace/cetvel-500-support')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    SUPPORT.mkdir(exist_ok=True)
    if not args.worker:
        assert not (SUPPORT / 'launch.json').exists(), 'Do not launch twice'
        command = [sys.executable, str(Path(__file__).resolve()), '--worker']
        with (SUPPORT / 'coordinator.log').open('x') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        info = dict(pid=process.pid, command=command, launched_at_unix=time.time())
        (SUPPORT / 'launch.json').write_text(json.dumps(info, indent=2) + '\n')
        print(json.dumps(info))
        return
    deadline = time.monotonic() + 1200
    while not (SUPPORT / 'setup-completed').exists():
        assert time.monotonic() < deadline, 'Setup did not complete within20minutes; inspect setup logs'
        time.sleep(5)
    env = os.environ.copy()
    env['HF_HOME'] = '/workspace/.cache/huggingface'
    env['LD_LIBRARY_PATH'] = '/workspace/.venvs/cetvel-vllm/lib/python3.12/site-packages/nvidia/cu13/lib:' + env.get('LD_LIBRARY_PATH', '')
    result = subprocess.run(['/workspace/.venvs/cetvel-vllm/bin/python', str(HERE / 'run_gpu.py'),
        '--adapter', '/workspace/F-adapter'], cwd=ROOT, env=env)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
