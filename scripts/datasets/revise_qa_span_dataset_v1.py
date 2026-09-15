#!/usr/bin/env python3
"""Create the reviewed-pending v1 of the short Turkish QA SFT candidate.

The source CSV remains immutable.  This revision deliberately makes two
content changes requested by the dataset owner:

1. Prefix every question with an explicit source-grounding cue so fabricated
   passages are not presented as world-knowledge questions.
2. Change 19 internally consistent ``Hayır`` items into ``Evet`` items by
   updating the passage as well as retaining the matching question.  Labels
   are never flipped on their own.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SOURCE = Path(r"C:\Users\cbark\Downloads\qa_span_dataset.csv")
OUTPUT = Path(r"C:\Users\cbark\Downloads\qa_span_dataset_v1.csv")
AUDIT = Path(r"C:\Users\cbark\Downloads\qa_span_dataset_v1_audit.json")
SOURCE_SHA256 = "0af7e0ea5914dc5feaba45658168fd47ce97f0502fdd1556d86bb9af6c45cf5b"
GROUNDING_PREFIX = "Aşağıdaki metne göre, "

# These revisions preserve the original question and turn its proposition into
# the passage's stated fact.  They are intentionally limited to non-harmful,
# synthetic everyday/technology/business examples.
YES_REBALANCE_SOURCES = {
    "bare_qa_span__465": "Apartmanda evcil hayvan beslemek serbesttir.",
    "bare_qa_span__466": "Site havuzu kış aylarında da açıktır.",
    "bare_qa_span__468": "Mahalle pazarı resmi tatillerde de kurulmaktadır.",
    "bare_qa_span__469": "Site içindeki spor salonu üyeler için ücretlidir.",
    "bare_qa_span__470": "Mahalle etkinlikleri belediye tarafından ücretli düzenlenmektedir.",
    "bare_qa_span__471": "Nöbetçi eczaneler yalnızca gündüz hizmet vermektedir.",
    "bare_qa_span__472": "Şehirdeki toplu taşıma sistemi hâlâ tamamen dizel otobüslerden oluşmaktadır.",
    "bare_qa_span__473": "Semt pazarında kartlı ödeme sistemi tüm tezgâhlarda geçerlidir.",
    "bare_qa_span__474": "Mahalledeki çocuk parkına giriş ücretlidir.",
    "bare_qa_span__475": "Yeni yazılım güncellemesi iOS cihazlarda da kullanılabilmektedir.",
    "bare_qa_span__477": "Uygulamanın ücretsiz sürümünde reklam bulunmaktadır.",
    "bare_qa_span__479": "Yeni uygulama kullanıcı verilerini üçüncü taraflarla paylaşmaktadır.",
    "bare_qa_span__480": "Yeni yazılım kapalı kaynaklıdır.",
    "bare_qa_span__481": "Yeni yonga seti önceki modelle uyumludur.",
    "bare_qa_span__482": "Yeni telefonun parmak izi okuyucusu ekranın üstünde yer almaktadır.",
    "bare_qa_span__483": "Uygulamanın karanlık mod özelliği baştan beri vardır.",
    "bare_qa_span__485": "Yeni geliştirilen aşı, hamileler için onaylanmıştır.",
    "bare_qa_span__488": "Aşı iki doz halinde uygulanmaktadır.",
    "bare_qa_span__512": "Şirket geçen yıl zarar açıklamıştır.",
}

PROMPT_RE = re.compile(
    r"Kaynak:\s*(?P<source>.*?)\n\nSoru:\s*(?P<question>.*?)\n\nCevap:\s*\Z",
    re.DOTALL,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def messages_from_prompt(prompt: str) -> tuple[str, str]:
    match = PROMPT_RE.fullmatch(prompt)
    if not match:
        raise ValueError(f"Unexpected QA prompt shape: {prompt!r}")
    return match.group("source"), match.group("question")


def render_prompt(source: str, question: str) -> str:
    if not question.startswith(GROUNDING_PREFIX):
        question = GROUNDING_PREFIX + question[0].lower() + question[1:]
    return f"Kaynak: {source}\n\nSoru: {question}\n\nCevap:"


def main() -> None:
    observed_sha256 = sha256(SOURCE)
    if observed_sha256 != SOURCE_SHA256:
        raise RuntimeError(
            f"Source hash changed: expected {SOURCE_SHA256}, got {observed_sha256}. "
            "Review the new source before making a derived revision."
        )

    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise RuntimeError("Source CSV has no header")
        rows = list(reader)

    changed_ids: list[str] = []
    question_ids: list[str] = []
    for row in rows:
        messages = json.loads(row["messages"])
        if [message.get("role") for message in messages] != ["user", "assistant"]:
            raise ValueError(f"{row['id']}: expected user/assistant messages")
        source, question = messages_from_prompt(messages[0]["content"])
        question_ids.append(row["id"])

        if row["id"] in YES_REBALANCE_SOURCES:
            if row["answer_type"] != "yes_no" or messages[1]["content"] != "Hayır":
                raise ValueError(f"{row['id']}: expected a Hayır yes/no example")
            source = YES_REBALANCE_SOURCES[row["id"]]
            messages[1]["content"] = "Evet"
            changed_ids.append(row["id"])

        messages[0]["content"] = render_prompt(source, question)
        row["messages"] = json.dumps(messages, ensure_ascii=False)
        prior_notes = (row.get("notes") or "").strip()
        revision_note = "v1: source-grounded question; yes/no balance revision where applicable"
        row["notes"] = f"{prior_notes}; {revision_note}" if prior_notes else revision_note

    if len(changed_ids) != 19:
        raise RuntimeError(f"Expected 19 changed yes/no rows; got {len(changed_ids)}")

    answer_counts = Counter()
    for row in rows:
        messages = json.loads(row["messages"])
        if not messages[0]["content"].startswith("Kaynak: "):
            raise ValueError(f"{row['id']}: lost source framing")
        if "\n\nSoru: " not in messages[0]["content"]:
            raise ValueError(f"{row['id']}: lost question framing")
        if not GROUNDING_PREFIX in messages[0]["content"]:
            raise ValueError(f"{row['id']}: missing source-grounding prefix")
        if row["answer_type"] == "yes_no":
            answer_counts[messages[1]["content"]] += 1

    if answer_counts != Counter({"Evet": 42, "Hayır": 42}):
        raise RuntimeError(f"Yes/no balance failed: {dict(answer_counts)}")

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    audit = {
        "dataset_revision": "qa_span_dataset_v1",
        "parent_path": str(SOURCE),
        "parent_sha256": SOURCE_SHA256,
        "output_path": str(OUTPUT),
        "output_sha256": sha256(OUTPUT),
        "rows": len(rows),
        "transformations": {
            "question_grounding_prefix": GROUNDING_PREFIX,
            "questions_updated": len(question_ids),
            "yes_no_rows_rewritten_with_source_and_answer": changed_ids,
            "yes_no_answer_counts": dict(answer_counts),
        },
        "review_status": "needs_review",
        "reviewer": "cbark",
        "known_remaining_work": [
            "Manual quality review is pending.",
            "Phrase and date language repairs are not included in this owner-requested revision.",
            "CETVEL exact/near-duplicate contamination checks remain pending.",
            "Train/validation/test splits have not been assigned.",
        ],
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
