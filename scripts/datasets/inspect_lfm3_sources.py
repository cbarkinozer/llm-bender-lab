"""Read pinned HF source tables; write metadata/counts only, never training data.

Requires pyarrow. Downloads parquet files into memory; executes no remote code.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import unicodedata
from urllib.request import urlopen

import pyarrow.parquet as pq


def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read()


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def inspect(repo, revision):
    info = json.loads(fetch(f"https://huggingface.co/api/datasets/{repo}/revision/{revision}"))
    result = {"repo": repo, "revision": info["sha"],
              "card": info.get("cardData", {}), "files": []}
    for item in info["siblings"]:
        name = item["rfilename"]
        if not name.endswith(".parquet"):
            continue
        raw = fetch(f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{name}")
        rows = pq.read_table(io.BytesIO(raw)).to_pylist()
        entry = {"path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                 "rows": len(rows), "columns": list(rows[0]) if rows else []}
        if rows and "language" in rows[0]:
            entry["languages"] = dict(sorted(Counter(r["language"] for r in rows).items()))
            entry["turkish_rows"] = sum(r["language"] in ("tr", "tur", "tur_Latn") for r in rows)
        if rows and "sentence_good" in rows[0]:
            keys = [(normalized(r["sentence_good"]), normalized(r["sentence_bad"])) for r in rows]
            entry["identical_pairs"] = sum(a == b for a, b in keys)
            entry["empty_pairs"] = sum(not a or not b for a, b in keys)
            entry["duplicate_pair_excess"] = len(keys) - len(set(keys))
            # IDs only: no benchmark sentences in this metadata artifact.
            entry["identical_pair_ids"] = [str(r["item_id"]) for r, (a, b) in zip(rows, keys) if a == b]
        result["files"].append(entry)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    report = {"captured_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Full pinned parquet language counts and within-file minimal-pair sanity checks; not a semantic or cross-split leakage audit.",
              "datasets": []}
    for source in config["inspection_sources"]:
        result = inspect(source["repo"], source["revision"])
        report["datasets"].append(result)
        print(source["repo"], sum(f["rows"] for f in result["files"]), "rows", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
