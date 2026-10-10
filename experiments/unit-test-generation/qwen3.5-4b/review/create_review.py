"""Create a development-only Argilla review schema; never replace old reviews."""
from pathlib import Path
import json
import argilla as rg

SMELLS = ["Assertion Roulette", "Eager Test", "Mystery Guest", "Magic Number Test",
          "Obscure Test", "Lack of Cohesion", "Conditional Test Logic",
          "External Dependency", "Unverified Action", "Trivial Assertion", "Duplicated Setup"]


def main():
    env = dict(line.split("=", 1) for line in Path(__file__).with_name(".env").read_text().splitlines()
               if line and not line.startswith("#"))
    client = rg.Argilla(api_url="http://127.0.0.1:7900", api_key=env["ARGILLA_API_KEY"])
    workspace = env["ARGILLA_WORKSPACE"]
    name = "unit-test-quality-development-v01"
    existing = client.datasets(name=name, workspace=workspace)
    if existing is not None:
        print(json.dumps({"status": "existing-preserved", "dataset_id": str(existing.id)}))
        return
    questions = [rg.LabelQuestion(name=d, title=d.replace("_", " ").title(),
                                 labels=["1", "2", "3", "4", "5", "not-rateable"], required=True)
                 for d in ["robustness", "assertion_strength", "readability", "conciseness"]]
    questions += [
        rg.LabelQuestion(name="semantic_correctness", title="Are the expectations justified by the contract?",
                         labels=["correct", "incorrect", "mixed", "uncertain", "not-rateable"], required=True),
        rg.LabelQuestion(name="usefulness", title="Would you retain this suite?",
                         labels=["retain", "repair", "reject", "uncertain"], required=True),
        rg.MultiLabelQuestion(name="oracle_classes", title="Observed oracle classes",
                              labels=["TRIVIAL", "WEAK", "STRONG", "UNKNOWN", "NO_ORACLE"], required=False),
        rg.MultiLabelQuestion(name="smells", title="Contextually confirmed smells", labels=SMELLS, required=False),
        rg.LabelQuestion(name="confidence", title="Review confidence", labels=["low", "medium", "high"], required=True),
        rg.TextQuestion(name="evidence", title="Affected oracle/test locations and reasoning", required=False),
    ]
    rubric = Path(__file__).parents[1] / "quality-rubric-v0.1.md"
    settings = rg.Settings(guidelines=rubric.read_text(), fields=[
        rg.TextField(name="contract", title="Task contract", use_markdown=True),
        rg.TextField(name="source", title="Approved source context", use_markdown=True),
        rg.TextField(name="generated_tests", title="Original generated tests", use_markdown=True),
        rg.TextField(name="execution_evidence", title="Execution and runtime oracle evidence", use_markdown=True),
    ], questions=questions)
    dataset = rg.Dataset(name=name, workspace=workspace, settings=settings, client=client)
    dataset.create()
    print(json.dumps({"status": "created-empty", "dataset_id": str(dataset.id),
                      "url": f"http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode"}))


if __name__ == "__main__":
    main()
