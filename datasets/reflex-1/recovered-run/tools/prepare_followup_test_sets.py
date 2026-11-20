"""Freeze held-out official test subsets after training, with no optimizer exposure."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import random
import urllib.request
from pathlib import Path

from datasets import load_dataset
from prepare_general_mixture import SOURCE_REVISIONS, convert_typed_decisions, intent_row, normalize


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> str:
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def balanced_subset(rows: list[dict], per_class: int, seed: int) -> list[dict]:
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        groups[row["route__label"]].append(row)
    rng = random.Random(seed)
    selected = []
    for label in sorted(groups):
        group = sorted(groups[label], key=lambda row: row["id"])
        if len(group) < per_class:
            raise ValueError(f"Too few test examples for {label}: {len(group)}")
        selected.extend(rng.sample(group, per_class))
    rng.shuffle(selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--general-train", type=Path, required=True)
    parser.add_argument("--phone-train", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--hf-cache", type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    td = SOURCE_REVISIONS["typed_decisions"]
    cl = SOURCE_REVISIONS["clinc150"]
    bank = SOURCE_REVISIONS["banking77"]
    typed_raw = load_dataset(td["repo"], td["config"], split="test", revision=td["revision"], cache_dir=str(args.hf_cache) if args.hf_cache else None)
    clinc_raw = load_dataset(cl["repo"], cl["config"], split="test", revision=cl["revision"], cache_dir=str(args.hf_cache) if args.hf_cache else None)
    bank_url = f"https://raw.githubusercontent.com/{bank['repo']}/{bank['revision']}/banking_data/test.csv"
    bank_payload = urllib.request.urlopen(bank_url, timeout=60).read()
    bank_raw = list(csv.DictReader(io.StringIO(bank_payload.decode("utf-8"))))
    bank_labels = sorted({row["category"] for row in bank_raw})
    clinc_labels = clinc_raw.features["intent"].names
    clinc_intents = sorted(label for label in clinc_labels if label != "oos")
    if len(bank_labels) != 77 or len(clinc_intents) != 150:
        raise ValueError("Official intent class counts changed")

    typed = [convert_typed_decisions(row, prefix="td_test") for row in typed_raw]
    banking = [intent_row(row["text"], row["category"], bank_labels, "banking77", "test", i)
               for i, row in enumerate(bank_raw)]
    clinc = [intent_row(row["text"], clinc_labels[row["intent"]], clinc_intents, "clinc150", "test", i)
             for i, row in enumerate(clinc_raw) if clinc_labels[row["intent"]] != "oos"]
    tests = {"typed_decisions": typed,
             "banking77": balanced_subset(banking, 6, 3407),
             "clinc150": balanced_subset(clinc, 3, 3407)}
    train_states = {normalize(row["state"]) for path in (args.general_train, args.phone_train) for row in load_jsonl(path)}
    for name, rows in tests.items():
        overlap = train_states & {normalize(row["state"]) for row in rows}
        if overlap:
            raise ValueError(f"Train/test text overlap in {name}: {len(overlap)}")
    args.output_dir.mkdir(parents=True)
    files = {}
    for name, rows in tests.items():
        files[name] = {"rows": len(rows), "decisions": sum(row["n_questions"] for row in rows),
                       "classes": len({row["route__label"] for row in rows}),
                       "sha256": write_jsonl(args.output_dir / f"{name}.jsonl", rows),
                       "ids": [row["id"] for row in rows]}
    manifest = {"seed": 3407, "source_revisions": SOURCE_REVISIONS,
                "banking_test_csv_sha256": hashlib.sha256(bank_payload).hexdigest(),
                "train_state_overlap": 0, "files": files,
                "selection": "All typed official test; 6 per BANKING77 class; 3 per CLINC150 class; OOS excluded"}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print({name: {key: value for key, value in meta.items() if key != "ids"} for name, meta in files.items()})


if __name__ == "__main__":
    main()
