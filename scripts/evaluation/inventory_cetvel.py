"""Expand CETVEL task selectors with the pinned lm-eval task manager."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lm_eval.tasks import TaskManager


OFFICIAL_ALL_SELECTORS = (
    "belebele_tr",
    "exams_tr",
    "gecturk_generation",
    "ironytr",
    "mkqa_tr",
    "mlsum_tr",
    "news_cat",
    "nli_tr",
    "offenseval_tr",
    "sts_tr",
    "tquad",
    "trclaim19",
    "turkish_plu_prompt",
    "tr-wikihow-summ",
    "wiki_lingua_tr",
    "wmt-tr-en-prompt",
    "xcopa_tr",
    "xfact_tr",
    "xlsum_tr",
    "xquad_tr",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks_dir", type=Path)
    args = parser.parse_args()

    manager = TaskManager(include_path=str(args.tasks_dir.resolve()))
    inventory = {
        selector: manager.match_tasks([selector])
        for selector in OFFICIAL_ALL_SELECTORS
    }
    print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
