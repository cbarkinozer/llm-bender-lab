"""Import the generated 60-record policy extension into three review datasets."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import argilla as rg

SOURCE = Path(__file__).parent / "results" / "targeted-generated" / "sft_all_60.jsonl"
API_URL = "http://127.0.0.1:6900"
API_KEY = "argilla.apikey"
WORKSPACE = "sft-review"
GROUPS = {
    "clarification_missing_context": ("exp-005-targeted-clarification", "Ask exactly one minimum clarification question; never guess missing context."),
    "lexical_entity_precision": ("exp-005-targeted-precision", "Preserve the exact requested word, entity, number, unit, and qualification."),
    "natural_non_anthropomorphic": ("exp-005-targeted-non-anthropomorphic", "Do not claim feelings, preferences, consciousness, or human experience."),
}

def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {"id", "category", "user_input", "assistant_target"}
    if any(set(row) != required for row in rows):
        raise ValueError("Every row must contain exactly id, category, user_input, assistant_target")
    counts = Counter(row["category"] for row in rows)
    if counts != Counter({key: 20 for key in GROUPS}):
        raise ValueError(f"Expected 20 records per category, got {counts}")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate IDs")
    client = rg.Argilla(api_url=API_URL, api_key=API_KEY)
    created = []
    for category, (name, rule) in GROUPS.items():
        old = client.datasets(name=name, workspace=WORKSPACE)
        if old is not None:
            old.delete()
        settings = rg.Settings(
            guidelines=(f"{rule} Review every candidate. Keep a good target unchanged; otherwise rewrite it directly. "
                        "Use the informal sen register, natural Turkish, no filler, and leave a short note only when useful."),
            fields=[
                rg.TextField(name="user_input", title="User input", use_markdown=False),
                rg.TextField(name="candidate_target", title="Current candidate target", use_markdown=False),
            ],
            questions=[
                rg.TextQuestion(name="reviewed_target", title="Reviewed target", description="Keep unchanged or edit directly.", required=True, use_markdown=False),
                rg.TextQuestion(name="review_note", title="Optional review note", required=False, use_markdown=False),
            ],
        )
        dataset = rg.Dataset(name=name, workspace=WORKSPACE, settings=settings, client=client)
        dataset.create()
        records = [
            rg.Record(id=row["id"], fields={"user_input": row["user_input"], "candidate_target": row["assistant_target"]})
            for row in rows if row["category"] == category
        ]
        dataset.records.log(records, batch_size=20)
        created.append({"name": name, "id": str(dataset.id), "records": len(records), "url": f"{API_URL}/dataset/{dataset.id}/annotation-mode?page=1&status=pending"})
    print(json.dumps(created, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
