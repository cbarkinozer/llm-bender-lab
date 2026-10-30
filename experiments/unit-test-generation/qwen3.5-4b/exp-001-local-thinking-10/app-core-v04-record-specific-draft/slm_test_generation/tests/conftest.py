"""Only these authored fixtures may run outside the isolated executor."""
from functools import partial
import pytest


@pytest.fixture
def local_runner():
    from benchmark_workflow import LocalPytestExecutor, run_task
    return partial(run_task, executor=LocalPytestExecutor())
