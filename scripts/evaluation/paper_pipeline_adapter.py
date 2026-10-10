"""Read pinned paper artifacts without running its artifact-writing entrypoints.

Paper tasks exported here are historical smoke fixtures, never a fresh holdout.
Oracle labels are diagnostics, not semantic correctness or trusted RL rewards.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import symtable
import types

PAPER_COMMIT = "380b7d362f49d43fd55af5b2f7e015d4fa651e97"
DEFAULT_PAPER = Path.home() / "Documents/GitHub/slm_test_generation"
DATASET = "TestEval/data/realworld-py-v2-tier-A.jsonl"
ORACLES = "step4_evaluation/oracle_analysis.py"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pinned(repo: Path, relative: str) -> bytes:
    # git show reads the recorded artifact, even if the working tree changes.
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{PAPER_COMMIT}:{relative}"])


def oracle_module(repo: Path):
    source = read_pinned(repo, ORACLES)
    name = "bender_paper_oracles_" + sha256(source)[:16]
    if name not in sys.modules:
        module = types.ModuleType(name)
        module.__file__ = f"{repo}@{PAPER_COMMIT}:{ORACLES}"
        sys.modules[name] = module
        try:
            exec(compile(source, module.__file__, "exec"), module.__dict__)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name], sha256(source)


def task_identity(row: dict) -> str:
    identity = {k: row.get(k) for k in ["repo", "commit_sha", "source_file", "func_name", "id"]}
    identity["source_sha256"] = sha256(row["focal_function"].encode())
    return "paper-smoke-" + sha256(json.dumps(identity, sort_keys=True).encode())


def inspect_rows(rows: list[dict]) -> dict:
    issues = []
    seen = {}
    for index, row in enumerate(rows):
        for field in ["id", "task_num"]:
            value = row.get(field)
            key = (field, str(value))
            if key in seen:
                issues.append({"row": index, "id": row.get("id"), "issue": f"duplicate_{field}", "previous_row": seen[key]})
            seen[key] = index
        revision = row.get("commit_sha", "")
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            issues.append({"row": index, "id": row.get("id"), "issue": "unresolved_source_revision"})
        if row.get("license") in [None, "", "varies", "unknown"]:
            issues.append({"row": index, "id": row.get("id"), "issue": "unresolved_license"})
        for field in ["focal_function", "python_solution_full"]:
            try:
                compile(row.get(field, ""), "<reference>", "exec")
            except (SyntaxError, ValueError, TypeError) as exc:
                issues.append({"row": index, "id": row.get("id"), "issue": f"invalid_{field}", "detail": str(exc)})
    return {"rows": len(rows), "issues": issues,
            "note": "Syntax checks do not establish importability, correctness, license clearance or freshness."}


def smoke_task(row: dict) -> dict | None:
    # Deliberately narrow: preserve top-level synchronous focal source verbatim.
    # Imports/defaults/decorators/methods need explicit module context later.
    if row.get("dependency_level") != "L0":
        return None
    source = row["focal_function"]
    tree = ast.parse(source)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return None
    function = tree.body[0]
    args = function.args
    if function.decorator_list or args.defaults or any(x is not None for x in args.kw_defaults):
        return None
    if function.returns or any(a.annotation for a in args.posonlyargs + args.args + args.kwonlyargs):
        return None
    if any(a.arg in {"self", "cls"} for a in args.posonlyargs + args.args):
        return None
    if any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(function)):
        return None
    # Do not trust the historical L0 label as proof of self-contained source.
    table = symtable.symtable(source, "<focal>", "exec")
    scopes = list(table.get_children())
    allowed_globals = set(dir(builtins)) | {function.name}
    while scopes:
        scope = scopes.pop()
        if any(s.is_global() and s.is_referenced() and s.get_name() not in allowed_globals
               for s in scope.get_symbols()):
            return None
        scopes.extend(scope.get_children())
    return {"id": task_identity(row), "role": "historical-development-smoke",
            "paper_task_id": row["id"], "paper_task_num": row["task_num"],
            "contract": row["docstring"], "function": function.name,
            "production_code": source, "production_sha256": sha256(source.encode()),
            "source": {k: row.get(k) for k in ["repo", "commit_sha", "source_file", "license", "commit_date"]},
            "temporal_status": "not-a-fresh-holdout", "runtime_preflight": "pending"}


def write_new(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-repo", type=Path, default=DEFAULT_PAPER)
    parser.add_argument("--output", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    export = sub.add_parser("export-smoke")
    export.add_argument("--count", type=int, default=10)
    classify = sub.add_parser("classify")
    classify.add_argument("tests", type=Path)
    classify.add_argument("--sut", action="append", required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.paper_repo.resolve()):
        parser.error("Write new artifacts outside the frozen paper repository")
    if args.command == "classify":
        module, code_hash = oracle_module(args.paper_repo)
        source = args.tests.read_text()
        sites = module.classify_oracles(source, sut_names=args.sut)
        result = {"paper_commit": PAPER_COMMIT, "classifier_sha256": code_hash,
                  "tests_sha256": sha256(source.encode()), "sut_names": args.sut,
                  "sites": [s.to_dict() for s in sites], "semantic_correctness": "not-established",
                  "runtime_reachability": "not-measured", "reward_eligible": False}
        write_new(args.output, json.dumps(result, indent=2) + "\n")
    else:
        data = read_pinned(args.paper_repo, DATASET)
        rows = [json.loads(line) for line in data.splitlines() if line.strip()]
        if args.command == "audit":
            result = inspect_rows(rows)
            result.update(paper_commit=PAPER_COMMIT, dataset_sha256=sha256(data))
            write_new(args.output, json.dumps(result, indent=2) + "\n")
            print(json.dumps({"rows": len(rows), "issues": len(result["issues"])}))
        else:
            if args.count < 1:
                parser.error("--count must be positive")
            tasks = [task for row in rows if (task := smoke_task(row)) is not None]
            tasks.sort(key=lambda task: task["id"])
            if len(tasks) < args.count:
                raise ValueError("Not enough eligible smoke tasks")
            write_new(args.output, "".join(json.dumps(t) + "\n" for t in tasks[:args.count]))
            print(json.dumps({"exported": args.count, "role": "historical-development-smoke"}))


if __name__ == "__main__":
    main()
