"""Checks shared by decision-model training; importable without a GPU stack."""
from __future__ import annotations


def compute_decision_metrics(eval_pred, gold_labels=None):
    """Trainer targets are padded probability vectors, not integer class IDs.

    Accuracy compares argmax per question. Index macro-F1 is meaningful for a
    homogeneous question schema only; mixed-schema validation uses accuracy.
    """
    import numpy as np
    from sklearn.metrics import f1_score
    logits = eval_pred.predictions
    targets = eval_pred.label_ids
    if isinstance(logits, tuple):
        logits = logits[0]
    if isinstance(targets, tuple):
        targets = targets[0]
    logits, targets = np.asarray(logits), np.asarray(targets)
    if logits.ndim != 2 or targets.ndim != 2 or logits.shape != targets.shape:
        raise ValueError(f"Expected matching question/options arrays: {logits.shape}, {targets.shape}")
    valid = (targets >= 0).any(axis=-1) & (np.maximum(targets, 0).sum(axis=-1) > 0)
    if not valid.any():
        raise ValueError("No valid decision targets")
    predictions = np.where(targets >= 0, logits, -np.inf).argmax(axis=-1)[valid]
    labels = targets.argmax(axis=-1)[valid]
    if gold_labels is not None:
        if len(gold_labels) != len(targets):
            raise ValueError("Evaluation question order/count differs from frozen gold labels")
        labels = np.asarray(gold_labels)[valid]
    return {"accuracy": float((predictions == labels).mean()),
            "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0))}


def decision_metrics_for_items(items):
    # Soft gold distributions can disagree with the explicit gold label. Preserve
    # build_dataset's labels, just as FastDecisionModel.evaluate does.
    labels = [label for item in items for label in item.get("labels", [item.get("label")])]
    if any(label is None for label in labels):
        raise ValueError("Missing explicit gold labels")
    schemas = {str(item.get("source", {}).get("questions")) for item in items}
    def metrics(prediction):
        result = compute_decision_metrics(prediction, labels)
        if len(schemas) != 1:
            # Option indices from unrelated questions are not semantic classes.
            result.pop("macro_f1")
        return result
    return metrics


def enable_existing_adapter_and_head(model):
    """Clef stores its trainable decision head under model.head."""
    adapter_tensors = 0
    for name, param in model.named_parameters():
        if any(k in name for k in ("lora_A", "lora_B", "lora_embedding_A", "lora_embedding_B")):
            param.requires_grad_(True)
            adapter_tensors += 1
    head = getattr(model, "head", None)
    if head is None:
        raise ValueError("Expected a Clef decision model with model.head")
    head.requires_grad_(True)
    if not adapter_tensors:
        raise ValueError("Existing checkpoint did not load any LoRA tensors")
    return adapter_tensors + sum(1 for _ in head.parameters())


def check_build_report(items, report, split):
    if not items or report.get("skipped", 0):
        raise ValueError(f"Invalid/empty {split} dataset: {report}")


def decision_trainer_class(base_trainer, fast_decision_model):
    """Use native decision evaluation for checkpoint selection.

    A Clef record may emit several question rows. Generic Trainer prediction
    aggregation counts dataset records, so it is unsuitable for this mixture.
    Native evaluation retains every question and its explicit gold label.
    """
    class RoutingDecisionTrainer(base_trainer):
        def evaluate(self, eval_dataset=None, ignore_keys=None, metric_key_prefix="eval", **kwargs):
            items = self.eval_dataset if eval_dataset is None else eval_dataset
            metrics = fast_decision_model.evaluate(
                self.model, self.processing_class, items,
                batch_size=self.args.per_device_eval_batch_size,
            )
            result = {f"{metric_key_prefix}_{key}": value for key, value in metrics.items()
                      if isinstance(value, (int, float))}
            if "accuracy" not in metrics:
                raise ValueError("Native decision evaluation returned no accuracy")
            self.log(result)
            self.control = self.callback_handler.on_evaluate(
                self.args, self.state, self.control, result)
            return result
    return RoutingDecisionTrainer
