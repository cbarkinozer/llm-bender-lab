#!/usr/bin/env python3
"""Freeze general decision data locally; no GPU, credentials or W&B required.

Official test states are exclusion inputs only. Historical evaluation selections
are copied unchanged when --historical-dir is supplied. They are never resampled.
Existing output directories are refused to prevent accidental re-freezing.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import random
import re
import urllib.request
from pathlib import Path

SOURCE_REVISIONS = {
    "typed_decisions": {"repo": "LocalLLaMA/typed-decisions", "revision": "6a7927fa3c8ac114e29f5300eacb86f6f37a6447", "config": "all", "license": "apache-2.0"},
    "banking77": {"repo": "PolyAI-LDN/task-specific-datasets", "revision": "57ec275d8078af65b7731c2a98be812d844a6d6b", "license": "cc-by-4.0"},
    "clinc150": {"repo": "clinc/clinc_oos", "revision": "155b9c710419136e17307b80d0a13e68cd46b4ec", "config": "plus", "license": "cc-by-3.0", "oos_excluded": True},
}
DEFAULT_WEIGHTS = {"typed_decisions": 1.0, "banking77": 0.5, "clinc150": 0.5}


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    return file_sha256(path)


def parsed(value):
    return json.loads(value) if isinstance(value, str) else value


def convert_typed_decisions(row, prefix="td"):
    # Preserve all typed questions and soft gold distributions, not a fake route.
    questions, gold = parsed(row["questions"]), parsed(row["gold"])
    if not questions or set(questions) != set(gold):
        raise ValueError("Typed question/gold mismatch")
    state = row["state"]
    if not isinstance(state, str):
        state = json.dumps(state, sort_keys=True)
    return {"id": f"{prefix}_{row['id']}", "source": "typed_decisions",
            "state": state, "questions": json.dumps(questions, sort_keys=True),
            "gold": json.dumps(gold, sort_keys=True),
            "workflow": row["workflow"], "route__label": row["workflow"],
            "n_questions": len(questions)}


def intent_row(text, label, labels, source, split, index):
    if label not in labels or not text.strip():
        raise ValueError("Invalid intent row")
    question = {"intent": {"type": "choice",
                "instructions": "Which intent best matches the user request? Select exactly one intent.",
                "criteria": {k: k.replace("_", " ").replace("?", "") for k in labels}}}
    gold = {"intent": {"type": "choice", "label": label,
             "probabilities": {k: float(k == label) for k in labels}}}
    return {"id": f"{source}_{split}_{index:06d}", "source": source,
            "source_index": index, "state": text, "route__label": label,
            "workflow": source + "_intent", "questions": json.dumps(question, sort_keys=True),
            "gold": json.dumps(gold, sort_keys=True), "n_questions": 1}


def stratified_split(rows, seed):
    rng = random.Random(seed)
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["route__label"]].append(row)
    train, val, calib = [], [], []
    for label, group in sorted(groups.items()):
        group = sorted(group, key=lambda r: r["id"])
        rng.shuffle(group)
        nv, nc = max(1, round(len(group) * .10)), max(1, round(len(group) * .05))
        if len(group) <= nv + nc:
            raise ValueError(f"Insufficient examples for {label}")
        val.extend(group[:nv]); calib.extend(group[nv:nv+nc]); train.extend(group[nv+nc:])
    return train, val, calib


def weighted_sample(sources, weights, seed):
    # Largest feasible mixture with the requested relative counts; no duplicates.
    if set(weights) != set(sources) or any(not math.isfinite(w) or w <= 0 for w in weights.values()):
        raise ValueError("Supply a positive finite weight for every source")
    scale = min(len(rows) / weights[name] for name, rows in sources.items())
    rng = random.Random(seed)
    result, counts = [], {}
    for source, rows in sorted(sources.items()):
        count = min(len(rows), max(1, round(scale * weights[source])))
        groups = collections.defaultdict(list)
        for row in rows:
            groups[row["route__label"]].append(row)
        labels = sorted(groups)
        if count < len(labels):
            raise ValueError(f"Mixture budget omits classes in {source}: {count} < {len(labels)}")
        rng.shuffle(labels)
        sampled = []
        for label in labels:
            rng.shuffle(groups[label])
        # Round-robin keeps source sampling balanced while respecting availability.
        while len(sampled) < count:
            for label in labels:
                if groups[label] and len(sampled) < count:
                    sampled.append(groups[label].pop())
        result.extend(sampled); counts[source] = count
    rng.shuffle(result)
    return result, counts


def clean_pool(rows, protected, excluded):
    seen, result = set(), []
    for row in rows:
        key = normalize(row["state"])
        if key in protected or key in seen:
            excluded.append({"id": row["id"], "reason": "protected_state" if key in protected else "duplicate_state"})
        else:
            seen.add(key); result.append(row)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--hf-cache", type=str)
    p.add_argument("--weights", default="typed_decisions=1.0,banking77=0.5,clinc150=0.5")
    p.add_argument("--seed", type=int, default=3407)
    p.add_argument("--historical-dir", type=Path, help="Original pod backup extracted directory")
    p.add_argument("--phone-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data/phone_routing")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    weights = {k: float(v) for k, v in (part.split("=") for part in args.weights.split(","))}
    if args.dry_run:
        print(json.dumps({"sources": SOURCE_REVISIONS, "weights": weights}, indent=2)); return
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite frozen output: {args.output_dir}")
    if args.seed != 3407:
        raise ValueError("This experiment freezes seed 3407, including reflex-1 exposure reconstruction")
    from datasets import load_dataset
    td_meta, cl_meta = SOURCE_REVISIONS["typed_decisions"], SOURCE_REVISIONS["clinc150"]
    td = load_dataset(td_meta["repo"], "all", revision=td_meta["revision"], cache_dir=args.hf_cache)
    if args.historical_dir:
        snapshot = args.historical_dir / "runs/data-snapshot/typed-decisions-train.jsonl"
        original = [json.loads(line) for line in snapshot.read_text().splitlines() if line.strip()]
        if [(r["id"], r["state"], r["n_questions"]) for r in original] != [(r["id"], r["state"], r["n_questions"]) for r in td["train"]]:
            raise ValueError("Original typed-decisions row order/content changed; cannot reconstruct holdout")
    cl = load_dataset(cl_meta["repo"], "plus", revision=cl_meta["revision"], cache_dir=args.hf_cache)
    bank = {}
    downloads = {}
    for split in ("train", "test"):
        url = f"https://raw.githubusercontent.com/{SOURCE_REVISIONS['banking77']['repo']}/{SOURCE_REVISIONS['banking77']['revision']}/banking_data/{split}.csv"
        payload = urllib.request.urlopen(url, timeout=60).read()
        downloads[split] = {"url": url, "sha256": hashlib.sha256(payload).hexdigest()}
        bank[split] = list(csv.DictReader(io.StringIO(payload.decode())))
    bank_labels = sorted({r["category"] for r in bank["train"]})
    cl_labels = cl["train"].features["intent"].names
    intent_labels = sorted(k for k in cl_labels if k != "oos")
    assert len(bank_labels) == 77 and len(intent_labels) == 150
    pools = {"typed_decisions": [convert_typed_decisions(r) for r in td["train"]],
             "banking77": [intent_row(r["text"], r["category"], bank_labels, "banking77", "train", i) for i, r in enumerate(bank["train"])],
             "clinc150": [intent_row(r["text"], cl_labels[r["intent"]], intent_labels, "clinc150", "train", i) for i, r in enumerate(cl["train"]) if cl_labels[r["intent"]] != "oos"]}
    protected = {normalize(r["state"]) for r in td["test"]}
    protected.update(normalize(r["text"]) for r in bank["test"])
    protected.update(normalize(r["text"]) for r in cl["test"])
    phone_hashes = {}
    for path in sorted(args.phone_dir.glob("*.jsonl")):
        phone_hashes[path.name] = file_sha256(path)
        protected.update(normalize(json.loads(line)["state"]) for line in path.read_text().splitlines() if line.strip())
    original_td = pools["typed_decisions"]
    # Reconstruct the *original* split_holdout algorithm at the recorded Unsloth
    # revision: 400 decisions, five per case, row indices shuffled with seed 3407.
    assert len(original_td) == 1200 and all(r["n_questions"] == 5 for r in original_td)
    indices = list(range(len(original_td))); random.Random(3407).shuffle(indices)
    held = set(indices[:80])
    original_training = {normalize(r["state"]) for i, r in enumerate(original_td) if i not in held}
    excluded, splits = [], {}
    for source, rows in pools.items():
        rows = clean_pool(rows, protected, excluded)
        if source == "typed_decisions":
            # Never carve new validation from cases used to train reflex-1.
            train = [r for r in rows if normalize(r["state"]) in original_training]
            holdout = [r for r in rows if normalize(r["state"]) not in original_training]
            holdout.sort(key=lambda r: r["id"])
            random.Random(args.seed).shuffle(holdout)
            val, calib = holdout[::2], holdout[1::2]
            splits[source] = train, val, calib
        else:
            splits[source] = stratified_split(rows, args.seed)
    train, counts = weighted_sample({s: v[0] for s, v in splits.items()}, weights, args.seed)
    val = [r for v in splits.values() for r in v[1]]
    calib = [r for v in splits.values() for r in v[2]]
    final = {"train": train, "val": val, "calibration": calib}
    keys = {s: {normalize(r["state"]) for r in rows} for s, rows in final.items()}
    for left, right in (("train", "val"), ("train", "calibration"), ("val", "calibration")):
        if keys[left] & keys[right]:
            raise ValueError(f"Cross-source state leakage: {left}/{right}")
    if (keys["val"] | keys["calibration"]) & original_training:
        raise ValueError("Validation/calibration overlaps reflex-1 original training")
    for rows in final.values():
        if len({r["id"] for r in rows}) != len(rows):
            raise ValueError("Duplicate IDs")
        for r in rows:
            if set(parsed(r["questions"])) != set(parsed(r["gold"])):
                raise ValueError("Question/gold schema mismatch")
    args.output_dir.mkdir(parents=True)
    files = {}
    for split, rows in final.items():
        for row in rows:
            row["split"] = split
        files[split] = {"sha256": write_jsonl(args.output_dir / f"{split}.jsonl", rows), "records": len(rows),
                        "decisions": sum(r["n_questions"] for r in rows), "ids": [r["id"] for r in rows],
                        "per_source": dict(collections.Counter(r["source"] for r in rows)),
                        "per_source_label_counts": {source: dict(collections.Counter(r["route__label"] for r in rows if r["source"] == source)) for source in SOURCE_REVISIONS}}
    historical_files = {}
    if args.historical_dir:
        for name in ("banking77-selection.json", "clinc150-selection.json"):
            src = args.historical_dir / "runs/balanced-benchmarks" / name
            if not src.exists():
                raise FileNotFoundError(f"Historical selection missing: {src}")
            target = args.output_dir / ("historical-" + name)
            target.write_bytes(src.read_bytes()); historical_files[target.name] = file_sha256(target)
    write_json(args.output_dir / "source-revisions.json", {"sources": SOURCE_REVISIONS, "banking_downloads": downloads})
    write_json(args.output_dir / "split-manifest.json", {
        "dataset": "general_routing_v1", "seed": args.seed, "files": files,
        "requested_weights": weights, "actual_train_counts": counts,
        "actual_train_proportions": {k: v / len(train) for k, v in counts.items()},
        "historical_files": historical_files, "protected_phone_hashes": phone_hashes,
        "excluded": excluded, "normalized_cross_split_overlap": 0,
        "reflex1_original_training_overlap_with_val_calibration": 0,
        "typed_holdout_provenance": "Reconstructed original 80-case seed-3407 holdout using Unsloth a70b2a8f7b88c3b8492409efef1dce3d670787f6 split_holdout. Previously evaluated/calibrated; not pristine evidence. Split 40/40, never original 1120 training cases.",
        "near_duplicate_status": "Not assessed for general data; normalized identity checks are not semantic decontamination",
        "test_policy": "Official tests used only for exclusion; no new test sampling; historical selections copied unchanged",
    })
    print(json.dumps({"output": str(args.output_dir), "splits": {s: m["per_source"] for s, m in files.items()}, "excluded": len(excluded)}, indent=2))


if __name__ == "__main__":
    main()
