"""Finalize exp-001 after the second saturation-review sample.

The reviewer inspected another 30 records and concluded that the remaining
examples were repetitive without a meaningful quality difference.  This
creates a complete, derived reviewed layer; immutable source pools remain
unchanged.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "reviewed-v2"
OUT = ROOT / "reviewed-v3"
INPUT = V2 / "pending-after-v2.csv"
V2_ACCEPTED = V2 / "accepted-reviewed.csv"
DATASET_ID = "bcedb991-50c4-4bc2-9467-611bf991bfc1"
REVIEWER_ID = "a3cedf29-50c3-4f85-b552-6317636192a5"
API_URL = os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900").rstrip("/")
API_KEY = os.getenv("ARGILLA_API_KEY", "argilla.apikey")

# These are the only two non-open-ended discarded records. They are literal
# applications of the reviewer's corrections.
EXPLICIT_REPAIRS = {
    "bare_qa_span__006": {
        "user": "Kaynak: Alanındaki çalışmalarıyla tanınan Cem Öztürk, kırtasiye açmıştır.\n\nSoru: Kırtasiyeyi kim açmıştır?\n\nCevap:",
    },
    "bare_qa_span__138": {
        "user": "Kaynak: Tarih kayıtlarına göre ilk taşınabilir cep telefonu 1983 senesinde geliştirilmiştir.\n\nSoru: İlk taşınabilir cep telefonu hangi yıl geliştirildi?\n\nCevap:",
    },
    "bare_gec__226": {
        "assistant": "Toplantıdan sonra ev sahibi bozulan musluğu öğleden önce tamir ettirdi; günün son işlemi olarak sonuç ilgililere bildirildi.",
    },
}

# The reviewer flagged this source template itself; it is repaired by the
# general location-template pass below, so its candidate target remains valid.
GENERIC_TEMPLATE_REPAIR_IDS = {"bare_qa_span__366"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_reviews() -> dict[str, dict]:
    endpoint = f"{API_URL}/api/v1/datasets/{DATASET_ID}/records/search"
    headers = {"X-Argilla-Api-Key": API_KEY}
    reviews: dict[str, dict] = {}
    offset = 0
    while True:
        response = requests.post(endpoint, headers=headers, params={"offset": offset, "limit": 1000, "include": "responses"}, json={}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        for item in payload["items"]:
            record = item["record"]
            saved = [response for response in record["responses"] if response["user_id"] == REVIEWER_ID and response["status"] in {"submitted", "discarded"}]
            if len(saved) > 1:
                raise ValueError(f"Multiple saved responses for {record['external_id']}")
            if saved:
                reviews[record["external_id"]] = {"response": saved[0], "category": record["metadata"]["category"]}
        offset += len(payload["items"])
        if offset >= payload["total"]:
            break
    if len(reviews) < 30:
        raise ValueError(f"Expected at least 30 saved reviews, found {len(reviews)}")
    return reviews


def response_value(response: dict, key: str) -> str:
    return response.get("values", {}).get(key, {}).get("value", "")


def set_messages(row: dict[str, str], user: str | None, assistant: str | None, note: str) -> None:
    messages = json.loads(row["messages"])
    if user is not None:
        messages[0]["content"] = user
    if assistant is not None:
        messages[1]["content"] = assistant
    row["messages"] = json.dumps(messages, ensure_ascii=False)
    row["quality_status"] = "accepted"
    row["reviewer"] = "cbark"
    row["notes"] = (row.get("notes", "") + f" | {note}").strip(" |")


def repair_qa_year_sentences(row: dict[str, str]) -> Counter[str]:
    """Repair the two malformed temporal-source templates across bare QA.

    Both templates put a verbal noun before a comma (for example, ``üretildiği,
    1983 senesinde meydana gelmiştir``).  The replacement makes ``yıl`` the
    subject and leaves the literal answer span unchanged.  Using ``olarak
    belirtilmiştir`` avoids incorrect number-suffix harmony such as ``1983'dir``.
    """
    if row["category"] != "bare_qa_span":
        return Counter()
    messages = json.loads(row["messages"])
    user = messages[0]["content"]
    counts: Counter[str] = Counter()
    source_patterns = (
        (
            "historical_records_made_occur",
            re.compile(r"Kaynak: Tarih kayıtlarına göre (.+?), (\d{4}) senesinde meydana gelmiştir\."),
        ),
        (
            "records_year_copula",
            re.compile(r"Kaynak: Kayıtlara göre (.+?) yıl (\d{4})'dir\."),
        ),
    )
    for label, pattern in source_patterns:
        user, changed = pattern.subn(
            r"Kaynak: Tarih kayıtlarına göre \1 yıl \2 olarak belirtilmiştir.", user
        )
        if changed:
            counts[label] += changed
    # ASCII-I at the beginning of several generated questions is a genuine
    # Turkish orthography error, not a stylistic preference.
    for old, new in (("Soru: Ilk ", "Soru: İlk "), ("Soru: Iki ", "Soru: İki "), ("Soru: Insülin", "Soru: İnsülin")):
        if old in user:
            user = user.replace(old, new)
            counts["question_initial_i"] += 1
    if counts:
        messages[0]["content"] = user
        row["messages"] = json.dumps(messages, ensure_ascii=False)
        row["notes"] = (row.get("notes", "") + " | final temporal-QA template repair").strip(" |")
    return counts


def repair_remaining_qa_source_templates(row: dict[str, str]) -> Counter[str]:
    """Remove other mechanically generated, ungrammatical QA source forms."""
    if row["category"] != "bare_qa_span":
        return Counter()
    messages = json.loads(row["messages"])
    user = messages[0]["content"]
    counts: Counter[str] = Counter()

    # "X olduğu, 2012 yılında gerçekleşmiştir" leaves a dangling verbal noun.
    user, changed = re.subn(
        r"Kaynak: (.+?), (\d{4}) yılında gerçekleşmiştir\.",
        r"Kaynak: \1 yıl \2 olarak belirtilmiştir.",
        user,
    )
    counts["year_happened_variant"] += changed

    # A location is a direct fact, not something that must be inferred from
    # research.  ``yer alır`` works across buildings, offices, sites, and
    # historical places without changing the literal location span.
    user, changed = re.subn(
        r"Kaynak: Yapılan araştırmalara göre (.+?), (.+?) konumlandırılmıştır\.",
        r"Kaynak: \1, \2 yer alır.",
        user,
    )
    counts["location_research_template"] += changed

    # "X, uzmanlara göre Y'dir olarak tanımlanmaktadır" has two competing
    # predicates.  Keep the fact and remove the fabricated attribution frame.
    user, changed = re.subn(
        r"Kaynak: (.+?), uzmanlara göre (.+?) olarak (?:tanımlanmaktadır|öne çıkmaktadır|açıklanmaktadır)\.",
        r"Kaynak: \1 \2.",
        user,
    )
    counts["expert_as_defined_template"] += changed

    # Repair genuine ASCII-I orthography defects in both source and question.
    for old, new in (("Kaynak: Ilk ", "Kaynak: İlk "), ("Kaynak: Insan", "Kaynak: İnsan"), ("Soru: Ilk ", "Soru: İlk "), ("Soru: Iki ", "Soru: İki "), ("Soru: Insan", "Soru: İnsan"), ("Soru: Insülin", "Soru: İnsülin")):
        if old in user:
            user = user.replace(old, new)
            counts["ascii_i_orthography"] += 1
    if counts:
        messages[0]["content"] = user
        row["messages"] = json.dumps(messages, ensure_ascii=False)
        row["notes"] = (row.get("notes", "") + " | final QA source-template repair").strip(" |")
    return counts


def main() -> None:
    pending, fieldnames = load_csv(INPUT)
    accepted, accepted_fields = load_csv(V2_ACCEPTED)
    if fieldnames != accepted_fields or len(pending) != 2370 or len(accepted) != 77:
        raise ValueError("Unexpected reviewed-v2 inventory or schema")
    reviews = fetch_reviews()
    by_id = {row["id"]: row for row in pending}
    if set(reviews) - set(by_id):
        raise ValueError("Review references an unknown pending record")

    status_counts = Counter()
    qa_year_repair_counts = Counter()
    accepted_now: list[dict[str, str]] = []
    for row in pending:
        result = dict(row)
        qa_year_repair_counts.update(repair_qa_year_sentences(result))
        review = reviews.get(row["id"])
        if review is None:
            # Explicit reviewer decision: the remaining repetitive pool is
            # accepted without altering candidate text.
            set_messages(result, None, None, "accepted after review-saturation decision")
            status_counts["accepted_by_saturation"] += 1
        else:
            response, category = review["response"], review["category"]
            if response["status"] == "submitted":
                original = json.loads(result["messages"])
                set_messages(
                    result,
                    response_value(response, "reviewed_user_input") or original[0]["content"],
                    response_value(response, "reviewed_target") or original[1]["content"],
                    "Argilla v3 submitted review",
                )
                status_counts["submitted_review"] += 1
            elif category == "open_ended_counterexample":
                # The reviewer decided the alternative wording was an optional
                # improvement, not a defect; retain the original target.
                set_messages(result, None, None, "accepted unchanged; optional improvement note retained in Argilla snapshot")
                status_counts["open_ended_optional_improvement"] += 1
            elif category == "terse_summary":
                # The reviewer concluded this category has no correctness
                # defects; alternative wording is not a reason to alter it.
                set_messages(result, None, None, "accepted unchanged; summary alternative retained in Argilla snapshot")
                status_counts["summary_optional_improvement"] += 1
            elif row["id"] in GENERIC_TEMPLATE_REPAIR_IDS:
                set_messages(result, None, None, "accepted; source repaired by final QA template pass")
                status_counts["generic_template_repair"] += 1
            elif row["id"] in EXPLICIT_REPAIRS:
                repair = EXPLICIT_REPAIRS[row["id"]]
                set_messages(result, repair.get("user"), repair.get("assistant"), "Argilla v3 explicit review repair")
                status_counts["explicit_review_repair"] += 1
            else:
                raise ValueError(f"Unhandled discarded review: {row['id']} ({category})")
        accepted_now.append(result)

    all_accepted = accepted + accepted_now
    qa_source_repair_counts = Counter()
    for row in all_accepted:
        qa_source_repair_counts.update(repair_remaining_qa_source_templates(row))
    if len(all_accepted) != 2447 or len({row["id"] for row in all_accepted}) != 2447:
        raise ValueError("Final reviewed set must contain every candidate exactly once")
    if {row["quality_status"] for row in all_accepted} != {"accepted"}:
        raise ValueError("Every final row must be accepted")

    # The final training artifact must itself be exact-deduplicated, rather
    # than relying on the trainer to filter a historical reviewed layer.
    unique_pairs: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    removed_duplicate_ids: list[str] = []
    for row in all_accepted:
        messages = json.loads(row["messages"])
        pair = tuple(" ".join(messages[index]["content"].casefold().split()) for index in (0, 1))
        if pair in unique_pairs:
            removed_duplicate_ids.append(row["id"])
            continue
        unique_pairs.add(pair)
        deduplicated.append(row)
    expected_removed = ["bare_gec__254", "bare_gec__261", "bare_gec__278", "bare_gec__285", "bare_gec__292"]
    if removed_duplicate_ids != expected_removed or len(deduplicated) != 2442:
        raise ValueError(f"Unexpected final exact-duplicate set: {removed_duplicate_ids}")
    all_accepted = deduplicated

    OUT.mkdir(exist_ok=True)
    output = OUT / "accepted-reviewed.csv"
    write_csv(output, all_accepted, fieldnames)
    snapshot = {
        "version": "argilla-v3-finalization",
        "dataset_id": DATASET_ID,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_id": REVIEWER_ID,
        "review_count": len(reviews),
        "responses": reviews,
        "reviewer_decision": "Apply real corrections from the 30-record sample; accept remaining repetitive examples as reviewed.",
    }
    snapshot_path = OUT / "argilla-v3-decisions.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "version": "reviewed-v3-final-deduplicated",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_candidate_count": 2447,
        "accepted_count": len(all_accepted),
        "pending_count": 0,
        "v3_hand_review_count": len(reviews),
        "finalization_counts": dict(status_counts),
        "temporal_qa_template_repairs": dict(qa_year_repair_counts),
        "additional_qa_source_template_repairs": dict(qa_source_repair_counts),
        "explicit_review_repair_ids": sorted(EXPLICIT_REPAIRS),
        "input_sha256": {INPUT.name: sha256(INPUT), V2_ACCEPTED.name: sha256(V2_ACCEPTED)},
        "decision_snapshot_sha256": sha256(snapshot_path),
        "deduplication_repair": {
            "reason": "Removed exact duplicate user/assistant GEC pairs from the final training artifact.",
            "removed_ids": removed_duplicate_ids,
            "removed_count": len(removed_duplicate_ids),
        },
        "output_sha256": sha256(output),
        "category_counts": Counter(row["category"] for row in all_accepted),
        "quality_status": "accepted for every row",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
