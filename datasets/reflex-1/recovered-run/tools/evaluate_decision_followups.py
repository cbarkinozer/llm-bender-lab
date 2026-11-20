"""Evaluate one frozen decision adapter on held-out phone and official test rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Saved adapter directory or base model ID")
    parser.add_argument("--phone-test", type=Path, required=True)
    parser.add_argument("--general-test-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-seq-length", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    args.output_dir.mkdir(parents=True)

    from datasets import Dataset
    from unsloth import FastDecisionModel
    from decision_training_utils import check_build_report

    started = time.time()
    model, tokenizer = FastDecisionModel.from_pretrained(
        model_name=args.model, max_seq_length=args.max_seq_length,
        dtype=None, load_in_4bit=True)
    tests = {"phone_historical": args.phone_test,
             "typed_decisions": args.general_test_dir / "typed_decisions.jsonl",
             "banking77": args.general_test_dir / "banking77.jsonl",
             "clinc150": args.general_test_dir / "clinc150.jsonl"}
    summary = {"model": args.model, "max_seq_length": args.max_seq_length,
               "batch_size": args.batch_size, "tests": {}}
    for name, path in tests.items():
        rows = load_jsonl(path)
        items, build_report = FastDecisionModel.build_dataset(Dataset.from_list(rows), tokenizer, model)
        check_build_report(items, build_report, name)
        if len(items) != len(rows):
            raise ValueError(f"Unexpected row count for {name}: {len(items)} vs {len(rows)}")
        metrics = FastDecisionModel.evaluate(model, tokenizer, items, batch_size=args.batch_size)
        for field in ("accuracy", "ece", "loss"):
            if field not in metrics or not math.isfinite(float(metrics[field])):
                raise ValueError(f"Invalid {field} for {name}: {metrics}")
        result = {"name": name, "rows": len(rows),
                  "decisions": sum(row.get("n_questions", len(json.loads(row["questions"]))) for row in rows),
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "build_report": build_report, "metrics": metrics,
                  "elapsed_seconds": round(time.time() - started, 2)}
        (args.output_dir / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        summary["tests"][name] = {"accuracy": metrics["accuracy"], "rows": len(rows)}
        print(json.dumps(summary["tests"][name] | {"test": name}), flush=True)
    summary["total_elapsed_seconds"] = round(time.time() - started, 2)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
