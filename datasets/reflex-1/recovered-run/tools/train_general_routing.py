#!/usr/bin/env python3
"""Fine-tune the Clef decision head on the general routing mixture.

This is one of three independent training runs starting from the same reflex-1
checkpoint. Run prepare_general_mixture.py first to build the data directory.

Schema difference from phone routing:
  The general mixture contains three different question structures (typed-decisions,
  banking77, clinc150). FastDecisionModel.build_dataset must handle each correctly.
  Use general validation scores (not phone_routing_v1) for retention decisions.
  Reserve benchmark test scores for final reporting only.

Validation:
  train_after_carve + val rows are both from prepare_general_mixture.py output.
  The 'val.jsonl' file written by prepare_general_mixture.py is used directly —
  it was carved at preparation time with per-source stratification.
  Calibration and test are similarly pre-carved; this script does NOT re-split.

Usage:
  cd /path/to/ReflexModels
  python3 /path/to/pocket-agents-lab/tools/train_general_routing.py \\
      --data-dir /path/to/pocket-agents-lab/data/general_routing_v1 \\
      --output-dir runs/general-routing-v1 \\
      --reflex1-adapter experiments/unsloth-qwen35-08b-decision/runs/pod-backup/extracted/checkpoint-60 \\
      [--smoke]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path

from decision_training_utils import decision_trainer_class, enable_existing_adapter_and_head, check_build_report


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir",    type=Path, required=True,
                   help="Directory with train.jsonl, val.jsonl, calibration.jsonl "
                        "(output of prepare_general_mixture.py)")
    p.add_argument("--output-dir",  type=Path, required=True)
    p.add_argument("--reflex1-adapter", type=Path, default=None,
                   help="Path to reflex-1 checkpoint-60 dir (recommended)")
    p.add_argument("--reflex1-adapter-sha256", type=str, default=None)
    p.add_argument("--adapter-strategy", choices=["resume", "merge"], default="resume")
    p.add_argument("--base-model",  type=str, default="unsloth/Qwen3.5-0.8B")
    p.add_argument("--max-seq-length", type=int, default=4096,
                   help="Sequence limit; 150-option intent schemas need more than 2048 tokens")
    p.add_argument("--max-steps",   type=int, default=60)
    p.add_argument("--batch-size",  type=int, default=8)
    p.add_argument("--grad-accum",  type=int, default=4)
    p.add_argument("--lr",          type=float, default=2e-4)
    p.add_argument("--lora-r",      type=int, default=16)
    p.add_argument("--lora-alpha",  type=int, default=16)
    p.add_argument("--seed",        type=int, default=3407)
    p.add_argument("--smoke",       action="store_true")
    p.add_argument("--wandb-project",  type=str, default=None)
    p.add_argument("--wandb-run-name", type=str, default=None)
    return p.parse_args()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.replace(path)


def count_trainable_params(model) -> tuple[int, int]:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    return trainable, total


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    run_start = time.time()
    print(f"\n{'='*60}")
    print(f"train_general_routing  seed={args.seed}  smoke={args.smoke}")
    print(f"  output: {args.output_dir}")
    print(f"{'='*60}\n")

    try:
        from unsloth import FastDecisionModel, DecisionTrainer, is_bfloat16_supported
    except ImportError:
        print("ERROR: unsloth not found. pip install unsloth[colab-new]")
        sys.exit(1)

    import math
    from datasets import Dataset
    from transformers import TrainingArguments, TrainerCallback

    class FiniteLossCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs and state.global_step <= 2:
                loss = logs.get("loss")
                if loss is not None:
                    if not math.isfinite(loss):
                        raise ValueError(f"Non-finite loss at step {state.global_step}: {loss}")
                    print(f"  Step {state.global_step} loss: {loss:.4f} — finite ✓")

    # ── load pre-carved splits ─────────────────────────────────────────────────
    train_path = args.data_dir / "train.jsonl"
    val_path   = args.data_dir / "val.jsonl"
    calib_path = args.data_dir / "calibration.jsonl"
    # test is evaluated by evaluate_phone_routing_model.py after candidate selection

    for path in [train_path, val_path, calib_path]:
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path} — run prepare_general_mixture.py first")

    def load_jsonl(path: Path) -> list[dict]:
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    train_raw = load_jsonl(train_path)
    val_raw   = load_jsonl(val_path)
    calib_raw = load_jsonl(calib_path)

    train_sha = file_sha256(train_path)
    val_sha   = file_sha256(val_path)
    calib_sha = file_sha256(calib_path)

    print(f"Data: {len(train_raw)} train / {len(val_raw)} val / {len(calib_raw)} calib")
    print(f"  train sha256: {train_sha[:16]}…")

    # Per-source distribution in train
    source_counts = collections.Counter(r.get("source", "unknown") for r in train_raw)
    print(f"  Sources in train: {dict(sorted(source_counts.items()))}")

    # ── verify reflex-1 adapter ───────────────────────────────────────────────
    reflex1_adapter_sha = None
    if args.reflex1_adapter:
        adapter_sf = args.reflex1_adapter / "adapter_model.safetensors"
        if not adapter_sf.exists():
            raise FileNotFoundError(f"adapter_model.safetensors not found in {args.reflex1_adapter}")
        reflex1_adapter_sha = file_sha256(adapter_sf)
        if args.reflex1_adapter_sha256 and reflex1_adapter_sha != args.reflex1_adapter_sha256:
            raise ValueError(
                f"SHA-256 mismatch for adapter_model.safetensors:\n"
                f"  expected: {args.reflex1_adapter_sha256}\n"
                f"  actual:   {reflex1_adapter_sha}"
            )
        print(f"\nReflex-1 adapter: {reflex1_adapter_sha[:16]}… verified")

    # ── load model ────────────────────────────────────────────────────────────
    if args.reflex1_adapter and args.adapter_strategy == "resume":
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=str(args.reflex1_adapter),
            max_seq_length=args.max_seq_length, dtype=None, load_in_4bit=True,
        )
        n_enabled = enable_existing_adapter_and_head(model)
        checkpoint_source = str(args.reflex1_adapter)
        print(f"RESUME: enabled gradients on {n_enabled} LoRA/head tensors")

    elif args.reflex1_adapter and args.adapter_strategy == "merge":
        from peft import PeftModel
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=args.base_model, max_seq_length=args.max_seq_length, dtype=None, load_in_4bit=True)
        model = PeftModel.from_pretrained(model, str(args.reflex1_adapter))
        model = model.merge_and_unload()
        model = FastDecisionModel.get_peft_model(
            model, r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0,
            use_gradient_checkpointing="unsloth", random_state=args.seed)
        checkpoint_source = f"merged:{args.base_model}+{args.reflex1_adapter}"

    else:
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=args.base_model, max_seq_length=args.max_seq_length, dtype=None, load_in_4bit=True)
        model = FastDecisionModel.get_peft_model(
            model, r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0,
            use_gradient_checkpointing="unsloth", random_state=args.seed)
        checkpoint_source = args.base_model

    trainable_params, total_params = count_trainable_params(model)
    print(f"Trainable: {trainable_params:,} / {total_params:,}")

    # ── build items ──────────────────────────────────────────────────────────
    train_items, train_report = FastDecisionModel.build_dataset(
        Dataset.from_list(train_raw), tokenizer, model)
    val_items, val_report   = FastDecisionModel.build_dataset(Dataset.from_list(val_raw),   tokenizer, model)
    calib_items, calib_report = FastDecisionModel.build_dataset(Dataset.from_list(calib_raw), tokenizer, model)

    print(f"Items: {len(train_items)} train / {len(val_items)} val / {len(calib_items)} calib "
          f"(skipped {train_report.get('skipped', 0)})")

    check_build_report(train_items, train_report, "train")
    check_build_report(val_items, val_report, "validation")
    check_build_report(calib_items, calib_report, "calibration")

    if args.smoke:
        train_items = train_items[:32]
        val_items   = val_items[:16]
        calib_items = calib_items[:16]
        print("Smoke mode: truncated")

    # ── baseline eval ─────────────────────────────────────────────────────────
    before_val = FastDecisionModel.evaluate(model, tokenizer, val_items)
    print(f"Baseline val accuracy: {before_val.get('accuracy', '?'):.4f}")
    write_json(args.output_dir / "metrics_before_val.json", before_val)

    # ── W&B ──────────────────────────────────────────────────────────────────
    report_to = "none"
    wandb_run_id = wandb_run_url = None
    if not args.smoke and args.wandb_project:
        try:
            import wandb
            run_name = args.wandb_run_name or f"general-routing-v1-lora{args.lora_r}-s{args.seed}"
            wandb.init(project=args.wandb_project, name=run_name,
                       config=vars(args), reinit=True)
            wandb_run_id  = wandb.run.id
            wandb_run_url = wandb.run.get_url()
            report_to = "wandb"
        except Exception as e:
            print(f"W&B init failed ({e}). Continuing without W&B.")

    # ── train ─────────────────────────────────────────────────────────────────
    effective_batch = args.batch_size * args.grad_accum
    RoutingDecisionTrainer = decision_trainer_class(DecisionTrainer, FastDecisionModel)
    trainer = RoutingDecisionTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_items,
        eval_dataset=val_items,
        args=TrainingArguments(
            per_device_train_batch_size=2 if args.smoke else args.batch_size,
            gradient_accumulation_steps=1 if args.smoke else args.grad_accum,
            warmup_steps=0 if args.smoke else 10,
            max_steps=2 if args.smoke else args.max_steps,
            learning_rate=args.lr,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=1,
            eval_strategy="steps",
            eval_steps=2 if args.smoke else 20,
            save_strategy="steps",
            save_steps=2 if args.smoke else 20,
            load_best_model_at_end=True,
            metric_for_best_model="eval_accuracy",
            greater_is_better=True,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=args.seed,
            output_dir=str(args.output_dir / "checkpoints"),
            report_to=report_to,
        ),
        callbacks=[FiniteLossCallback()],
    )
    train_start = time.time()
    trainer.train()
    train_elapsed = time.time() - train_start

    after_val = FastDecisionModel.evaluate(model, tokenizer, val_items)
    print(f"Post-training val accuracy: {after_val.get('accuracy', '?'):.4f}")
    write_json(args.output_dir / "metrics_after_val.json", after_val)

    # ── calibration ──────────────────────────────────────────────────────────
    calib_eval = FastDecisionModel.evaluate(model, tokenizer, calib_items)
    write_json(args.output_dir / "metrics_calib_pre.json", calib_eval)

    calibration_ok = False
    calibrate_fn = getattr(FastDecisionModel, "calibrate", None)
    if calibrate_fn is None:
        calib_config = {"calibrated": False, "method": "NOT_CALIBRATED",
                        "reason": "FastDecisionModel.calibrate() not found", "temperature": 1.0}
        print("ERROR: calibrate() not available — checkpoint is NOT calibrated")
    else:
        try:
            calib_config = calibrate_fn(model, tokenizer, calib_items)
            calib_config["calibrated"] = True
            calibration_ok = True
        except Exception as e:
            calib_config = {"calibrated": False, "method": "NOT_CALIBRATED",
                            "reason": str(e), "temperature": 1.0}
            print(f"ERROR: calibrate() failed — NOT calibrated: {e}")

    write_json(args.output_dir / "calibration_config.json", calib_config)

    # ── save adapter ──────────────────────────────────────────────────────────
    adapter_dir = args.output_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    if report_to == "wandb":
        try:
            import wandb; wandb.finish()
        except Exception:
            pass

    manifest = {
        "run_completed": True,
        "dataset": "general_routing_v1",
        "checkpoint_source": checkpoint_source,
        "adapter_strategy": args.adapter_strategy if args.reflex1_adapter else "scratch",
        "reflex1_adapter_sha256": reflex1_adapter_sha,
        "train_sha256": train_sha,
        "val_sha256": val_sha,
        "calib_sha256": calib_sha,
        "source_counts_train": dict(source_counts),
        "seed": args.seed,
        "max_steps": 2 if args.smoke else args.max_steps,
        "effective_batch_size": 2 if args.smoke else effective_batch,
        "learning_rate": args.lr,
        "trainable_params": trainable_params,
        "training_elapsed_s": round(train_elapsed, 1),
        "wandb_run_id": wandb_run_id,
        "wandb_run_url": wandb_run_url,
        "metrics": {"before_val": before_val, "after_val": after_val, "calib_pre": calib_eval},
        "calibration_config": calib_config,
        "calibration_ok": calibration_ok,
        "checkpoint_selection_metric": "eval_accuracy (greater is better)",
        "retention_note": "Use general val accuracy for retention decisions; "
                          "benchmark test scores are for final reporting only.",
        "smoke": args.smoke,
    }
    write_json(args.output_dir / "run-manifest.json", manifest)

    total_elapsed = time.time() - run_start
    print(f"\n{'='*60}")
    print(f"GENERAL TRAINING COMPLETE  ({total_elapsed:.0f}s total)")
    print(f"  Val before: {before_val.get('accuracy', 0):.4f}")
    print(f"  Val after:  {after_val.get('accuracy', 0):.4f}")
    print(f"  Calibrated: {'YES' if calibration_ok else 'NO'}")
    print(f"  Adapter: {adapter_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
