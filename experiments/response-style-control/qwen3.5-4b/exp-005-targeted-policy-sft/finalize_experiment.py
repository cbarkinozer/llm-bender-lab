"""Write the runnable exp-005 config only after the reviewed dataset is frozen."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "sft-clean-v3-targeted-858.csv"
DATA_MANIFEST = HERE / "data" / "manifest.json"
HOLDOUT = HERE / "evaluation" / "final-holdout-v1.csv"
HOLDOUT_MANIFEST = HERE / "evaluation" / "manifest.json"
CONFIG = HERE / "config.yaml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data_manifest = json.loads(DATA_MANIFEST.read_text(encoding="utf-8"))
    holdout_manifest = json.loads(HOLDOUT_MANIFEST.read_text(encoding="utf-8"))
    if data_manifest.get("do_not_train") or data_manifest.get("status") != "frozen-reviewed":
        raise RuntimeError("Dataset is not frozen-reviewed; finish precision-v2 review and rebuild first")
    if data_manifest["rows"]["combined"] != 858 or sha256(DATA) != data_manifest["artifacts"]["combined"]["sha256"]:
        raise RuntimeError("Dataset count or hash differs from its manifest")
    if holdout_manifest.get("role") != "sealed-final-test":
        raise RuntimeError("Final holdout is not sealed")
    if sha256(HOLDOUT) != holdout_manifest["artifacts"]["holdout"]["sha256"]:
        raise RuntimeError("Final holdout hash differs from its manifest")

    config = {
        "experiment": {
            "id": "exp-005-targeted-policy-sft",
            "parent": "exp-004-unsloth-sft-v2",
            "status": "ready-for-preflight",
            "hypothesis": (
                "Adding a small human-reviewed targeted tranche to the unchanged 800-example core "
                "will improve missing-context clarification, typo-like near-term precision, and "
                "natural non-anthropomorphic responses without exceeding the capability budget."
            ),
        },
        "model": {
            "name": "unsloth/Qwen3.5-4B",
            "revision": "3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636",
            "tokenizer_name": "unsloth/Qwen3.5-4B",
            "tokenizer_revision": "3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636",
            "thinking_mode": False,
        },
        "dataset": {
            "path": "data/sft-clean-v3-targeted-858.csv",
            "sha256": sha256(DATA),
            "rows": 858,
            "split": "train",
            "builder_artifact": "data/manifest.json",
        },
        "evaluation": {
            "benchmark_path": "evaluation/final-holdout-v1.csv",
            "benchmark_sha256": sha256(HOLDOUT),
            "benchmark_split": "sealed-final",
            "protocol": "evaluation/scoring-rubric.md",
            "thinking_mode": False,
            "do_sample": False,
            "temperature": 0.0,
            "max_new_tokens": 256,
            "selection_policy": (
                "Do not use this holdout for data, hyperparameter, or checkpoint decisions. "
                "The exp-002 benchmark is development/diagnostic for this experiment."
            ),
        },
        "training": {
            "framework": "unsloth",
            "method": "bf16_lora_sft",
            "starting_artifact": "base-model-not-exp-004-adapter",
            "max_seq_length": 1024,
            "epochs": 3.0,
            "learning_rate": 0.0001,
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "effective_batch_size": 8,
            "optimizer": "adamw_8bit",
            "lr_scheduler_type": "cosine",
            "warmup_ratio": 0.05,
            "seed": 3407,
            "assistant_only_loss": True,
            "packing": False,
            "lora": {
                "rank": 16,
                "alpha": 16,
                "dropout": 0.0,
                "bias": "none",
                "target_modules": [
                    "q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"
                ],
            },
            "checkpointing": {"strategy": "steps", "save_steps": 100, "save_total_limit": 2},
        },
        "capability_budget": {
            "target_families": "improve",
            "overall_task_completion_max_regression_points": 2,
            "per_family_max_regression_points": 5,
            "invalid_or_nonterminating_max_increase": 0,
        },
        "tracking": {
            "provider": "wandb",
            "project": "llm-bender-lab-response-style-control",
            "log_model": False,
        },
        "reproducibility": {
            "allow_dirty_worktree": False,
            "determinism": "best_effort_cuda",
            "output_root": "results",
            "required_preflight_modes": ["representation-check", "smoke", "tiny-overfit"],
        },
    }
    rendered = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    if CONFIG.exists():
        if CONFIG.read_text(encoding="utf-8") != rendered:
            raise FileExistsError(f"Existing {CONFIG} differs; review the change instead of overwriting it")
        print(f"Already up to date: {CONFIG}")
        return
    CONFIG.write_text(rendered, encoding="utf-8")
    print(f"Wrote {CONFIG}")


if __name__ == "__main__":
    main()
