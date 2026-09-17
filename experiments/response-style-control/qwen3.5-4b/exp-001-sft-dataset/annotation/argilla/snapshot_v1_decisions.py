"""Snapshot the completed 47-row Argilla v1 review into versioned JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import argilla as rg


OUT = Path(__file__).resolve().parents[2] / "reviewed-v1" / "argilla-v1-decisions.json"


def main() -> None:
    client = rg.Argilla(api_url="http://127.0.0.1:6900", api_key="argilla.apikey")
    dataset = client.datasets(name="exp-001-response-style-candidates", workspace="sft-review")
    if dataset is None:
        raise RuntimeError("The original Argilla v1 dataset is unavailable")
    submitted, discarded, notes = [], [], {}
    for record in dataset.records(with_responses=True):
        responses = record.responses["reviewed_target"]
        if len(responses) != 1:
            continue
        status = str(responses[0].status)
        if status == "ResponseStatus.submitted":
            submitted.append(record.id)
        elif status == "ResponseStatus.discarded":
            discarded.append(record.id)
            notes[record.id] = [str(item.value) for item in record.responses["review_note"] if str(item.status) == status]
        else:
            raise RuntimeError(f"Unexpected review status for {record.id}: {status}")
    snapshot = {
        "source": "Argilla v1 exp-001-response-style-candidates",
        "snapshotted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_ids": sorted(submitted),
        "discarded_ids": sorted(discarded),
        "discarded_feedback": notes,
    }
    if len(submitted) != 28 or len(discarded) != 19:
        raise RuntimeError(f"Expected 28 submitted and 19 discarded rows; got {len(submitted)} and {len(discarded)}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(submitted)} submitted and {len(discarded)} discarded decisions")


if __name__ == "__main__":
    main()
