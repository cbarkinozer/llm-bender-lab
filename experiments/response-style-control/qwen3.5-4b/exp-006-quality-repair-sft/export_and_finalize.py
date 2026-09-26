#!/usr/bin/env python3
"""Export all reviewed candidates, build the exp-006 SFT artifact, and freeze config."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT=Path(__file__).parent; DATA=ROOT/"data"; EVAL=ROOT/"evaluation"
PARENT=ROOT.parent/"exp-005-targeted-policy-sft"; CAND=DATA/"quality-repair-candidates-100.jsonl"
PARTIAL=DATA/"partial-reviews"

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def load_review_exports(candidates: dict[str, dict]) -> list[dict]:
    """Load the durable category exports and bind them to the frozen candidates."""
    reviewed=[]
    for path in sorted(PARTIAL.glob("*-reviewed-20.jsonl")):
        rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows)!=20:
            raise ValueError(f"Expected 20 rows in {path}, found {len(rows)}")
        reviewed.extend(rows)

    expected_ids=set(candidates); reviewed_ids=[row.get("id") for row in reviewed]
    if len(reviewed_ids)!=100 or set(reviewed_ids)!=expected_ids or len(set(reviewed_ids))!=100:
        missing=sorted(expected_ids-set(reviewed_ids)); unexpected=sorted(set(reviewed_ids)-expected_ids)
        raise RuntimeError(
            f"Review exports do not cover the candidate pool exactly: rows={len(reviewed_ids)} "
            f"unique={len(set(reviewed_ids))} missing={missing} unexpected={unexpected}"
        )

    source_fields=("id","category","messages","source","generation_method","language","quality_status")
    for row in reviewed:
        source=candidates[row["id"]]
        if any(row.get(field)!=source.get(field) for field in source_fields):
            raise ValueError(f"Reviewed source differs from frozen candidate: {row['id']}")
        decision=row.get("review_decision")
        response=(row.get("reviewed_response") or "").strip()
        if decision not in {"accept","rewrite","reject"}:
            raise ValueError(f"Missing or invalid decision: {row['id']}")
        if decision!="reject" and not response:
            raise ValueError(f"Accepted review has no target response: {row['id']}")
        if decision=="reject" and response:
            raise ValueError(f"Rejected review unexpectedly has a target response: {row['id']}")
    return sorted(reviewed,key=lambda row:row["id"])

def main()->None:
    candidates={r["id"]:r for r in (json.loads(x) for x in CAND.read_text(encoding="utf-8").splitlines() if x.strip())}
    reviewed=load_review_exports(candidates)
    accepted=[r for r in reviewed if r["review_decision"]!="reject"]
    if len(accepted)<80: raise RuntimeError(f"Too many rejects for the planned tranche: accepted={len(accepted)}")
    review_path=DATA/"quality-repair-reviewed-100.jsonl"
    with review_path.open("w",encoding="utf-8") as h:
        for r in reviewed: h.write(json.dumps(r,ensure_ascii=False)+"\n")
    parent_rows=list(csv.DictReader((PARENT/"data"/"sft-clean-v3-targeted-858.csv").open(encoding="utf-8",newline="")))
    new_rows=[]
    for r in accepted:
        messages=[r["messages"][0],{"role":"assistant","content":r["reviewed_response"]}]
        new_rows.append({"id":r["id"],"messages":json.dumps(messages,ensure_ascii=False),"category":f"repair_{r['category']}","task_type":"quality_repair","difficulty":"mixed","language":"tr","source":"project-internal-quality-repair","source_id":r["id"],"generator_model":"project-agent-human-reviewed","generation_prompt_version":"exp006-data-spec-v1","quality_method":"argilla-human-review","quality_status":"accepted","license":"project-internal-draft","split":"train","notes":"exp-006 corrective tranche"})
    fields=list(parent_rows[0]); bycat=defaultdict(list)
    for row in new_rows: bycat[row["category"]].append(row)
    prefix=[]
    for i in range(6):
        for category in sorted(bycat):
            if i<len(bycat[category]): prefix.append(bycat[category][i])
    used={r["id"] for r in prefix}; combined=prefix+parent_rows[:2]+parent_rows[2:]+[r for r in new_rows if r["id"] not in used]
    out=DATA/f"sft-clean-v4-quality-repair-{len(combined)}.csv"
    with out.open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(combined)
    holdout=EVAL/"final-holdout-v2.csv"
    manifest={"status":"frozen-reviewed","rows":{"parent":len(parent_rows),"reviewed":len(reviewed),"accepted":len(accepted),"rejected":len(reviewed)-len(accepted),"combined":len(combined)},"decisions":dict(Counter(r["review_decision"] for r in reviewed)),"accepted_categories":dict(Counter(r["category"] for r in accepted)),"artifacts":{"candidates":{"sha256":sha(CAND)},"review_export":{"path":review_path.name,"sha256":sha(review_path)},"combined":{"path":out.name,"sha256":sha(out)},"holdout":{"path":str(holdout.relative_to(ROOT)),"sha256":sha(holdout)}},"tiny_overfit_prefix":"first 30 rows contain six accepted examples per repair family when no family has >14 rejects; next two rows are parent core"}
    (DATA/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    base=yaml.safe_load((PARENT/"config.yaml").read_text(encoding="utf-8")); base["experiment"]={"id":"exp-006-quality-repair-sft","parent":"exp-005-targeted-policy-sft","status":"ready-for-preflight","hypothesis":"A human-reviewed quality-repair tranche reduces hidden-assumption, unsupported-completion, Turkish-integrity, emotional-calibration, and semantic-consistency failures while preserving exp-005 surface-policy gains."}; base["dataset"].update({"path":f"data/{out.name}","sha256":sha(out),"rows":len(combined),"builder_artifact":"data/manifest.json"}); base["evaluation"].update({"benchmark_path":"evaluation/final-holdout-v2.csv","benchmark_sha256":sha(holdout),"protocol":"evaluation/scoring-rubric.md","selection_policy":"Sealed final test; do not use for data, recipe, hyperparameter, or checkpoint decisions. Exp-005 final holdout is development/diagnostic."}); config=ROOT/"config.yaml"; rendered=yaml.safe_dump(base,sort_keys=False,allow_unicode=True)
    if config.exists() and config.read_text(encoding="utf-8")!=rendered: raise FileExistsError("Existing config differs; do not overwrite silently")
    config.write_text(rendered,encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
