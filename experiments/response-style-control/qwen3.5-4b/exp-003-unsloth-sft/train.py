#!/usr/bin/env python3
"""Reproducible bf16-LoRA SFT for response-style control.

The script intentionally trains only on the frozen reviewed-v3 artifact and
fails closed if any normalized benchmark prompt occurs in a training prompt.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parent
MODEL_DIR = EXPERIMENT_DIR.parent
DEFAULT_CONFIG = EXPERIMENT_DIR / "config.yaml"
DEFAULT_TRAIN_CSV = MODEL_DIR / "exp-001-sft-dataset" / "reviewed-v3" / "accepted-reviewed.csv"
DEFAULT_BENCHMARK_CSV = MODEL_DIR / "exp-002-communication-policy-benchmark" / "test.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_and_validate(train_path: Path, benchmark_path: Path, allow_overlap: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not train_path.is_file():
        raise FileNotFoundError(f"Training data not found: {train_path}")
    if not benchmark_path.is_file():
        raise FileNotFoundError(f"Benchmark not found: {benchmark_path}")

    raw_rows = read_csv(train_path)
    if len(raw_rows) != 2442:
        raise ValueError(f"Expected frozen v1 training data to contain 2442 rows, found {len(raw_rows)}")
    required_columns = {"id", "messages", "category", "quality_status"}
    if missing := required_columns - set(raw_rows[0]):
        raise ValueError(f"Training CSV missing columns: {sorted(missing)}")

    examples: list[dict[str, Any]] = []
    ids: set[str] = set()
    user_prompts: list[str] = []
    pair_keys: set[tuple[str, str]] = set()
    for row in raw_rows:
        if row["quality_status"] != "accepted":
            raise ValueError(f"Non-accepted row in frozen artifact: {row['id']}")
        if not row["id"] or row["id"] in ids:
            raise ValueError(f"Missing or duplicate training id: {row['id']!r}")
        ids.add(row["id"])
        try:
            messages = json.loads(row["messages"])
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid messages JSON for {row['id']}") from error
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or messages[0].get("role") != "user"
            or messages[1].get("role") != "assistant"
            or not isinstance(messages[0].get("content"), str)
            or not isinstance(messages[1].get("content"), str)
            or not messages[0]["content"].strip()
            or not messages[1]["content"].strip()
        ):
            raise ValueError(f"Expected exactly one user/assistant text pair for {row['id']}")
        pair_key = (normalize(messages[0]["content"]), normalize(messages[1]["content"]))
        if pair_key in pair_keys:
            raise ValueError(f"Duplicate normalized training pair: {row['id']}")
        pair_keys.add(pair_key)
        user_prompts.append(pair_key[0])
        examples.append({"id": row["id"], "category": row["category"], "messages": messages})

    benchmark_rows = read_csv(benchmark_path)
    benchmark_prompts = {normalize(row["prompt_tr"]) for row in benchmark_rows if row.get("prompt_tr")}
    overlaps = sorted(set(user_prompts) & benchmark_prompts)
    if overlaps and not allow_overlap:
        raise ValueError(
            "Benchmark-to-training prompt overlap detected. Refusing to train. "
            f"Examples: {overlaps[:3]}"
        )
    manifest = {
        "training_rows": len(examples),
        "training_category_counts": dict(sorted(Counter(item["category"] for item in examples).items())),
        "training_sha256": sha256(train_path),
        "benchmark_rows": len(benchmark_rows),
        "benchmark_sha256": sha256(benchmark_path),
        "normalized_prompt_overlap_count": len(overlaps),
        "train_path": str(train_path.resolve()),
        "benchmark_path": str(benchmark_path.resolve()),
    }
    return examples, manifest


def run_capture(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("PyYAML is required to load config.yaml. Install it with: pip install pyyaml") from error
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {path}")
    return config


def config_get(config: dict[str, Any], *keys: str) -> Any:
    value: Any = config
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(f"Missing required config value: {'.'.join(keys)}")
        value = value[key]
    return value


def git_snapshot() -> dict[str, Any]:
    root = run_capture(["git", "rev-parse", "--show-toplevel"])
    if root is None:
        return {"available": False}
    return {
        "available": True,
        "repository_root": root,
        "commit": run_capture(["git", "rev-parse", "HEAD"]),
        "status_porcelain": run_capture(["git", "status", "--porcelain=v1"]),
    }


def environment_snapshot() -> dict[str, Any]:
    relevant_environment = {
        key: value for key, value in os.environ.items()
        if key in {"CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "TOKENIZERS_PARALLELISM"}
        or key.startswith(("NCCL_", "CUDA_", "CUBLAS_", "TORCH_", "HF_", "TRANSFORMERS_"))
        and not any(secret in key.upper() for secret in ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "nvidia_smi": run_capture(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader"]),
        "nvidia_smi_full": run_capture(["nvidia-smi", "-q"]),
        "pip_freeze": run_capture([sys.executable, "-m", "pip", "freeze"]),
        "relevant_environment": relevant_environment,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model-name")
    parser.add_argument("--model-revision")
    parser.add_argument("--train-csv", type=Path)
    parser.add_argument("--benchmark-csv", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-seq-length", type=int)
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--per-device-batch-size", type=int)
    parser.add_argument("--gradient-accumulation-steps", type=int)
    parser.add_argument("--lora-rank", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--report-to", choices=["wandb", "none"])
    parser.add_argument("--wandb-project")
    parser.add_argument("--wandb-run-name", default=None)
    parser.add_argument(
        "--mode",
        choices=["dry-run", "representation-check", "smoke", "tiny-overfit", "full"],
        default="dry-run",
        help="Full training is allowed only after separately recorded smoke and tiny-overfit checks.",
    )
    parser.add_argument("--allow-benchmark-overlap", action="store_true")
    parser.add_argument("--allow-dirty-worktree", action="store_true")
    parser.add_argument("--smoke-run", type=Path, help="Completed smoke-run directory required for --mode full.")
    parser.add_argument("--tiny-overfit-run", type=Path, help="Completed tiny-overfit-run directory required for --mode full.")
    return parser.parse_args()


def apply_config_defaults(args: argparse.Namespace, config: dict[str, Any]) -> argparse.Namespace:
    model = config_get(config, "model")
    dataset = config_get(config, "dataset")
    evaluation = config_get(config, "evaluation")
    training = config_get(config, "training")
    tracking = config_get(config, "tracking")
    defaults = {
        "model_name": model["name"],
        "model_revision": model["revision"],
        "train_csv": (args.config.parent / dataset["path"]).resolve(),
        "benchmark_csv": (args.config.parent / evaluation["benchmark_path"]).resolve(),
        "max_seq_length": training["max_seq_length"],
        "epochs": training["epochs"],
        "learning_rate": training["learning_rate"],
        "per_device_batch_size": training["per_device_train_batch_size"],
        "gradient_accumulation_steps": training["gradient_accumulation_steps"],
        "lora_rank": training["lora"]["rank"],
        "seed": training["seed"],
        "report_to": tracking["provider"],
        "wandb_project": tracking["project"],
    }
    for name, value in defaults.items():
        if getattr(args, name) is None:
            setattr(args, name, value)
    if args.output_dir is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        args.output_dir = args.config.parent / config_get(config, "reproducibility", "output_root") / timestamp
    return args


def verify_preflight_run(path: Path | None, expected_mode: str, config_hash: str, git_commit: str | None) -> None:
    if path is None:
        raise RuntimeError(f"--mode full requires --{expected_mode}-run.")
    config_path = path / "run-config.json"
    result_path = path / "train-result.json"
    if not config_path.is_file() or not result_path.is_file():
        raise RuntimeError(f"Preflight evidence is incomplete: {path}")
    saved_config = json.loads(config_path.read_text(encoding="utf-8"))
    if saved_config.get("mode") != expected_mode or saved_config.get("config_sha256") != config_hash:
        raise RuntimeError(f"Preflight run {path} does not match the current {expected_mode} configuration.")
    saved_git = json.loads((path / "git.json").read_text(encoding="utf-8")) if (path / "git.json").is_file() else {}
    if git_commit and saved_git.get("commit") != git_commit:
        raise RuntimeError(f"Preflight run {path} used a different Git commit than the requested full run.")


def main() -> None:
    args = parse_args()
    if not args.config.is_file():
        raise FileNotFoundError(f"Experiment config not found: {args.config}")
    args.config = args.config.resolve()
    source_config = load_config(args.config)
    args = apply_config_defaults(args, source_config)
    examples, data_manifest = load_and_validate(
        args.train_csv, args.benchmark_csv, args.allow_benchmark_overlap
    )
    configured_dataset_hash = config_get(source_config, "dataset", "sha256")
    configured_benchmark_hash = config_get(source_config, "evaluation", "benchmark_sha256")
    if data_manifest["training_sha256"] != configured_dataset_hash:
        raise ValueError("Training CSV hash differs from config.yaml; create a new traceable dataset revision.")
    if data_manifest["benchmark_sha256"] != configured_benchmark_hash:
        raise ValueError("Benchmark hash differs from config.yaml; version the evaluation config before running.")
    git = git_snapshot()
    configured_allow_dirty = config_get(source_config, "reproducibility", "allow_dirty_worktree")
    if args.mode != "dry-run" and git.get("status_porcelain") and not (configured_allow_dirty or args.allow_dirty_worktree):
        raise RuntimeError(
            "Refusing a GPU run from a dirty worktree. Commit intended changes first, "
            "or use --allow-dirty-worktree only when the resulting exact diff is deliberately preserved."
        )
    configuration = {
        "experiment_id": config_get(source_config, "experiment", "id"),
        "parent": config_get(source_config, "experiment", "parent"),
        "config_path": str(args.config),
        "config_sha256": sha256(args.config),
        "model_name": args.model_name,
        "model_revision": args.model_revision,
        "tokenizer_name": config_get(source_config, "model", "tokenizer_name"),
        "tokenizer_revision": config_get(source_config, "model", "tokenizer_revision"),
        "precision": "bf16 LoRA",
        "thinking_mode": "disabled during template rendering",
        "max_seq_length": args.max_seq_length,
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "per_device_batch_size": args.per_device_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "effective_batch_size": args.per_device_batch_size * args.gradient_accumulation_steps,
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_rank,
        "seed": args.seed,
        "assistant_only_loss": True,
        "report_to": args.report_to,
        "wandb_project": args.wandb_project if args.report_to == "wandb" else None,
        "mode": args.mode,
    }
    if args.mode == "full":
        verify_preflight_run(args.smoke_run, "smoke", configuration["config_sha256"], git.get("commit"))
        verify_preflight_run(args.tiny_overfit_run, "tiny-overfit", configuration["config_sha256"], git.get("commit"))
    print(json.dumps({"data_manifest": data_manifest, "configuration": configuration, "git": git}, ensure_ascii=False, indent=2))
    if args.mode == "dry-run":
        print("Dry run passed: no model was loaded and no files were written.")
        return

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    run_name = args.wandb_run_name or output_dir.name
    if args.report_to == "wandb":
        # Transformers' W&B integration owns init/finish. These environment
        # variables make the remote run name/project explicit and reproducible.
        os.environ.setdefault("WANDB_PROJECT", args.wandb_project)
        os.environ.setdefault("WANDB_NAME", run_name)
        os.environ.setdefault("WANDB_LOG_MODEL", "false")
        try:
            import wandb  # noqa: F401
        except ImportError as error:
            raise RuntimeError(
                "W&B tracking was requested but wandb is not installed. "
                "Install it with pip install wandb, authenticate with wandb login, "
                "or pass --report-to none explicitly."
            ) from error
    write_json(output_dir / "data-manifest.json", data_manifest)
    write_json(output_dir / "run-config.json", configuration)
    write_json(output_dir / "environment.json", environment_snapshot())
    write_json(output_dir / "git.json", git)
    (output_dir / "source-config.yaml").write_bytes(args.config.read_bytes())
    if git.get("status_porcelain"):
        patch = run_capture(["git", "diff", "--binary", "HEAD"])
        if patch is not None:
            (output_dir / "working-tree.patch").write_text(patch + "\n", encoding="utf-8")

    random.seed(args.seed)
    os.environ["PYTHONHASHSEED"] = str(args.seed)

    import torch
    from datasets import Dataset
    # Unsloth patches trl's SFTConfig/SFTTrainer at import time. Importing trl
    # first binds the pre-patch classes; SFTTrainer's isinstance(args, SFTConfig)
    # check then fails against the post-patch class and silently rebuilds args
    # via to_dict(), dropping our explicit eos_token override. Unsloth must be
    # imported before trl/transformers/peft (Unsloth's own runtime warning).
    from unsloth import FastLanguageModel
    from trl import SFTConfig, SFTTrainer

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.benchmark = False
    runtime = {
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "flash_sdp_enabled": torch.backends.cuda.flash_sdp_enabled(),
        "mem_efficient_sdp_enabled": torch.backends.cuda.mem_efficient_sdp_enabled(),
        "math_sdp_enabled": torch.backends.cuda.math_sdp_enabled(),
    }
    write_json(output_dir / "runtime-backend.json", runtime)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        revision=args.model_revision,
        max_seq_length=args.max_seq_length,
        load_in_4bit=False,
        load_in_16bit=True,
        full_finetuning=False,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_rank,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
        max_seq_length=args.max_seq_length,
    )
    # Qwen3.5 is a unified VLM. Its processor reserves the positional first
    # argument for images, so SFT's text pipeline must use the nested tokenizer.
    text_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
    chat_template = tokenizer.chat_template or ""
    write_json(output_dir / "chat-template.json", {
        "tokenizer_name": config_get(source_config, "model", "tokenizer_name"),
        "tokenizer_revision": config_get(source_config, "model", "tokenizer_revision"),
        "chat_template": chat_template,
        "chat_template_sha256": hashlib.sha256(chat_template.encode("utf-8")).hexdigest(),
        "special_tokens_map": text_tokenizer.special_tokens_map,
        "thinking_mode": False,
    })

    def render(example: dict[str, Any]) -> dict[str, str]:
        # Qwen3.5 thinks by default. This explicit setting is part of the
        # experiment definition; it must match the benchmark inference setting.
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
        )
        return {"text": text}

    rendered_dataset = Dataset.from_list(examples).map(render, remove_columns=["id", "category", "messages"])
    token_lengths = [len(text_tokenizer(row["text"], add_special_tokens=False)["input_ids"]) for row in rendered_dataset]
    if max(token_lengths) > args.max_seq_length:
        raise ValueError(
            f"A rendered example has {max(token_lengths)} tokens, above max_seq_length={args.max_seq_length}. "
            "Increase --max-seq-length rather than silently truncating training data."
        )
    sorted_lengths = sorted(token_lengths)

    def percentile(percent: float) -> int:
        return sorted_lengths[round((len(sorted_lengths) - 1) * percent)]

    inspection_examples = []
    for example in examples[:5]:
        rendered = render(example)["text"]
        token_ids = text_tokenizer(rendered, add_special_tokens=False)["input_ids"]
        inspection_examples.append({
            "id": example["id"],
            "category": example["category"],
            "raw_messages": example["messages"],
            "rendered_text": rendered,
            "decoded_tokens": text_tokenizer.decode(token_ids, skip_special_tokens=False),
            "token_count": len(token_ids),
        })
    write_json(output_dir / "representation-samples.json", {"samples": inspection_examples})
    write_json(output_dir / "rendered-data-stats.json", {
        "examples": len(rendered_dataset),
        "min_tokens": min(token_lengths),
        "max_tokens": max(token_lengths),
        "mean_tokens": sum(token_lengths) / len(token_lengths),
        "median_tokens": percentile(0.50),
        "p90_tokens": percentile(0.90),
        "p95_tokens": percentile(0.95),
        "p99_tokens": percentile(0.99),
        "truncated_examples": 0,
    })

    def to_conversational(example: dict[str, Any]) -> dict[str, Any]:
        # TRL's assistant_only_loss masking requires the raw conversational
        # "messages" format (not a pre-rendered "text" string) so it can
        # locate assistant-turn token spans itself via the chat template.
        return {"messages": example["messages"], "chat_template_kwargs": {"enable_thinking": False}}

    conversational_dataset = Dataset.from_list([to_conversational(example) for example in examples])

    # Unsloth's patched SFTTrainer currently requires an explicit formatter
    # even for a conversational dataset. Keep the raw messages available so
    # TRL can derive assistant-only masks, while using the exact same pinned
    # non-thinking template used by the representation checks above.
    def formatting_func(example: dict[str, Any]) -> list[str]:
        messages = example["messages"]
        # Unsloth calls formatting_func in batched mode. Normalize both its
        # batched shape ([[messages], ...]) and the single-example shape.
        if messages and isinstance(messages[0], dict):
            messages = [messages]
        return [
            text_tokenizer.apply_chat_template(
                item,
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False,
            )
            for item in messages
        ]

    trainer_args = SFTConfig(
            output_dir=str(output_dir / "checkpoints"),
            max_length=args.max_seq_length,
            per_device_train_batch_size=args.per_device_batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            warmup_ratio=0.05,
            lr_scheduler_type="cosine",
            optim="adamw_8bit",
            logging_steps=5,
            save_strategy="steps",
            save_steps=100,
            save_total_limit=2,
            report_to=args.report_to,
            run_name=run_name,
            seed=args.seed,
            data_seed=args.seed,
            dataset_num_proc=1,
            assistant_only_loss=True,
            # Qwen3.5's processor configuration exposes a placeholder EOS to
            # newer TRL versions, while its chat template terminates turns
            # with this vocabulary token. Pin the concrete template token.
            eos_token="<|im_end|>",
            dataset_kwargs={"add_special_tokens": False},
        )
    if trainer_args.eos_token != "<|im_end|>":
        raise RuntimeError(f"Unexpected TRL EOS token: {trainer_args.eos_token!r}")
    trainer = SFTTrainer(
        model=model,
        processing_class=text_tokenizer,
        train_dataset=conversational_dataset,
        formatting_func=formatting_func,
        args=trainer_args,
    )
    trainable_parameters = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total_parameters = sum(parameter.numel() for parameter in model.parameters())
    write_json(output_dir / "model-trainability.json", {
        "trainable_parameters": trainable_parameters,
        "total_parameters": total_parameters,
        "trainable_percent": 100 * trainable_parameters / total_parameters,
    })
    dataloader = trainer.get_train_dataloader()
    first_batch = next(iter(dataloader))
    labels = first_batch.get("labels")
    if labels is None:
        raise RuntimeError("Trainer batch has no labels; assistant-only loss cannot be verified.")
    valid_target_tokens = (labels != -100).sum(dim=1).tolist()
    if any(count == 0 for count in valid_target_tokens):
        raise RuntimeError("At least one inspected batch item has zero trainable target tokens.")
    write_json(output_dir / "label-mask-inspection.json", {
        "batch_size": len(valid_target_tokens),
        "valid_target_tokens_per_item": valid_target_tokens,
        "all_items_have_trainable_target_tokens": True,
    })
    if args.mode == "representation-check":
        print(f"Representation check passed. Artifacts: {output_dir}")
        return

    if args.mode == "smoke":
        trainer.args.max_steps = 20
        trainer.args.num_train_epochs = 1
    elif args.mode == "tiny-overfit":
        tiny_examples = examples[:32]
        trainer.train_dataset = Dataset.from_list([to_conversational(example) for example in tiny_examples])
        trainer.args.max_steps = 100
        trainer.args.num_train_epochs = 20
        trainer.args.learning_rate = max(args.learning_rate, 5e-4)
    elif args.mode != "full":
        raise RuntimeError(f"Unsupported training mode: {args.mode}")
    stats = trainer.train()
    trainer.save_model(str(output_dir / "lora-adapter"))
    tokenizer.save_pretrained(str(output_dir / "lora-adapter"))
    write_json(output_dir / "train-result.json", {
        "metrics": stats.metrics,
        "gpu_memory_allocated_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
        "gpu_memory_reserved_gb": round(torch.cuda.max_memory_reserved() / 1024**3, 3),
    })
    print(f"{args.mode} run complete. LoRA adapter: {output_dir / 'lora-adapter'}")


if __name__ == "__main__":
    main()
