#!/usr/bin/env python3
"""Task-native scoring for evaluate_cetvel_generation_vllm.py output.

Run in the CETVEL venv (has sacrebleu, rouge-score already installed), not
the vLLM venv -- this reads samples.jsonl produced by the generation script
and never touches the GPU.

Per-task metrics:
- gecturk: exact match (normalized) + a format-failure heuristic tagging
  unchanged/empty/verbose outputs, separate from semantic correctness. This
  heuristic is a *candidate flag for manual review*, not a substitute for
  the four-way manual taxonomy (correct-but-different / over-correction /
  under-correction / meaning-changed) required for anything scored wrong.
- tquad / xquad_tr: SQuAD-style EM/F1 (standard normalization: lowercase,
  strip punctuation, collapse whitespace) plus answerability breakdown
  (gold-answerable vs. gold-unanswerable, crossed with whether the model's
  output looks like an attempted answer or a refusal/unanswerable marker).
  A low EM with high F1 is reported explicitly since it usually means
  boundary/normalization mismatch, not comprehension failure.
- wmt_en_tr: corpus + per-item sentence BLEU and chrF via sacrebleu.
- mlsum_tr: ROUGE-1/2/L/Lsum via rouge-score, per item and aggregate.
  Reported explicitly as a reference-overlap signal, not a faithfulness
  measure -- faithfulness requires the manual stratified read this script
  sets up sampling for.

Every task's output also includes a stratified sample selection (by score
band, truncation, and source length) to make the required manual review
pass easy to run without re-deriving which items to look at.
"""

from __future__ import annotations

import argparse
import json
import re
import string
from pathlib import Path

UNANSWERABLE_MARKERS = {"cevaplanamaz", "unanswerable"}


