#!/usr/bin/env python3
"""Build a small, reviewable SFT set with deterministic de-duplication.

The source CSVs are never modified.  This produces 200 examples per category,
caps repeated answer/template patterns, and writes a manifest describing every
filtering decision.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset"
OUT = ROOT / "clean-v2"
N = 200
SEED = 3407
CATEGORIES = ["bare_qa_span", "terse_summary", "numeric_entity_precision_qa", "open_ended_counterexample"]


def text(row: dict, index: int) -> str:
    return json.loads(row["messages"])[index]["content"].strip()


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"\d+(?:[.,]\d+)?", "<num>", value)
    value = re.sub(r"[^\w<>]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def content_fingerprint(prompt: str) -> str:
    # Remove fixed task wrappers so repeated synthetic sentence shapes become
    # visible, while retaining the actual content words.
    p = norm(prompt)
    for token in ("verilen cümlenin yazım hatalarını düzeltin", "kaynak", "soru", "cevap", "başlık", "metin", "özet"):
        p = p.replace(norm(token), " ")
    words = p.split()
    return " ".join(words[:8])


def answer_span_to_sentence(prompt: str, answer: str) -> tuple[str, str]:
    """Put an extractive answer into the question's grammatical frame."""
    question = prompt.split("Soru:", 1)[-1].split("Cevap:", 1)[0].strip().rstrip("?").strip()
    out = question
    kind = "fallback"
    if re.search(r"\bkim\b", out, flags=re.IGNORECASE):
        out = re.sub(r"\bkim\b", answer, out, count=1, flags=re.IGNORECASE)
        kind = "who"
    elif re.search(r"\bnerede(?:dir)?\b", out, flags=re.IGNORECASE):
        # Location answers already carry -da/-de/-ta/-te. Add the Turkish
        # copula so the result is a complete sentence: "... avlusundadır."
        vowels = re.findall(r"[aıoueiöü]", answer.lower())
        suffix = {"a": "dır", "ı": "dır", "o": "dur", "u": "dur", "e": "dir", "i": "dir", "ö": "dür", "ü": "dür"}.get(vowels[-1], "dır") if vowels else "dır"
        location = answer.rstrip(".!?") + suffix
        out = re.sub(r"\bnerede(?:dir)?\b", location, out, count=1, flags=re.IGNORECASE)
        kind = "where"
    elif re.search(r"\bkaçtır\b", out, flags=re.IGNORECASE):
        out = re.sub(r"\bkaçtır\b", f"{answer} olarak belirtilmiştir", out, count=1, flags=re.IGNORECASE)
        kind = "quantity"
    elif re.search(r"\bkaç\b", out, flags=re.IGNORECASE):
        out = re.sub(r"\bkaç\b", answer, out, count=1, flags=re.IGNORECASE)
        kind = "quantity"
    else:
        # Keep the answer visible for manual review rather than inventing a
        # grammatical relation that is not supported by the question.
        out = answer
    out = out[:1].upper() + out[1:]
    if out and out[-1] not in ".!?":
        out += "."
    return out, kind


def load_rows(category: str) -> list[dict]:
    path = ROOT / f"{category}.csv"
    # accepted-reviewed is the authoritative post-review source when present.
    reviewed = ROOT / "reviewed-v3/accepted-reviewed.csv"
    if reviewed.exists():
        rows = [r for r in csv.DictReader(reviewed.open(encoding="utf-8-sig", newline="")) if r["category"] == category]
    else:
        rows = [r for r in csv.DictReader(path.open(encoding="utf-8-sig", newline=""))]
    return rows


def choose(category: str, rows: list[dict]) -> tuple[list[dict], dict]:
    rng = random.Random(SEED + CATEGORIES.index(category))
    # First remove exact duplicate prompt/target pairs.
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    exact_removed = []
    for row in rows:
        key = (text(row, 0), text(row, 1))
        if key in seen:
            exact_removed.append(row["id"])
            continue
        seen.add(key)
        unique.append(row)

    # Prefer substantive answers.  One-word answers are valid for extractive
    # QA and numeric precision, so they are capped rather than eliminated.
    def substantive(row: dict) -> bool:
        return len(text(row, 1).split()) > 1

    rng.shuffle(unique)
    unique.sort(key=lambda r: (not substantive(r), r["id"]))
    answer_cap = 4 if category in {"bare_qa_span", "numeric_entity_precision_qa"} else 3
    template_cap = 4
    selected: list[dict] = []
    answer_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    one_word = 0
    rejected = []
    for row in unique:
        if len(selected) >= N:
            break
        answer_key = norm(text(row, 1))
        template_key = content_fingerprint(text(row, 0))
        is_one = not substantive(row)
        if answer_counts[answer_key] >= answer_cap:
            rejected.append((row["id"], "answer_cap"))
            continue
        if template_counts[template_key] >= template_cap:
            rejected.append((row["id"], "template_cap"))
            continue
        selected.append(row)
        answer_counts[answer_key] += 1
        template_counts[template_key] += 1
        one_word += int(is_one)

    # Fill exactly N if caps were too strict, still preserving exact dedup.
    if len(selected) < N:
        selected_ids = {r["id"] for r in selected}
        for row in unique:
            if row["id"] in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row["id"])
            one_word += int(not substantive(row))
            if len(selected) == N:
                break

    if len(selected) != N:
        raise RuntimeError(f"{category}: only {len(selected)} unique rows available")
    selected.sort(key=lambda r: r["id"])
    answer_rewrites = Counter()
    if category == "bare_qa_span":
        rewritten = []
        for row in selected:
            row = dict(row)
            messages = json.loads(row["messages"])
            new_target, kind = answer_span_to_sentence(messages[0]["content"], messages[1]["content"])
            messages[1]["content"] = new_target
            row["messages"] = json.dumps(messages, ensure_ascii=False)
            answer_rewrites[kind] += 1
            rewritten.append(row)
        selected = rewritten
    return selected, {
        "source_rows": len(rows),
        "exact_duplicate_rows_removed": len(exact_removed),
        "exact_duplicate_ids_removed": exact_removed,
        "selected_rows": len(selected),
        "selected_one_word_targets": one_word,
        "selected_one_word_fraction": round(one_word / N, 4),
        "answer_cap": answer_cap,
        "template_cap": template_cap,
        "rejected_by_cap": len(rejected),
        "answer_span_rewrites": dict(answer_rewrites),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"version": "clean-sft-v2", "seed": SEED, "target_per_category": N, "categories": {}, "files": {}}
    all_rows = []
    for category in CATEGORIES:
        rows, stats = choose(category, load_rows(category))
        out = OUT / f"{category}.csv"
        fields = list(rows[0].keys())
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        manifest["categories"][category] = stats
        manifest["files"][out.name] = {"rows": len(rows), "sha256": digest}
        all_rows.extend(rows)
    combined = OUT / "sft-clean-v2-800.csv"
    with combined.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader(); writer.writerows(all_rows)
    manifest["files"][combined.name] = {"rows": len(all_rows), "sha256": hashlib.sha256(combined.read_bytes()).hexdigest()}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
