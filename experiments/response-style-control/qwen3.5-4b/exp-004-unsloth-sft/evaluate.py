#!/usr/bin/env python3
"""Generate reproducible raw outputs for the response-policy final benchmark.

Run once for the immutable base model before SFT and once for the pre-registered
final adapter. This program deliberately scores nothing: blind human scoring is
the evaluator defined by exp-002's rubric.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=HERE / "config.yaml")
    parser.add_argument("--role", choices=["base", "candidate"], required=True)
    parser.add_argument("--adapter", type=Path, help="Required for --role candidate.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N rows (diagnostic use).")
    parser.add_argument("--max-new-tokens", type=int, default=None, help="Override configured generation length.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    evaluation = config["evaluation"]
    model_config = config["model"]
    benchmark_path = (config_path.parent / evaluation["benchmark_path"]).resolve()
    if sha256(benchmark_path) != evaluation["benchmark_sha256"]:
        raise ValueError("Benchmark hash differs from config.yaml; refuse to generate against an unversioned test set.")
    if args.role == "candidate" and args.adapter is None:
        raise ValueError("--adapter is required for candidate evaluation.")
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation output: {args.output}")

    from unsloth import FastLanguageModel
    import torch

    load_name = str(args.adapter.resolve()) if args.role == "candidate" else model_config["name"]
    load_kwargs = {
        "model_name": load_name,
        "max_seq_length": 1024,
        "load_in_4bit": False,
        "load_in_16bit": True,
    }
    if args.role == "base":
        load_kwargs["revision"] = model_config["revision"]
    model, tokenizer = FastLanguageModel.from_pretrained(**load_kwargs)
    FastLanguageModel.for_inference(model)

    rows = list(csv.DictReader(benchmark_path.open(encoding="utf-8", newline="")))
    if args.limit is not None:
        rows = rows[:args.limit]
    max_new_tokens = args.max_new_tokens or int(evaluation["max_new_tokens"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        for row in rows:
            print(f"generating {row['id']}", flush=True)
            messages = [{"role": "user", "content": row["prompt_tr"]}]
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
            # Qwen3.5's processor accepts text by keyword; positional input
            # is reserved for images because the architecture is a VLM.
            inputs = tokenizer(images=None, text=text, return_tensors="pt", add_special_tokens=False).to(model.device)
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    do_sample=False,
                    temperature=0.0,
                    max_new_tokens=max_new_tokens,
                    use_cache=True,
                )
            text_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
            completion = text_tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            handle.write(json.dumps({"id": row["id"], "model_role": args.role, "output": completion}, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"completed {row['id']}", flush=True)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "role": args.role,
        "base_model": model_config["name"],
        "base_model_revision": model_config["revision"],
        "adapter": str(args.adapter.resolve()) if args.adapter else None,
        "benchmark": str(benchmark_path),
        "benchmark_sha256": sha256(benchmark_path),
        "config_sha256": sha256(config_path),
        "generation": {"thinking_mode": False, "do_sample": False, "temperature": 0.0, "max_new_tokens": max_new_tokens},
        "output_sha256": sha256(args.output),
        "items": len(rows),
    }
    args.output.with_suffix(args.output.suffix + ".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
