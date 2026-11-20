#!/usr/bin/env python3
"""Fine-tune the Clef decision head on phone routing using v1 or reviewed v2 data.

Checkpoint loading strategy: RESUME (default when --reflex1-adapter is supplied).
  FastDecisionModel.from_pretrained(reflex1_checkpoint_path) loads the backbone,
  existing LoRA adapter, and decision head together. Training continues on those
  existing LoRA parameters — get_peft_model is NOT called again, which would wrap
  the adapter twice. If you need a completely fresh LoRA on top of the merged
  backbone, run with --adapter-strategy merge (requires GPU RAM for merge).

Validation split:
  A data directory with validation.jsonl uses that explicit split and checks
  IDs and template groups against training/calibration. Reviewed v2 data should
  use this path. Frozen v1 data without validation.jsonl falls back to a
  route-stratified --val-split-size carve, which is not template-group safe.
  Calibration rows are used only for probability calibration after checkpoint
  selection; they are never used as the trainer's eval_dataset.
  Test rows are never opened during training or smoke checks.

Checkpoint selection metric:
  eval_accuracy (native FastDecisionModel.evaluate on the validation split).
  Accuracy is used for checkpoint selection because higher is better semantics
  are required for load_best_model_at_end. Balanced classes do not make accuracy
  equal macro-F1; compute macro-F1 separately for the final comparison.
  If DecisionTrainer does not support compute_metrics, this will fail at smoke
  time before any GPU costs are incurred — check unsloth version.

W&B:
  Disabled for smoke runs. Pass --wandb-project to enable for actual training.
  Run ID and URL are appended to the run manifest.

Usage:
  cd /path/to/ReflexModels
  python3 /path/to/pocket-agents-lab/tools/train_phone_routing.py \\
      --data-dir /path/to/pocket-agents-lab/data/phone_routing \\
      --output-dir runs/phone-routing-v1 \\
      --reflex1-adapter experiments/unsloth-qwen35-08b-decision/runs/pod-backup/extracted/checkpoint-60 \\
      [--smoke]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

from decision_training_utils import decision_trainer_class, enable_existing_adapter_and_head, check_build_report


# ─── argument parsing ─────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir",       type=Path, required=True,
                   help="Path to phone_routing JSONL dir (train/calibration/test.jsonl)")
    p.add_argument("--output-dir",     type=Path, required=True,
                   help="Where to write checkpoints, adapter and manifests")

    # Checkpoint loading
    p.add_argument("--reflex1-adapter", type=Path, default=None,
                   help="Path to reflex-1 checkpoint dir (recommended: checkpoint-60). "
                        "Contains adapter_model.safetensors + joint_head.safetensors.")
    p.add_argument("--reflex1-adapter-sha256", type=str, default=None,
                   help="Expected SHA-256 of adapter_model.safetensors for pre-load verification")
    p.add_argument("--adapter-strategy", choices=["resume", "merge"], default="resume",
                   help="resume: continue training existing LoRA (default). "
                        "merge: merge reflex-1 LoRA into backbone then attach fresh LoRA.")
    p.add_argument("--base-model",     type=str, default="unsloth/Qwen3.5-0.8B",
                   help="HF model ID for backbone (only used when --reflex1-adapter is absent or strategy=merge)")

    # Validation split
    p.add_argument("--val-split-size", type=int, default=90,
                   help="Rows to carve from train pool for validation (stratified by route, default 90)")

    # Training
    p.add_argument("--max-steps",      type=int, default=60)
    p.add_argument("--batch-size",     type=int, default=8)
    p.add_argument("--grad-accum",     type=int, default=4)
    p.add_argument("--lr",             type=float, default=2e-4)
    p.add_argument("--lora-r",         type=int, default=16)
    p.add_argument("--lora-alpha",     type=int, default=16)
    p.add_argument("--seed",           type=int, default=3407)
    p.add_argument("--smoke",          action="store_true",
                   help="Run 2 steps on 32 examples. No test eval, no W&B.")

    # W&B
    p.add_argument("--wandb-project",  type=str, default=None,
                   help="W&B project name. If absent, W&B is disabled.")
    p.add_argument("--wandb-run-name", type=str, default=None,
                   help="W&B run name (optional, auto-generated if absent)")

    return p.parse_args()


# ─── utilities ────────────────────────────────────────────────────────────────

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sha256(path: Path, expected: str, label: str) -> None:
    actual = file_sha256(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {label}:\n  expected: {expected}\n  actual:   {actual}")
    print(f"  {label}: SHA-256 verified {actual[:16]}…")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.replace(path)


def count_trainable_params(model) -> tuple[int, int]:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    return trainable, total


# ─── validation carve ────────────────────────────────────────────────────────

def carve_validation(
    train_rows: list[dict],
    val_size: int,
    seed: int,
) -> tuple[list[dict], list[dict]]:
    """Stratified carve of val_size rows from train_rows.

    Groups by route__label, takes val_size // num_routes per group (rounded
    down), then draws the remainder at random. Returns (remaining_train, val).
    """
    rng = random.Random(seed)
    by_route: dict[str, list[dict]] = collections.defaultdict(list)
    for row in train_rows:
        by_route[row["route__label"]].append(row)

    routes = sorted(by_route.keys())
    per_route = val_size // len(routes)
    extra = val_size - per_route * len(routes)

    val_rows: list[dict] = []
    keep_rows: list[dict] = []

    for route in routes:
        pool = list(by_route[route])
        rng.shuffle(pool)
        take = per_route
        val_rows.extend(pool[:take])
        keep_rows.extend(pool[take:])

    # distribute remainder across routes
    if extra > 0:
        leftover = [r for r in keep_rows]
        rng.shuffle(leftover)
        for row in leftover[:extra]:
            keep_rows.remove(row)
            val_rows.append(row)

    return keep_rows, val_rows


# ─── integrity checks ─────────────────────────────────────────────────────────

def check_split_isolation(
    train_items: list,
    val_items: list,
    label: str = "train/val",
) -> None:
    def ids(items):
        return set(getattr(item, "id", None) or item.get("id") if hasattr(item, "get") else None
                   for item in items)

    # Fallback: compare state strings if items are dicts
    def states(items):
        result = set()
        for item in items:
            if hasattr(item, "get"):
                result.add(item.get("state") or item.get("input_ids", id(item)))
            else:
                result.add(id(item))
        return result

    overlap = ids(train_items) & ids(val_items)
    if None in overlap:
        # fall back to state comparison
        overlap = states(train_items) & states(val_items)

    if overlap:
        raise ValueError(
            f"Split isolation check FAILED: {len(overlap)} items appear in both {label} sets. "
            "This would leak validation data into training."
        )
    print(f"  Split isolation ({label}): OK — no overlap detected")


def check_label_mapping(route_names: list[str], model, tokenizer) -> None:
    # Clef scores arbitrary supplied options; its head is not a nine-class layer.
    if len(route_names) != 9 or getattr(model, "head", None) is None:
        raise ValueError("Expected nine phone routes and a loaded Clef head")
    print(f"  Schema: {len(route_names)} routes; dynamic-option Clef head present")


# FiniteLossCallback is defined inside main() after TrainerCallback is imported.
# Defining it here without the base class breaks trainer callback dispatch.


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    run_start = time.time()
    print(f"\n{'='*60}")
    print(f"train_phone_routing  seed={args.seed}  smoke={args.smoke}")
    print(f"  output: {args.output_dir}")
    print(f"{'='*60}\n")

    # ── heavy imports (GPU required) ─────────────────────────────────────────
    try:
        from unsloth import FastDecisionModel, DecisionTrainer, is_bfloat16_supported
    except ImportError:
        print("ERROR: unsloth not found. Install with: pip install unsloth[colab-new]")
        sys.exit(1)

    import math
    from datasets import Dataset
    from transformers import TrainingArguments, TrainerCallback

    class FiniteLossCallback(TrainerCallback):
        """Raise immediately on NaN/Inf loss at the first two steps."""
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs and state.global_step <= 2:
                loss = logs.get("loss")
                if loss is not None:
                    if not math.isfinite(loss):
                        raise ValueError(
                            f"Non-finite loss at step {state.global_step}: {loss}")
                    print(f"  Step {state.global_step} loss: {loss:.4f} — finite ✓")

    # ── data paths and hashes ────────────────────────────────────────────────
    train_path = args.data_dir / "train.jsonl"
    explicit_val_path = args.data_dir / "validation.jsonl"
    calib_path = args.data_dir / "calibration.jsonl"
    test_path  = args.data_dir / "test.jsonl"

    for path, label in [(train_path, "train"), (calib_path, "calibration"), (test_path, "test")]:
        if not path.exists():
            raise FileNotFoundError(f"Missing {label} data: {path}")

    train_sha = file_sha256(train_path)
    calib_sha = file_sha256(calib_path)
    test_sha  = file_sha256(test_path)

    print("Dataset hashes:")
    print(f"  train.jsonl:       {train_sha[:16]}…")
    print(f"  calibration.jsonl: {calib_sha[:16]}…")
    print(f"  test.jsonl:        {test_sha[:16]}…")

    # ── verify reflex-1 adapter hashes ──────────────────────────────────────
    if args.reflex1_adapter:
        adapter_safetensors = args.reflex1_adapter / "adapter_model.safetensors"
        if not adapter_safetensors.exists():
            raise FileNotFoundError(f"adapter_model.safetensors not found in {args.reflex1_adapter}")
        print(f"\nReflex-1 adapter: {args.reflex1_adapter}")
        if args.reflex1_adapter_sha256:
            verify_sha256(adapter_safetensors, args.reflex1_adapter_sha256, "adapter_model.safetensors")
        else:
            actual = file_sha256(adapter_safetensors)
            print(f"  adapter_model.safetensors: {actual[:16]}… (no expected hash supplied — record this)")
        reflex1_adapter_sha = file_sha256(adapter_safetensors)

    # ── load raw JSONL ───────────────────────────────────────────────────────
    def load_jsonl(path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    train_raw = load_jsonl(train_path)
    calib_raw = load_jsonl(calib_path)
    # test_raw intentionally not loaded during training — sealed

    print(f"\nRaw counts: {len(train_raw)} train, {len(calib_raw)} calibration")

    # ── carve validation from train pool ───────────────────────────────────
    if explicit_val_path.exists():
        keep_raw, val_raw = train_raw, load_jsonl(explicit_val_path)
        if not val_raw or {r["id"] for r in keep_raw} & {r["id"] for r in val_raw}:
            raise ValueError("Explicit validation must be nonempty and disjoint from training IDs")
        if {r["id"] for r in calib_raw} & ({r["id"] for r in keep_raw} | {r["id"] for r in val_raw}):
            raise ValueError("Calibration IDs overlap training or validation")
        group_path = args.data_dir / "template-groups.json"
        if group_path.exists():
            group_ids = json.loads(group_path.read_text(encoding="utf-8"))
            group_sets = [{group_ids[r["id"]] for r in rows} for rows in (keep_raw, val_raw, calib_raw)]
            if any(group_sets[i] & group_sets[j] for i, j in ((0, 1), (0, 2), (1, 2))):
                raise ValueError("Template group overlaps training, validation, or calibration")
        val_split_strategy = "explicit grouped validation.jsonl"
        print(f"Explicit validation: {len(val_raw)} val, {len(keep_raw)} train")
    else:
        keep_raw, val_raw = carve_validation(train_raw, args.val_split_size, args.seed)
        val_split_strategy = "route-stratified carve (not template-group safe)"
        print(f"Validation carve (seed={args.seed}): {len(val_raw)} val, {len(keep_raw)} train remaining")

    # verify route balance in carve
    val_routes = collections.Counter(r["route__label"] for r in val_raw)
    keep_routes = collections.Counter(r["route__label"] for r in keep_raw)
    print(f"  Val routes:   {dict(sorted(val_routes.items()))}")
    print(f"  Train routes: {dict(sorted(keep_routes.items()))}")

    # write val manifest
    val_manifest_path = args.output_dir / "val-manifest.jsonl"
    val_manifest_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in val_raw) + "\n", encoding="utf-8")
    val_sha = file_sha256(val_manifest_path)
    print(f"  Val manifest: {val_manifest_path}  sha256={val_sha[:16]}…")

    train_dataset = Dataset.from_list(keep_raw)
    val_dataset   = Dataset.from_list(val_raw)
    calib_dataset = Dataset.from_list(calib_raw)

    # ── load model ───────────────────────────────────────────────────────────
    print(f"\n{'─'*40}")
    if args.reflex1_adapter and args.adapter_strategy == "resume":
        print(f"Strategy: RESUME — loading reflex-1 from {args.reflex1_adapter}")
        print("  (existing LoRA + head used as init; get_peft_model NOT called again)")
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=str(args.reflex1_adapter),
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        # Enable gradients on the existing LoRA parameters without adding a new adapter
        n_enabled = enable_existing_adapter_and_head(model)
        checkpoint_source = str(args.reflex1_adapter)

    elif args.reflex1_adapter and args.adapter_strategy == "merge":
        print(f"Strategy: MERGE — loading base {args.base_model}, merging reflex-1, attaching fresh LoRA")
        from peft import PeftModel
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=args.base_model,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        print(f"  Loading adapter from {args.reflex1_adapter}…")
        model = PeftModel.from_pretrained(model, str(args.reflex1_adapter))
        print("  Merging and unloading…")
        model = model.merge_and_unload()
        model = FastDecisionModel.get_peft_model(
            model,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=0,
            use_gradient_checkpointing="unsloth",
            random_state=args.seed,
        )
        checkpoint_source = f"merged:{args.base_model}+{args.reflex1_adapter}"

    else:
        print(f"Strategy: SCRATCH — loading base model {args.base_model}")
        model, tokenizer = FastDecisionModel.from_pretrained(
            model_name=args.base_model,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        model = FastDecisionModel.get_peft_model(
            model,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=0,
            use_gradient_checkpointing="unsloth",
            random_state=args.seed,
        )
        checkpoint_source = args.base_model

    trainable_params, total_params = count_trainable_params(model)
    print(f"  Trainable params: {trainable_params:,} / {total_params:,} "
          f"({100*trainable_params/total_params:.2f}%)")

    # ── label mapping check ───────────────────────────────────────────────────
    route_names = sorted(set(r["route__label"] for r in train_raw))
    check_label_mapping(route_names, model, tokenizer)

    # ── build training items ──────────────────────────────────────────────────
    print(f"\nBuilding training items…")
    train_items, train_report = FastDecisionModel.build_dataset(train_dataset, tokenizer, model)
    val_items, val_report              = FastDecisionModel.build_dataset(val_dataset,   tokenizer, model)
    calib_items, calib_report            = FastDecisionModel.build_dataset(calib_dataset, tokenizer, model)

    skipped = train_report.get("skipped", 0)
    print(f"  Train items: {len(train_items)} (skipped {skipped})")
    print(f"  Val items:   {len(val_items)}")
    print(f"  Calib items: {len(calib_items)}")

    # ── split isolation check ─────────────────────────────────────────────────
    check_split_isolation(train_raw, val_raw, "train/val")

    check_build_report(train_items, train_report, "train")
    check_build_report(val_items, val_report, "validation")
    check_build_report(calib_items, calib_report, "calibration")

    # ── smoke truncation ──────────────────────────────────────────────────────
    if args.smoke:
        train_items = train_items[:32]
        val_items   = val_items[:16]
        calib_items = calib_items[:16]
        print(f"\nSmoke mode: truncated to {len(train_items)} train / {len(val_items)} val items")

    # ── baseline eval on validation ───────────────────────────────────────────
    print(f"\nBaseline eval (validation, before training)…")
    before_val = FastDecisionModel.evaluate(model, tokenizer, val_items)
    print(f"  Validation accuracy before: {before_val.get('accuracy', '?'):.4f}")
    write_json(args.output_dir / "metrics_before_val.json", before_val)

    # ── W&B setup ─────────────────────────────────────────────────────────────
    report_to = "none"
    wandb_run_id = None
    wandb_run_url = None

    if not args.smoke and args.wandb_project:
        try:
            import wandb
            run_name = args.wandb_run_name or f"phone-routing-v1-lora{args.lora_r}-s{args.seed}"
            wandb.init(project=args.wandb_project, name=run_name,
                       config=vars(args), reinit=True)
            wandb_run_id  = wandb.run.id
            wandb_run_url = wandb.run.get_url()
            report_to = "wandb"
            print(f"\nW&B: project={args.wandb_project} run={run_name} id={wandb_run_id}")
        except Exception as e:
            print(f"\nWARNING: W&B init failed ({e}). Continuing without W&B.")

    # ── train ─────────────────────────────────────────────────────────────────
    print(f"\n{'─'*40}")
    print(f"Training — max_steps={2 if args.smoke else args.max_steps}  "
          f"effective_batch={args.batch_size * args.grad_accum}")

    effective_batch = args.batch_size * args.grad_accum

    RoutingDecisionTrainer = decision_trainer_class(DecisionTrainer, FastDecisionModel)
    trainer = RoutingDecisionTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_items,
        eval_dataset=val_items,          # validation, NOT calibration
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
    print(f"\nTraining complete in {train_elapsed:.0f}s")

    # ── post-training eval on validation ─────────────────────────────────────
    print(f"\nPost-training eval (validation)…")
    after_val = FastDecisionModel.evaluate(model, tokenizer, val_items)
    print(f"  Validation accuracy after:  {after_val.get('accuracy', '?'):.4f}")
    write_json(args.output_dir / "metrics_after_val.json", after_val)

    # ── calibration (AFTER checkpoint selection, before test) ─────────────────
    # Fit temperature scaling on calibration data; save fitted config.
    # NOTE: Do not evaluate on test.jsonl here. Test is sealed.
    print(f"\nProbability calibration on calibration split…")
    calib_eval = FastDecisionModel.evaluate(model, tokenizer, calib_items)
    print(f"  Calibration accuracy (pre-calibration):  {calib_eval.get('accuracy', '?'):.4f}")
    write_json(args.output_dir / "metrics_calib_pre.json", calib_eval)

    # Temperature calibration: requires FastDecisionModel.calibrate().
    # A missing or failed calibration is NOT a silent fallback — the candidate is
    # explicitly marked uncalibrated and must not be used for final evaluation.
    calibrate_fn = getattr(FastDecisionModel, "calibrate", None)
    calibration_ok = False
    if calibrate_fn is None:
        print(
            "\n  ERROR: FastDecisionModel.calibrate() is not available in this unsloth version.\n"
            "  The checkpoint is NOT calibrated. Do not report ECE/Brier or open the\n"
            "  sealed test without completing calibration manually.\n"
            "  Upgrade unsloth or implement temperature scaling via tools/calibrate_adapter.py."
        )
        calib_config = {
            "calibrated": False,
            "method": "NOT_CALIBRATED",
            "reason": "FastDecisionModel.calibrate() not found in installed unsloth",
            "temperature": 1.0,
        }
    else:
        try:
            calib_config = calibrate_fn(model, tokenizer, calib_items)
            calib_config["calibrated"] = True
            calibration_ok = True
            print(f"  Calibration config: {calib_config}")
        except Exception as e:
            print(
                f"\n  ERROR: calibrate() raised {type(e).__name__}: {e}\n"
                "  The checkpoint is NOT calibrated. Do not open the sealed test."
            )
            calib_config = {
                "calibrated": False,
                "method": "NOT_CALIBRATED",
                "reason": f"calibrate() raised {type(e).__name__}: {e}",
                "temperature": 1.0,
            }

    write_json(args.output_dir / "calibration_config.json", calib_config)

    # ── save adapter ──────────────────────────────────────────────────────────
    adapter_dir = args.output_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print(f"\nAdapter saved to {adapter_dir}")

    # ── W&B finish ────────────────────────────────────────────────────────────
    if report_to == "wandb":
        try:
            import wandb
            wandb.finish()
        except Exception:
            pass

    # ── run manifest ─────────────────────────────────────────────────────────
    manifest = {
        "run_completed": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "smoke": args.smoke,
        "checkpoint_source": checkpoint_source,
        "adapter_strategy": args.adapter_strategy if args.reflex1_adapter else "scratch",
        "reflex1_adapter_sha256": reflex1_adapter_sha if args.reflex1_adapter else None,
        "dataset": "phone_routing_v1",
        "train_sha256": train_sha,
        "calib_sha256": calib_sha,
        "test_sha256":  test_sha,
        "val_sha256": val_sha,
        "val_split_size": len(val_raw),
        "train_after_carve": len(keep_raw),
        "seed": args.seed,
        "max_steps": 2 if args.smoke else args.max_steps,
        "effective_batch_size": 2 if args.smoke else effective_batch,
        "learning_rate": args.lr,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "trainable_params": trainable_params,
        "total_params": total_params,
        "training_elapsed_s": round(train_elapsed, 1),
        "wandb_run_id": wandb_run_id,
        "wandb_run_url": wandb_run_url,
        "metrics": {
            "before_val": before_val,
            "after_val":  after_val,
            "calib_pre":  calib_eval,
        },
        "calibration_config": calib_config,
        "calibration_ok": calibration_ok,
        "checkpoint_selection_metric": "eval_accuracy (greater is better)",
        "val_split_strategy": val_split_strategy,
    }
    write_json(args.output_dir / "run-manifest.json", manifest)

    # ── summary ──────────────────────────────────────────────────────────────
    total_elapsed = time.time() - run_start
    print(f"\n{'='*60}")
    print(f"TRAINING COMPLETE  ({total_elapsed:.0f}s total)")
    print(f"  Validation before: {before_val.get('accuracy', 0):.4f}")
    print(f"  Validation after:  {after_val.get('accuracy', 0):.4f}")
    print(f"  Calibration:       {calib_eval.get('accuracy', 0):.4f}")
    print(f"  Calibrated:        {'YES' if calibration_ok else 'NO — do not open sealed test'}")
    print(f"")
    print(f"  Test is SEALED. Run evaluate_phone_routing_model.py after")
    print(f"  candidate selection to open it.")
    print(f"  Win target: >50/90 (0.556) on test.jsonl with A32 latency <36.8s")
    print(f"")
    print(f"  Manifest: {args.output_dir}/run-manifest.json")
    print(f"  Adapter:  {adapter_dir}")
    if args.wandb_project:
        print(f"  W&B:      {wandb_run_url or 'not logged'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
