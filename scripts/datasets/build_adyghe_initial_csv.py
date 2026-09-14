#!/usr/bin/env python3
"""Build clean initial Adyghe SFT-candidate and benchmark CSV artifacts.

The combined CSV is deliberately model-neutral: ``input_text`` and
``target_text`` are semantic fields, not a chat template.  A future training
builder can render them with Qwen's current chat template.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


WIKTIONARY_SHA256 = "4b7e3bba72a79293d108873afe172cd9ffa3a6da192b781b4d9957b8ca89700d"
USER_SOURCE_SHA256 = "70edc807e964cc249282b0a0201eb70be7dcdad401825b761a22d84f0156e810"
BENCHMARK_SHA256 = "c1059e339dbf53ed8df10745d62db7f7fafa2899c1ea94015fa29177258366f5"
BENCHMARK_EXCLUSIONS = {"104", "107", "108", "109", "136", "137", "145", "191", "192", "193", "194", "195"}
SOURCE_GROUPS = {
    **{item_id: "crow_story" for item_id in range(97, 99)},
    99: "wind_and_sun_story",
    100: "udhr_article_1",
    **{item_id: "crow_story" for item_id in range(146, 161)},
    **{item_id: "wind_and_sun_story" for item_id in range(161, 176)},
    **{item_id: "udhr_article_1" for item_id in range(176, 181)},
}
CYRILLIC_FORM = re.compile(r"[А-Яа-яЁёӀӏ][А-Яа-яЁёӀӏ -]*")
POS_PATTERN = re.compile(r"<i>(.*?)</i>")
SENSE_PATTERN = re.compile(r"<li>(.*?)</li>", re.DOTALL)
HTML_TAG = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def plain_html(value: str) -> str:
    return WHITESPACE.sub(" ", html.unescape(HTML_TAG.sub(" ", value))).strip()


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def leading_cyrillic(value: str) -> str | None:
    match = CYRILLIC_FORM.match(value.strip())
    return match.group(0).strip(" -") if match else None


def user_category(line_number: int) -> str:
    if 3 <= line_number <= 47:
        return "orthography_romanization"
    if 48 <= line_number <= 71:
        return "phrase_translation"
    if 72 <= line_number <= 161:
        return "lexicon"
    if 162 <= line_number <= 170:
        return "parallel_text"
    if 172 <= line_number <= 195:
        return "story_lexicon"
    raise ValueError(f"unexpected user source line {line_number}")


def load_wiktionary(path: Path) -> list[dict[str, str]]:
    require_hash(path, WIKTIONARY_SHA256, "Wiktionary source")
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"Wiktionary line {line_number}: expected two TSV columns")
        raw_headword, raw_definition = fields
        segments = [segment.strip() for segment in raw_headword.split("|") if segment.strip()]
        lemma = leading_cyrillic(segments[0]) if segments else None
        if not lemma:
            raise ValueError(f"Wiktionary line {line_number}: missing Cyrillic lemma")
        variants = []
        for segment in segments:
            form = leading_cyrillic(segment)
            if form and form not in variants:
                variants.append(form)
        senses = [plain_html(value) for value in SENSE_PATTERN.findall(raw_definition)]
        pos = [plain_html(value) for value in POS_PATTERN.findall(raw_definition)]
        rows.append(
            {
                "id": f"wiktionary-{line_number:05d}",
                "source": "wiktionary",
                "source_id": str(line_number),
                "category": "lexicon",
                "input_text": lemma,
                "target_text": " ; ".join(senses),
                "part_of_speech": " | ".join(pos),
                "variants": " | ".join(variants),
                "quality_status": "accepted" if senses else "review_required",
            }
        )
    return rows


def load_user_source(path: Path) -> list[dict[str, str]]:
    require_hash(path, USER_SOURCE_SHA256, "user-authored source")
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"user source line {line_number}: expected two TSV columns")
        adyghe, gloss = (value.strip() for value in fields)
        # Objective normalizations previously recorded in the source audit.
        if line_number == 24:
            gloss = "h / kh"
        if line_number == 79:
            adyghe = "Мыр"
        rows.append(
            {
                "id": f"user-authored-{line_number:03d}",
                "source": "user_authored",
                "source_id": str(line_number),
                "category": user_category(line_number),
                "input_text": adyghe,
                "target_text": gloss,
                "part_of_speech": "",
                "variants": "",
                "quality_status": "accepted",
            }
        )
    return rows


def benchmark_contexts(user_source: Path) -> dict[str, dict[str, str]]:
    pairs = []
    for line in user_source.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            adyghe, english = line.split("\t", maxsplit=1)
            pairs.append((adyghe.strip(), english.strip()))
    selectors = {
        "crow_story": ("Once upon a time, there was a crow.", "He moved closer to it.", "He picked up those stones"),
        "wind_and_sun_story": ("The breeze and the sun were arguing", "They agreed that whoever", "Then, the wind began", "Then the sun started to shine"),
        "udhr_article_1": ("All human beings are born", "They are endowed with reason"),
    }
    contexts: dict[str, dict[str, str]] = {}
    for group, prefixes in selectors.items():
        selected = [pair for pair in pairs if any(pair[1].startswith(prefix) for prefix in prefixes)]
        if len(selected) != len(prefixes):
            raise ValueError(f"could not recover all {group} context lines")
        contexts[group] = {"adyghe": "\n".join(pair[0] for pair in selected), "english": "\n".join(pair[1] for pair in selected)}
    return contexts


def load_benchmark(path: Path, user_source: Path) -> list[dict[str, str]]:
    require_hash(path, BENCHMARK_SHA256, "benchmark source")
    contexts = benchmark_contexts(user_source)
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not re.match(r"^\d{3}\t", line):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"benchmark line {line_number}: expected four TSV columns")
        row_id, task, prompt, reference = fields
        if row_id in BENCHMARK_EXCLUSIONS:
            continue
        source_group = SOURCE_GROUPS.get(int(row_id))
        context = contexts[source_group]["english" if int(row_id) <= 100 else "adyghe"] if source_group else ""
        rows.append(
            {
                "id": f"adigebench-v0.2-candidate-{row_id}",
                "source_row_id": row_id,
                "task": task,
                "prompt": prompt.strip(),
                "reference": reference.strip(),
                "context": context,
                "scoring": "manual_native_review" if task in {"chat_ady_ady", "summary_ady_ady", "contrast_ady_ady"} else "exact_match_normalized",
                "native_review_required": str(task in {"chat_ady_ady", "summary_ady_ady", "contrast_ady_ady"} or 121 <= int(row_id) <= 145).lower(),
            }
        )
    if len(rows) != 188:
        raise ValueError(f"expected 188 benchmark rows after curation, got {len(rows)}")
    return rows


def benchmark_text(rows: list[dict[str, str]]) -> str:
    return "\n".join(normalized(f"{row['context']}\n{row['prompt']}\n{row['reference']}") for row in rows)


def overlaps_benchmark(record: dict[str, str], all_benchmark_text: str) -> bool:
    # Exact phrase containment is deliberately conservative. User-authored data
    # is excluded wholesale below because it is the benchmark's parent source.
    candidates = [record["input_text"], record["target_text"]]
    candidates.extend(part.strip() for part in record["variants"].split("|") if part.strip())
    return any(len(normalized(value)) >= 3 and normalized(value) in all_benchmark_text for value in candidates)


def split_eligible(records: list[dict[str, str]], seed: int) -> None:
    groups: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        if record["training_eligible"] == "true":
            # All variants belong to the same source record, and therefore one split.
            groups[f"{record['source']}|{record['category']}|{record['part_of_speech'] or 'unspecified'}"].append(record)
    for stratum, members in groups.items():
        ordered = sorted(
            members,
            key=lambda row: hashlib.sha256(f"{seed}:{stratum}:{row['id']}".encode()).hexdigest(),
        )
        count = len(ordered)
        validation_count = round(count * 0.10)
        test_count = round(count * 0.10)
        train_count = count - validation_count - test_count
        for index, record in enumerate(ordered):
            record["split"] = "train" if index < train_count else "validation" if index < train_count + validation_count else "test"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiktionary-source", type=Path, required=True)
    parser.add_argument("--user-source", type=Path, required=True)
    parser.add_argument("--benchmark-source", type=Path, required=True)
    parser.add_argument("--training-csv", type=Path, required=True)
    parser.add_argument("--benchmark-csv", type=Path, required=True)
    parser.add_argument("--audit-json", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3407)
    args = parser.parse_args()

    benchmark_rows = load_benchmark(args.benchmark_source, args.user_source)
    all_benchmark_text = benchmark_text(benchmark_rows)
    training_rows = load_wiktionary(args.wiktionary_source) + load_user_source(args.user_source)
    for record in training_rows:
        if record["quality_status"] != "accepted":
            record["training_eligible"] = "false"
            record["split"] = "excluded_review_required"
            record["exclusion_reason"] = "missing_target_text"
        elif record["source"] == "user_authored":
            record["training_eligible"] = "false"
            record["split"] = "excluded_benchmark_parent"
            record["exclusion_reason"] = "adige_data_is_a_parent_source_of_adige_bench"
        elif overlaps_benchmark(record, all_benchmark_text):
            record["training_eligible"] = "false"
            record["split"] = "excluded_benchmark_overlap"
            record["exclusion_reason"] = "exact_normalized_input_target_or_variant_overlap_with_benchmark"
        else:
            record["training_eligible"] = "true"
            record["split"] = "unassigned"
            record["exclusion_reason"] = ""
    split_eligible(training_rows, args.seed)

    training_fields = [
        "id", "split", "training_eligible", "exclusion_reason", "source", "source_id", "category",
        "input_text", "target_text", "part_of_speech", "variants", "quality_status",
    ]
    benchmark_fields = ["id", "source_row_id", "task", "context", "prompt", "reference", "scoring", "native_review_required"]
    write_csv(args.training_csv, training_fields, training_rows)
    write_csv(args.benchmark_csv, benchmark_fields, benchmark_rows)
    audit = {
        "dataset": "adyghe-initial-sft-candidates",
        "version": "v0.1",
        "split_seed": args.seed,
        "split_policy": "80/10/10 deterministic stratification by source/category/POS across eligible source-record groups",
        "benchmark_policy": "AdigeBench is an external final diagnostic. Parent-source rows and exact normalized overlaps are excluded from training candidates.",
        "training_row_count": len(training_rows),
        "training_counts_by_split": dict(sorted(Counter(row["split"] for row in training_rows).items())),
        "training_counts_by_source": dict(sorted(Counter(row["source"] for row in training_rows).items())),
        "benchmark_row_count": len(benchmark_rows),
        "benchmark_counts_by_task": dict(sorted(Counter(row["task"] for row in benchmark_rows).items())),
        "input_hashes": {
            "wiktionary": digest(args.wiktionary_source),
            "user_authored": digest(args.user_source),
            "benchmark": digest(args.benchmark_source),
        },
        "output_hashes": {"training_csv": digest(args.training_csv), "benchmark_csv": digest(args.benchmark_csv)},
    }
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
