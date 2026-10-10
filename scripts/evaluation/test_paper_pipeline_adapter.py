"""Regression tests for integrity boundaries of the paper adapter."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("paper_adapter", Path(__file__).with_name("paper_pipeline_adapter.py"))
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def row(**changes):
    result = dict(id="old", task_num=1, repo="owner/repo", commit_sha="a" * 40,
                  source_file="a/utils.py", func_name="f", dependency_level="L0",
                  docstring="Return its input.", license="MIT", focal_function="def f(x):\n    return x\n",
                  python_solution_full="def f(x):\n    return x\n")
    result.update(changes)
    return result


def test_id_distinguishes_paths_revisions_and_content():
    original = row()
    variants = [original, row(source_file="b/utils.py"), row(commit_sha="b" * 40),
                row(focal_function="def f(x):\n    return x + 1\n")]
    assert len({adapter.task_identity(r) for r in variants}) == 4


def test_export_preserves_source_and_does_not_claim_freshness():
    original = row()
    result = adapter.smoke_task(original)
    assert result["production_code"] == original["focal_function"]
    assert result["runtime_preflight"] == "pending"
    assert result["temporal_status"] == "not-a-fresh-holdout"


@pytest.mark.parametrize("source", [
    "def f(self, x):\n    return x\n", "def f(x=missing):\n    return x\n",
    "@decorator\ndef f(x):\n    return x\n", "async def f(x):\n    return x\n",
    "def f(x: Missing):\n    return x\n",
    "def f(x):\n    return missing(x)\n",
    "def f(x):\n    return [missing(y) for y in x]\n",
    "def f(x):\n    import os\n    return os.getenv(x)\n",
])
def test_smoke_rejects_tasks_needing_context(source):
    assert adapter.smoke_task(row(focal_function=source)) is None


def test_audit_flags_ambiguous_ids_and_provenance():
    result = adapter.inspect_rows([row(), row(commit_sha="frozen-in-TestEval", license="varies")])
    issues = {r["issue"] for r in result["issues"]}
    assert {"duplicate_id", "duplicate_task_num", "unresolved_source_revision", "unresolved_license"} <= issues


def test_existing_artifact_is_never_overwritten(tmp_path):
    output = tmp_path / "review.json"
    output.write_text("human decision")
    with pytest.raises(FileExistsError):
        adapter.write_new(output, "replacement")
    assert output.read_text() == "human decision"
