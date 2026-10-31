import os
import subprocess
import sys
import pytest

@pytest.fixture
def local_executor():
    # Trusted authored microfixtures only. Generated suites use the Docker default.
    def execute(run_directory, timeout_seconds):
        env=dict(os.environ, SUITE_TIMEOUT=str(timeout_seconds),
                 ORACLE_EXECUTION_FILE=str(run_directory/'events.jsonl'),
                 PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
        env.pop('PYTEST_ADDOPTS',None)
        subprocess.run([sys.executable,'supervisor.py'], cwd=run_directory, env=env,
                       check=True, capture_output=True, text=True, timeout=timeout_seconds+10)
    return execute
