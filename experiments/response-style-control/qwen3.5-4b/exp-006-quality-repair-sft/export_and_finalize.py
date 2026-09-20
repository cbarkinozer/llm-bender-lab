#!/usr/bin/env python3
"""Export all reviewed candidates, build the exp-006 SFT artifact, and freeze config."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import argilla as rg
import yaml

ROOT=Path(__file__).parent; DATA=ROOT/"data"; EVAL=ROOT/"evaluation"
PARENT=ROOT.parent/"exp-005-targeted-policy-sft"; CAND=DATA/"quality-repair-candidates-100.jsonl"

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->None:
    candidates={r["id"]:r for r in (json.loads(x) for x in CAND.read_text(encoding="utf-8").splitlines() if x.strip())}
    client=rg.Argilla(api_url=os.getenv("ARGILLA_API_URL","http://127.0.0.1:6900"),api_key=os.getenv("ARGILLA_API_KEY","argilla.apikey"))
    reviewed=[]; incomplete=[]
    for category in sorted({r["category"] for r in candidates.values()}):
        dataset=client.datasets(name=f"exp-006-{category.replace('_','-')}",workspace="sft-review")
        for record in dataset.records:
            if str(record.status)!="completed": incomplete.append(record.id); continue
            answers={x.question_name:x.value for x in (record.responses or [])}; decision=answers.get("decision")
            rewritten=(answers.get("rewritten_response") or "").strip()
            if decision not in {"accept","rewrite","reject"}: raise ValueError(f"Missing decision: {record.id}")
            if decision=="rewrite" and not rewritten: raise ValueError(f"Rewrite has no replacement: {record.id}")
            source=candidates[record.id]; proposed=source["messages"][1]["content"]
            reviewed.append({**source,"review_decision":decision,"reviewed_response":rewritten if decision=="rewrite" else (proposed if decision=="accept" else ""),"failure_tags":answers.get("failure_tags") or [],"review_notes":answers.get("review_notes") or "","argilla_dataset_id":str(dataset.id)})
    if incomplete or len(reviewed)!=100: raise RuntimeError(f"Human review incomplete: completed={len(reviewed)} pending={len(incomplete)}")
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
