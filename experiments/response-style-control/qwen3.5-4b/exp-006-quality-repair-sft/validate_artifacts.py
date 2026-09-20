#!/usr/bin/env python3
"""Validate exp-006 candidates and holdout against all prior training/evaluation prompts."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).parent
PARENT = ROOT.parent / "exp-005-targeted-policy-sft"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def prior_prompts() -> list[tuple[str, str]]:
    result = []
    with (PARENT / "data" / "sft-clean-v3-targeted-858.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            result.append((f"train:{row['id']}", json.loads(row["messages"])[0]["content"]))
    for path in [PARENT / "evaluation" / "final-holdout-v1.csv", ROOT.parent / "exp-002-communication-policy-benchmark" / "test.csv"]:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle): result.append((f"eval:{row['id']}", row["prompt_tr"]))
    return result


def main() -> None:
    candidates=[json.loads(x) for x in (ROOT/"data"/"quality-repair-candidates-100.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    with (ROOT/"evaluation"/"final-holdout-v2.csv").open(encoding="utf-8",newline="") as handle: holdout=list(csv.DictReader(handle))
    assert len(candidates)==100 and len(holdout)==50
    assert len({r["id"] for r in candidates})==100 and len({r["id"] for r in holdout})==50
    assert Counter(r["category"] for r in candidates)==Counter({"hidden_ambiguity":20,"unsupported_completion":20,"turkish_precision":20,"calibrated_emotional":20,"consistency_integrity":20})
    assert Counter(r["capability_family"] for r in holdout)==Counter({"hidden_ambiguity":10,"unsupported_completion":10,"turkish_precision":10,"calibrated_emotional":10,"consistency_integrity":10})
    candidate_prompts=[(r["id"],r["messages"][0]["content"]) for r in candidates]
    holdout_prompts=[(r["id"],r["prompt_tr"]) for r in holdout]
    all_prompts=candidate_prompts+holdout_prompts
    normalized=[norm(p) for _,p in all_prompts]
    assert len(normalized)==len(set(normalized))
    prior=prior_prompts(); exact_prior={norm(p):i for i,p in prior}
    exact=[(i,exact_prior[norm(p)]) for i,p in all_prompts if norm(p) in exact_prior]
    near=[]
    for ident,prompt in all_prompts:
        for old_id,old_prompt in prior:
            score=SequenceMatcher(None,norm(prompt),norm(old_prompt)).ratio()
            if score>=0.86: near.append({"new":ident,"old":old_id,"score":round(score,4)})
    cross=[]
    for cid,cp in candidate_prompts:
        for hid,hp in holdout_prompts:
            score=SequenceMatcher(None,norm(cp),norm(hp)).ratio()
            if score>=0.82: cross.append({"candidate":cid,"holdout":hid,"score":round(score,4)})
    assert not exact, exact
    assert not near, near
    assert not cross, cross
    for row in candidates:
        assert [m["role"] for m in row["messages"]]==["user","assistant"]
        answer=row["messages"][1]["content"]
        assert answer and len(answer)<=600 and answer[-1] in ".?!"
    report={"candidate_rows":100,"holdout_rows":50,"prior_prompt_pool":len(prior),"exact_prior_overlap":len(exact),"near_prior_overlap_gte_0_86":len(near),"candidate_holdout_near_overlap_gte_0_82":len(cross),"schema":"passed"}
    (ROOT/"evaluation"/"validation-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