def load_samples(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stratified_sample(rows: list[dict], score_key: str, n_per_band: int = 5) -> dict:
    scored = [r for r in rows if score_key in r]
    scored.sort(key=lambda r: r[score_key])
    n = len(scored)
    bands = {
        "lowest_score": [r["index"] for r in scored[:n_per_band]],
        "highest_score": [r["index"] for r in scored[-n_per_band:]] if n >= n_per_band else [],
        "truncated": [r["index"] for r in rows if r.get("hit_max_new_tokens")][:n_per_band],
    }
    by_len = sorted(rows, key=lambda r: len(r.get("semantic_prompt", "")))
    bands["shortest_source"] = [r["index"] for r in by_len[:n_per_band]]
    bands["longest_source"] = [r["index"] for r in by_len[-n_per_band:]]
    return bands


# --- GEC -------------------------------------------------------------------

def normalize_gec(text: str) -> str:
    return " ".join(text.strip().split())


def score_gecturk(rows: list[dict]) -> dict:
    for r in rows:
        source = normalize_gec(r["document"]["source"])
        target = normalize_gec(r["target"])
        pred = normalize_gec(r["raw_output"])
        r["exact_match"] = int(pred == target)
        r["unchanged_from_source"] = int(pred == source)
        r["empty_output"] = int(len(pred) == 0)
        r["verbose_output"] = int(len(pred) > 2 * max(len(source), 1))
        r["format_failure_candidate"] = int(r["empty_output"] or r["verbose_output"] or r["unchanged_from_source"])

    n = len(rows)
    exact = sum(r["exact_match"] for r in rows)
    format_failures = sum(r["format_failure_candidate"] for r in rows)
    unchanged = sum(r["unchanged_from_source"] for r in rows)
    empty = sum(r["empty_output"] for r in rows)
    verbose = sum(r["verbose_output"] for r in rows)
    truncated = sum(r.get("hit_max_new_tokens", False) for r in rows)

    wrong_not_format_failure = [r["index"] for r in rows if not r["exact_match"] and not r["format_failure_candidate"]]

    return {
        "n_items": n,
        "exact_match_rate": exact / n,
        "unchanged_from_source_rate": unchanged / n,
        "empty_output_rate": empty / n,
        "verbose_output_rate": verbose / n,
        "format_failure_candidate_rate": format_failures / n,
        "truncation_rate": truncated / n,
        "note": "exact_match alone understates valid alternative corrections -- every wrong-and-not-format-failure item needs the manual four-way taxonomy pass (correct-but-different / over-correction / under-correction / meaning-changed)",
        "manual_review_needed_indices": wrong_not_format_failure,
        "stratified_sample": stratified_sample(rows, "exact_match"),
    }


# --- SQuAD-style EM/F1 (standard normalization) -----------------------------

_ARTICLES_RE = re.compile(r"\b(a|an|the)\b", re.UNICODE)
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_WS_RE = re.compile(r"\s+")


def normalize_squad(text: str) -> str:
    text = text.lower()
    text = _ARTICLES_RE.sub(" ", text)
    text = text.translate(_PUNCT_TABLE)
    text = _WS_RE.sub(" ", text).strip()
    return text


def f1_score(pred: str, gold: str) -> float:
    pred_tokens = normalize_squad(pred).split()
    gold_tokens = normalize_squad(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = {}
    for t in pred_tokens:
        common[t] = min(pred_tokens.count(t), gold_tokens.count(t))
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def is_refusal_style(text: str) -> bool:
    norm = normalize_squad(text)
    return norm in UNANSWERABLE_MARKERS or len(norm) == 0


def score_squad_task(rows: list[dict]) -> dict:
    for r in rows:
        gold_answers = r["target"]["answers"]["text"]
        gold_is_answerable = len(gold_answers) > 0
        pred = r["raw_output"].strip()
        if gold_is_answerable:
            em = max(int(normalize_squad(pred) == normalize_squad(g)) for g in gold_answers)
            f1 = max(f1_score(pred, g) for g in gold_answers)
        else:
            em = int(is_refusal_style(pred))
            f1 = float(em)
        r["exact_match"] = em
        r["f1"] = f1
        r["gold_is_answerable"] = gold_is_answerable
        r["predicted_refusal_style"] = is_refusal_style(pred)
        r["answerability_correct"] = int(gold_is_answerable != r["predicted_refusal_style"])
        r["low_em_high_f1"] = int(em == 0 and f1 >= 0.5)

    n = len(rows)
    answerable = [r for r in rows if r["gold_is_answerable"]]
    unanswerable = [r for r in rows if not r["gold_is_answerable"]]
    truncated = sum(r.get("hit_max_new_tokens", False) for r in rows)

    def _rate(sub: list[dict], key: str) -> float | None:
        return (sum(r[key] for r in sub) / len(sub)) if sub else None

    return {
        "n_items": n,
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
        "exact_match": sum(r["exact_match"] for r in rows) / n,
        "f1": sum(r["f1"] for r in rows) / n,
        "answerability_accuracy": sum(r["answerability_correct"] for r in rows) / n,
        "exact_match_on_answerable": _rate(answerable, "exact_match"),
        "f1_on_answerable": _rate(answerable, "f1"),
        "exact_match_on_unanswerable": _rate(unanswerable, "exact_match"),
        "truncation_rate": truncated / n,
        "low_em_high_f1_rate": sum(r["low_em_high_f1"] for r in rows) / n,
        "note": "low_em_high_f1 items usually indicate boundary/normalization mismatch (extra/missing words around a correct span), not a comprehension failure -- inspect these separately from genuine wrong answers",
        "low_em_high_f1_indices": [r["index"] for r in rows if r["low_em_high_f1"]],
        "stratified_sample": stratified_sample(rows, "f1"),
    }


# --- Translation (BLEU/chrF via sacrebleu) -----------------------------------

def score_translation(rows: list[dict]) -> dict:
    import sacrebleu

    hyps = [r["raw_output"].strip() for r in rows]
    refs = [r["target"] for r in rows]
    for r, hyp, ref in zip(rows, hyps, refs):
        r["sentence_bleu"] = sacrebleu.sentence_bleu(hyp, [ref]).score
        r["sentence_chrf"] = sacrebleu.sentence_chrf(hyp, [ref]).score

    corpus_bleu = sacrebleu.corpus_bleu(hyps, [refs]).score
    corpus_chrf = sacrebleu.corpus_chrf(hyps, [refs]).score
    truncated = sum(r.get("hit_max_new_tokens", False) for r in rows)

    return {
        "n_items": len(rows),
        "corpus_bleu": corpus_bleu,
        "corpus_chrf": corpus_chrf,
        "mean_sentence_bleu": sum(r["sentence_bleu"] for r in rows) / len(rows),
        "mean_sentence_chrf": sum(r["sentence_chrf"] for r in rows) / len(rows),
        "truncation_rate": truncated / len(rows),
        "note": "this is the EN->TR direction (CETVEL's task is misleadingly named wmt-tr-en-prompt) -- a direct test of Turkish generation quality, not a TR comprehension check",
        "stratified_sample": stratified_sample(rows, "sentence_bleu"),
    }


# --- Summarization (ROUGE via rouge-score) -----------------------------------

def score_summarization(rows: list[dict]) -> dict:
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL", "rougeLsum"], use_stemmer=False)
    for r in rows:
        scores = scorer.score(r["target"], r["raw_output"].strip())
        r["rouge1"] = scores["rouge1"].fmeasure
        r["rouge2"] = scores["rouge2"].fmeasure
        r["rougeL"] = scores["rougeL"].fmeasure
        r["rougeLsum"] = scores["rougeLsum"].fmeasure

    n = len(rows)
    truncated = sum(r.get("hit_max_new_tokens", False) for r in rows)

    return {
        "n_items": n,
        "mean_rouge1": sum(r["rouge1"] for r in rows) / n,
        "mean_rouge2": sum(r["rouge2"] for r in rows) / n,
        "mean_rougeL": sum(r["rougeL"] for r in rows) / n,
        "mean_rougeLsum": sum(r["rougeLsum"] for r in rows) / n,
        "truncation_rate": truncated / n,
        "note": "ROUGE is a reference-overlap signal, not a faithfulness measure -- manually inspect the stratified sample below (high/low ROUGE, truncations, longest/shortest source) before concluding anything about summary quality",
        "stratified_sample": stratified_sample(rows, "rougeL"),
    }


SCORERS = {
    "gecturk": score_gecturk,
    "tquad": score_squad_task,
    "xquad_tr": score_squad_task,
    "wmt_en_tr": score_translation,
    "mlsum_tr": score_summarization,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, choices=sorted(SCORERS))
    parser.add_argument("--samples", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    cfg = parser.parse_args()

    rows = load_samples(cfg.samples)
    result = SCORERS[cfg.task](rows)
    result = {"task": cfg.task, **result}
    write_json(cfg.output, result)

    scored_samples_path = cfg.output.with_name(cfg.output.stem + "-scored-samples.jsonl")
    with scored_samples_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_indices") and k != "stratified_sample"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
