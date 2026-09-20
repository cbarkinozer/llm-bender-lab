#!/usr/bin/env python3
"""Import five exp-006 candidate groups for explicit human review."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import argilla as rg

ROOT=Path(__file__).parent


def settings() -> rg.Settings:
    return rg.Settings(
        guidelines=("Review the proposed target as training data. Accept only if it is correct, natural Turkish, concise, non-repetitive, internally consistent, and contains no unsupported causal or general-principle filler. Choose rewrite for a repairable target and enter the complete replacement response. Choose reject when the prompt itself is unsuitable."),
        fields=[
            rg.TextField(name="prompt_tr",title="User prompt",use_markdown=False),
            rg.TextField(name="proposed_response",title="Proposed assistant response",use_markdown=False),
            rg.TextField(name="dominant_objective",title="Dominant repair objective",use_markdown=False),
        ],
        questions=[
            rg.LabelQuestion(name="decision",title="Training-data decision",labels=["accept","rewrite","reject"],required=True),
            rg.TextQuestion(name="rewritten_response",title="Complete replacement response (required for rewrite)",required=False,use_markdown=False),
            rg.MultiLabelQuestion(name="failure_tags",title="Problems in proposed response",labels=["incorrect_or_unsupported","missed_or_wrong_clarification","unnatural_turkish","repetition_or_filler","internal_contradiction","overcorrected_non_anthropomorphism","semantic_breakdown"],required=False),
            rg.TextQuestion(name="review_notes",title="Optional review note",required=False,use_markdown=False),
        ],
    )


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--replace",action="store_true"); args=parser.parse_args()
    client=rg.Argilla(api_url=os.getenv("ARGILLA_API_URL","http://127.0.0.1:6900"),api_key=os.getenv("ARGILLA_API_KEY","argilla.apikey"))
    rows=[json.loads(x) for x in (ROOT/"data"/"quality-repair-candidates-100.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    urls=[]
    for category in sorted({r["category"] for r in rows}):
        name=f"exp-006-{category.replace('_','-')}"; existing=client.datasets(name=name,workspace="sft-review")
        if existing is not None:
            if not args.replace: raise SystemExit(f"{name!r} already exists; use --replace intentionally")
            existing.delete()
        dataset=rg.Dataset(name=name,workspace="sft-review",settings=settings(),client=client); dataset.create()
        subset=[r for r in rows if r["category"]==category]
        dataset.records.log([rg.Record(id=r["id"],fields={"prompt_tr":r["messages"][0]["content"],"proposed_response":r["messages"][1]["content"],"dominant_objective":category}) for r in subset],batch_size=20)
        urls.append({"dataset":name,"records":len(subset),"url":f"http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode?page=1&status=pending"})
    print(json.dumps(urls,indent=2))

if __name__=="__main__": main()
