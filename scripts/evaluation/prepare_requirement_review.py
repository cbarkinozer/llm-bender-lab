"""Append an unchanged generated suite to a separate initial Argilla review set.

No model identity, execution outcome, automatic labels or private grader is shown.
Existing records and responses are never updated.
"""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path

import argilla as rg

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT / "experiments/unit-test-generation/qwen3.5-4b"
SMELLS = ["Assertion Roulette", "Eager Test", "Mystery Guest", "Magic Number Test",
          "Obscure Test", "Lack of Cohesion", "Conditional Test Logic", "External Dependency",
          "Unverified Action", "Trivial Assertion", "Duplicated Setup"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--context-file", type=Path, required=True)
    parser.add_argument("--review-spec", type=Path, required=True)
    args = parser.parse_args()
    run = args.run_directory.resolve()
    summary = json.loads((run / "summary.json").read_text())
    tests = (run / "generated_tests.py").read_text()
    context = args.context_file.read_text()
    if sha256(context.encode()).hexdigest() != summary["approved_context_sha256"]:
        raise ValueError("Review context differs from model context")
    requirement = (run.parent / "requirement.md").read_text()
    study_id = sha256((summary["task_id"] + summary["prompt_sha256"] + tests).encode()).hexdigest()[:24]
    spec = json.loads(args.review_spec.read_text())
    if spec["task_id"] != summary["task_id"]:
        raise ValueError("Review specification task mismatch")
    effective = (run / "effective-prompt.md").read_text()
    if sha256(effective.encode()).hexdigest() != summary["prompt_sha256"]:
        raise ValueError("Original generation prompt hash mismatch")
    names = [n.name for n in ast.parse(tests).body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")]
    instructions = effective.split("Repository:", 1)[0].strip()
    fields = {
        "environment": "**Language: Python. Framework: pytest.**\n\n"
            "One generation per task; zero repair attempts; no model tools. "
            "Pass@1 is evaluated on the original output. Human repairs are separate artifacts.",
        "instructions": "System instruction:\n\n" + summary["system_prompt"] +
            "\n\nTask instructions (verbatim):\n\n" + instructions,
        "contract": requirement,
        "clauses": "\n".join(f"- **{c['id']}**: {c['text']}" for c in spec["clauses"]),
        "ambiguities": "\n".join("- " + a for a in spec["known_ambiguities"]),
        "context": spec["api_facts"],
        "original_context": context,
        "test_index": "\n".join("- `" + n + "`" for n in names),
        "tests": "```python\n" + tests + "\n```",
    }
    (run / "review-v03-packet.json").write_text(json.dumps({"id": study_id, "fields": fields}, indent=2)+"\n")
    env = dict(line.split("=", 1) for line in (DOMAIN / "review/.env").read_text().splitlines()
               if line and not line.startswith("#"))
    client = rg.Argilla(api_url="http://127.0.0.1:7900", api_key=env["ARGILLA_API_KEY"])
    name = "requirements-stage-a-v01-review-v03"
    dataset = client.datasets(name=name, workspace=env["ARGILLA_WORKSPACE"])
    if dataset is None:
        questions = [rg.LabelQuestion(name=d, title=d.replace("_", " ").title(),
                                     labels=["1", "2", "3", "4", "5", "not-rateable"], required=True)
                     for d in ["robustness", "assertion_strength", "readability", "conciseness"]]
        questions += [
            rg.LabelQuestion(name="semantic_correctness", title="Are the expectations justified by the requirement?",
                             labels=["correct", "incorrect", "mixed", "uncertain", "not-rateable"], required=True),
            rg.LabelQuestion(name="usefulness", title="Would you retain this suite?",
                             labels=["retain", "repair", "reject", "uncertain"], required=True),
            rg.MultiLabelQuestion(name="oracle_classes", title="Observed oracle classes",
                                  labels=["TRIVIAL", "WEAK", "STRONG", "UNKNOWN", "NO_ORACLE"], required=False),
            rg.MultiLabelQuestion(name="smells", title="Contextually confirmed smells", labels=SMELLS, required=False),
            rg.TextQuestion(name="per_test", title="Per-test review: use the row template in guidelines", required=False),
            rg.TextQuestion(name="clause_coverage", title="For each R ID: covered / partial / missing / tested-wrongly / uncertain; cite tests", required=False),
            rg.TextQuestion(name="repair_notes", title="Proposed repairs (original output remains unchanged)", required=False),
            rg.TextQuestion(name="importance", title="Which important behaviors are protected or missing?", required=False),
            rg.TextQuestion(name="evidence", title="Test locations and reasons for your ratings", required=False),
            rg.LabelQuestion(name="confidence", title="Review confidence", labels=["low", "medium", "high"], required=True),
        ]
        settings = rg.Settings(
            guidelines=("Review v0.3: execution results and automated judgments are withheld. "
                        "Judge expectations against the English requirement and approved existing API context. "
                        "Unspecified behavior is uncertain rather than automatically wrong. Preserve your initial "
                        "rating before any later evidence-assisted review.\n\n" + (DOMAIN / "review-guidelines-v0.3.md").read_text() + "\n\n" + (DOMAIN / "quality-rubric-v0.1.md").read_text()),
            fields=[rg.TextField(name=k, title=title, use_markdown=True) for k, title in [
                ("environment", "Language and testing approach"),
                ("instructions", "Original generation instructions"),
                ("contract", "English requirement — unchanged"),
                ("clauses", "Requirement clauses — reviewer aid"),
                ("ambiguities", "Known specification ambiguities"),
                ("context", "Verified existing API facts"),
                ("original_context", "Original model context — verbatim audit copy"),
                ("test_index", "Test names for annotation"),
                ("tests", "Original generated tests")]],
            questions=questions)
        dataset = rg.Dataset(name=name, workspace=env["ARGILLA_WORKSPACE"], settings=settings, client=client)
        dataset.create()
    exists = any(str(r.id) == study_id for r in dataset.records(with_responses=False, with_suggestions=False))
    if not exists:
        dataset.records.log([rg.Record(id=study_id, fields=fields)])
    receipt = {"status": "existing-preserved" if exists else "appended-original",
               "dataset": name, "study_id": study_id, "dataset_id": str(dataset.id),
               "url": f"http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode",
               "execution_or_model_identity_shown": False, "human_ratings_submitted": False, "schema_version": "0.3",
               "review_mode": spec["review_mode"], "prior_feedback_exposure": spec["prior_feedback_exposure"]}
    (run / "review-v03-receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
