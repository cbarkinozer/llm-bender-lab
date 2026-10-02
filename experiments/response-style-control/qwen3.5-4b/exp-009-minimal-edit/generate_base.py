"""Prepare base drafts with auditable natural termination; never trains a model."""
import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_finish(token_ids, budget, eos_ids):
    if not token_ids:
        return "empty"
    if token_ids[-1] in eos_ids:
        return "native_eos"
    if len(token_ids) >= budget:
        return "length_limit"
    return "unexpected_stop"


def validate_inputs(config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    path = (config_path.parent / config["dataset_path"]).resolve()
    if sha256(path) != config["dataset_sha256"]:
        raise ValueError("Prompt hash does not match generation configuration")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != config["expected_rows"] or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Unexpected row count or duplicate IDs")
    if dict(Counter(r["split"] for r in rows)) != config["expected_split_counts"]:
        raise ValueError("Unexpected split")
    audit_path = path.parent / "audit-report.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["status"] != "passed" or audit["cross_split_near_flags"] or audit["cross_split_exact_turn_or_prompt_matches"]:
        raise ValueError("Overlap audit is not passed")
    manifest = json.loads((path.parent / "selection-manifest.json").read_text(encoding="utf-8"))
    for name, info in manifest["artifacts"].items():
        if sha256(path.parent / name) != info["sha256"]:
            raise ValueError(f"Frozen dataset artifact changed: {name}")
    budgets = config["generation"]["output_token_budgets"]
    if not budgets or sorted(set(budgets)) != budgets or any(not isinstance(b, int) or b < 1 for b in budgets):
        raise ValueError("Output budgets must be increasing positive integers")
    if config["generation"]["forced_eos_token_id"] is not None or config["generation"]["input_truncation"]:
        raise ValueError("Forced EOS or input truncation is forbidden")
    if config["model"]["adapter"] is not None:
        raise ValueError("Only the unadapted model is permitted")
    if config["model"]["revision"] != config["model"]["tokenizer_revision"]:
        raise ValueError("Model/tokenizer pins must agree")
    gen = config["generation"]
    if gen["thinking_mode"] or gen["do_sample"] or gen["num_beams"] != 1 or gen["repetition_penalty"] != 1.0 or gen["additional_system_prompt"] is not None:
        raise ValueError("This entrypoint implements the frozen greedy/non-thinking/no-added-system protocol only")
    if gen["stop_policy"] != "native_eos_or_end_of_turn":
        raise ValueError("Only native EOS/end-of-turn stopping is allowed")
    for row in rows:
        if row["dataset_version"] != config["dataset_version"] or row["messages"][-1]["role"] != "user":
            raise ValueError(f"Invalid row {row['id']}")
        if row["answer_status"] != "not-generated":
            raise ValueError("Generation inputs must not include previously generated targets")
        data = json.dumps(row["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if hashlib.sha256(data).hexdigest() != row["input_messages_sha256"]:
            raise ValueError(f"Message identity mismatch: {row['id']}")
    return config, path, rows


def json_file(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def git_info():
    repo = HERE.parents[3]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
    return {"commit": commit.stdout.strip() if commit.returncode == 0 else None,
            "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=HERE / "generation-config.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="CPU-only input/config validation; no model imports")
    subset = parser.add_mutually_exclusive_group()
    subset.add_argument("--limit", type=int)
    subset.add_argument("--ids", help="Comma-separated IDs for diagnostic generation")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config, dataset_path, rows = validate_inputs(config_path)
    all_count = len(rows)
    if args.limit is not None:
        if not 1 <= args.limit <= all_count:
            raise ValueError("Diagnostic limit out of range")
        rows = rows[:args.limit]
    if args.ids:
        ids = args.ids.split(",")
        if len(set(ids)) != len(ids) or not set(ids) <= {r["id"] for r in rows}:
            raise ValueError("Unknown or duplicate diagnostic IDs")
        rows = [r for r in rows if r["id"] in ids]
    if args.dry_run:
        print(json.dumps({"status": "cpu_input_checks_passed", "frozen_rows": all_count,
                          "selected_rows": len(rows), "split": config["expected_split_counts"],
                          "token_budgets": config["generation"]["output_token_budgets"],
                          "cuda_or_model_loaded": False}, indent=2))
        return
    if args.output_dir is None:
        raise ValueError("--output-dir is required for GPU generation")
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite any previous run: {output_dir}")
    output_dir.mkdir(parents=True)
    manifest = {"status": "initializing", "created_at": datetime.now(timezone.utc).isoformat(),
                "config": config, "config_sha256": sha256(config_path), "dataset_sha256": sha256(dataset_path),
                "dataset_manifest_sha256": sha256(dataset_path.parent / "selection-manifest.json"),
                "coverage_map_sha256": sha256(dataset_path.parent / "coverage-map.json"),
                "overlap_audit_sha256": sha256(dataset_path.parent / "audit-report.json"),
                "entrypoint_sha256": sha256(Path(__file__).resolve()), "argv": sys.argv,
                "git": git_info(), "python": platform.python_version(), "platform": platform.platform(),
                "selected_ids": [r["id"] for r in rows], "diagnostic_subset": len(rows) != all_count,
                "environment_allowlist": {k: os.environ[k] for k in ["HF_HOME", "PIP_CACHE_DIR", "UV_CACHE_DIR"] if k in os.environ}}
    json_file(output_dir / "run-manifest.json", manifest)
    try:
        # Import Unsloth before Torch/Transformers; use the established project stack.
        from unsloth import FastLanguageModel
        import torch

        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("CUDA GPU with BF16 support is required; do not run on the local 4 GB GPU")
        torch.manual_seed(config["generation"]["seed"])
        manifest["packages"] = {}
        for name in ["torch", "transformers", "unsloth", "unsloth-zoo", "accelerate", "flash-linear-attention", "fla-core", "causal-conv1d"]:
            try:
                manifest["packages"][name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                manifest["packages"][name] = None
        manifest["hardware"] = {"gpu": torch.cuda.get_device_name(0), "cuda": torch.version.cuda,
                                "vram_bytes": torch.cuda.get_device_properties(0).total_memory}
        manifest["backend"] = {"float32_matmul_precision": torch.get_float32_matmul_precision(),
                               "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                               "cudnn_version": torch.backends.cudnn.version(),
                               "cudnn_deterministic": torch.backends.cudnn.deterministic,
                               "cudnn_benchmark": torch.backends.cudnn.benchmark}
        model, processor = FastLanguageModel.from_pretrained(
            model_name=config["model"]["name"], revision=config["model"]["revision"],
            max_seq_length=config["model"]["context_tokens"], dtype=torch.bfloat16,
            load_in_4bit=False, load_in_16bit=True,
        )
        FastLanguageModel.for_inference(model)
        model.eval()
        json_file(output_dir / "effective-model-config.json", model.config.to_dict())
        text_tokenizer = getattr(processor, "tokenizer", processor)
        native = model.generation_config.eos_token_id
        if native is None:
            native = text_tokenizer.eos_token_id
        eos_ids = native if isinstance(native, list) else [native]
        if not eos_ids or any(not isinstance(i, int) or i < 0 for i in eos_ids):
            raise RuntimeError("No valid native EOS/end-of-turn IDs found")
        gen_config = copy.deepcopy(model.generation_config)
        gen_config.do_sample = False
        gen_config.num_beams = 1
        gen_config.num_return_sequences = 1
        gen_config.temperature = None
        gen_config.top_p = None
        gen_config.top_k = None
        gen_config.repetition_penalty = 1.0
        gen_config.forced_eos_token_id = None
        gen_config.forced_bos_token_id = None
        gen_config.min_length = 0
        gen_config.min_new_tokens = 0
        gen_config.max_time = None
        gen_config.stop_strings = None
        gen_config.eos_token_id = eos_ids
        gen_config.use_cache = True
        manifest["native_eos_ids"] = eos_ids
        manifest["native_eos_tokens"] = text_tokenizer.convert_ids_to_tokens(eos_ids)
        manifest["effective_generation_config"] = gen_config.to_dict()
        manifest["chat_template"] = getattr(processor, "chat_template", None) or getattr(text_tokenizer, "chat_template", None)
        manifest["status"] = "generating"
        json_file(output_dir / "run-manifest.json", manifest)
        complete, incomplete = [], []
        budgets = config["generation"]["output_token_budgets"]
        with (output_dir / "attempts.jsonl").open("x", encoding="utf-8", newline="\n") as attempts_file, (output_dir / "drafts.jsonl").open("x", encoding="utf-8", newline="\n") as drafts_file:
            for row in rows:
                # Do not inject the style rubric or expected answer into the input.
                rendered = processor.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False)
                inputs = processor(images=None, text=rendered, return_tensors="pt", add_special_tokens=False, truncation=False).to(model.device)
                input_length = inputs["input_ids"].shape[1]
                if input_length + budgets[-1] > config["model"]["context_tokens"]:
                    raise ValueError(f"Context budget exceeded without truncation: {row['id']}")
                latest = None
                for attempt, budget in enumerate(budgets, 1):
                    print(f"generating {row['id']} attempt={attempt} budget={budget}", flush=True)
                    started = time.monotonic()
                    with torch.inference_mode():
                        output = model.generate(**inputs, generation_config=gen_config, max_new_tokens=budget)
                    ids = output[0, input_length:].detach().cpu().tolist()
                    finish = classify_finish(ids, budget, eos_ids)
                    latest = {"id": row["id"], "dataset_version": row["dataset_version"], "split": row["split"],
                              "category": row["category"], "attempt": attempt, "max_new_tokens": budget,
                              "input_tokens": input_length, "output_tokens": len(ids), "finish_reason": finish,
                              "last_token_id": ids[-1] if ids else None, "generated_token_ids": ids,
                              "output": text_tokenizer.decode(ids, skip_special_tokens=True),
                              "raw_output_with_special_tokens": text_tokenizer.decode(ids, skip_special_tokens=False),
                              "rendered_prompt": rendered, "input_messages_sha256": row["input_messages_sha256"],
                              "elapsed_seconds": time.monotonic() - started}
                    attempts_file.write(json.dumps(latest, ensure_ascii=False) + "\n")
                    attempts_file.flush()
                    print(f"finished {row['id']} reason={finish} tokens={len(ids)}", flush=True)
                    if finish != "length_limit":
                        break
                latest["review_eligible"] = latest["finish_reason"] == "native_eos" and bool(latest["output"].strip())
                drafts_file.write(json.dumps(latest, ensure_ascii=False) + "\n")
                drafts_file.flush()
                (complete if latest["review_eligible"] else incomplete).append(row["id"])
        manifest.update({"status": "completed" if not incomplete else "completed_with_incomplete_rows",
                         "completed_ids": complete, "incomplete_ids": incomplete,
                         "drafts_sha256": sha256(output_dir / "drafts.jsonl"), "attempts_sha256": sha256(output_dir / "attempts.jsonl"),
                         "peak_vram_allocated_bytes": torch.cuda.max_memory_allocated(),
                         "peak_vram_reserved_bytes": torch.cuda.max_memory_reserved(),
                         "finished_at": datetime.now(timezone.utc).isoformat()})
        json_file(output_dir / "run-manifest.json", manifest)
        if incomplete:
            raise RuntimeError(f"Rows not naturally complete; do not import them: {incomplete}")
    except Exception as error:
        if manifest["status"] != "completed_with_incomplete_rows":
            manifest["status"] = "failed"
        manifest["error"] = {"type": type(error).__name__, "message": str(error)}
        json_file(output_dir / "run-manifest.json", manifest)
        raise


if __name__ == "__main__":
    main()
