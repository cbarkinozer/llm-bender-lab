"""Import the corrected typo-like precision tranche for human review."""
from __future__ import annotations

import json
from pathlib import Path

import argilla as rg


SOURCE = Path(__file__).parent / "data" / "precision-v2-candidates.jsonl"
API_URL = "http://127.0.0.1:6900"
API_KEY = "argilla.apikey"
WORKSPACE = "sft-review"
DATASET_NAME = "exp-005-targeted-precision-v2"


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 20 or len({row["id"] for row in rows}) != 20:
        raise ValueError("Expected exactly 20 unique precision-v2 records")
    if len({row["contrast"] for row in rows}) != 20:
        raise ValueError("Each precision-v2 record must test a distinct contrast")

    client = rg.Argilla(api_url=API_URL, api_key=API_KEY)
    if client.datasets(name=DATASET_NAME, workspace=WORKSPACE) is not None:
        raise RuntimeError(f"{DATASET_NAME} already exists; refusing to replace review state")
    settings = rg.Settings(
        guidelines=(
            "Her örnek yazım hatası sanılabilecek veya biçimce yakın iki terimi ayırt etmelidir. "
            "Bağlam doğru terimi belirlemeye yetmeli; hedef tam istenen terimi korumalıdır. "
            "İyi hedefi kabul et, gerekiyorsa doğrudan düzelt; genel sayı/birim hassasiyeti örneğine dönüştürme."
        ),
        fields=[
            rg.TextField(name="contrast", title="Test edilen ayrım", use_markdown=False),
            rg.TextField(name="user_input", title="Kullanıcı girdisi", use_markdown=False),
            rg.TextField(name="candidate_target", title="Aday hedef", use_markdown=False),
        ],
        questions=[
            rg.TextQuestion(name="reviewed_target", title="İncelenmiş hedef", required=True, use_markdown=False),
            rg.TextQuestion(name="review_note", title="İsteğe bağlı not", required=False, use_markdown=False),
        ],
    )
    dataset = rg.Dataset(name=DATASET_NAME, workspace=WORKSPACE, settings=settings, client=client)
    dataset.create()
    records = [
        rg.Record(
            id=row["id"],
            fields={
                "contrast": row["contrast"],
                "user_input": row["user_input"],
                "candidate_target": row["assistant_target"],
            },
            suggestions=[
                rg.Suggestion(
                    question_name="reviewed_target",
                    value=row["assistant_target"],
                    agent="precision-v2-candidate",
                )
            ],
        )
        for row in rows
    ]
    dataset.records.log(records, batch_size=20)
    print(f"{DATASET_NAME}: {len(records)} pending records")
    print(f"{API_URL}/dataset/{dataset.id}/annotation-mode?page=1&status=pending")


if __name__ == "__main__":
    main()
