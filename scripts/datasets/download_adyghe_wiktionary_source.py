#!/usr/bin/env python3
"""Download the pinned upstream Adyghe--English Wiktionary TSV verbatim."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


COMMIT = "be0cfb8d614470bc8b9d9006ddff8b921cd5c2e3"
PATH = "Adyghe-English%20Wiktionary%20dictionary.tsv"
URL = f"https://raw.githubusercontent.com/Vuizur/Wiktionary-Dictionaries/{COMMIT}/{PATH}"
EXPECTED_SHA256 = "4b7e3bba72a79293d108873afe172cd9ffa3a6da192b781b4d9957b8ca89700d"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    with urlopen(URL) as response:  # nosec B310: immutable GitHub raw URL above
        data = response.read()
    digest = sha256_bytes(data)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"download hash mismatch: expected {EXPECTED_SHA256}, got {digest}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    manifest = {
        "upstream_repository": "https://github.com/Vuizur/Wiktionary-Dictionaries",
        "upstream_commit": COMMIT,
        "upstream_path": "Adyghe-English Wiktionary dictionary.tsv",
        "download_url": URL,
        "sha256": digest,
        "byte_count": len(data),
        "license": "CC-BY-SA-3.0 and GFDL (as declared by the upstream repository)",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
