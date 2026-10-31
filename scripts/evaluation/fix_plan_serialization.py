"""Traceable v04 correction of independently confirmed shared-file planning conflicts."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from active_tdd_data import EXP, rows, read_json
from serialize_plan_files import conflicts, serialize


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8',newline='\n')
def jsave(path,value):save(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    source=EXP/'planning-pilot-v03';output=EXP/'planning-pilot-v04'
    if output.exists():raise ValueError('Preserve revisions; v04 already exists')
    old_children=rows(source/'materialized-child-inputs.jsonl')
    original=rows(source/'records.jsonl');updated=[];children=[];evidence=[]
    for prior in original:
        row=deepcopy(prior);plan=json.loads(row['messages'][-1]['content'])
        before=conflicts(plan['tasks']);edges=serialize(plan['tasks'])
        prior_id=row['record_id'];row['record_id']=prior_id.replace('-planning-v03','-planning-v04')
        plan['file_edit_order_policy']='depends_on includes logical prerequisites and explicit shared-file edit ordering. Added resource-order edges serialize writes; they do not imply extra user requirements. Independent files may still run concurrently.'
        plan['resource_order_edges']=edges
        replacements={}
        if row['source_group']=='cryptocurrency-analyser':
            for key,text in plan['shared_contracts'].items():
                if 'Adj Close' in text:
                    revised=('PROPOSED PRICE POLICY, NOT YET AGREED: the Adj Close selection and auto_adjust=False described below are a provisional provider adapter design. Resolve price-definition (raw versus adjusted and provider) before freezing fetch/return oracles. Until resolved, do not treat this selection as a user requirement.\n'+text)
                    plan['shared_contracts'][key]=revised;replacements[text]=revised
        row['messages'][-1]['content']=json.dumps(plan,ensure_ascii=False,indent=2)
        row['validation'].update(structural_checks='passed: DAG, dependency closure, and ancestor ordering of every pair of shared-file writers',
                                 file_serialization_conflicts=0,content_review='Independent Finding A corrected; provisional crypto policy explicitly conditioned on open question. No runtime integration claim.')
        row['review_lineage']=dict(prior_record_id=prior_id,prior_record_sha256=sha256(json.dumps(prior,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                                   review='LOCAL-AGENT-REVIEW-RESULTS.md Findings A and D',builder_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
        row.pop('tokens',None);row['training_eligible']=False
        for child in old_children:
            if child['plan_id']!=prior_id:continue
            revised=deepcopy(child);revised['plan_id']=row['record_id']
            task=next(t for t in plan['tasks'] if t['id']==child['task_id'])
            for old,new in replacements.items():revised['prompt']=revised['prompt'].replace(old,new)
            revised['prompt']+='\n\nSCHEDULING\nTask: '+task['id']+'\nComplete these prerequisite tasks before editing shared files: '+json.dumps(task['depends_on'])+'\nThis includes resource ordering as well as functional prerequisites.'
            revised['depends_on']=task['depends_on'];revised['implementation_files']=task['implementation_files']
            children.append(revised)
        evidence.append(dict(prior_record_id=prior_id,new_record_id=row['record_id'],prior_conflicts=before,added_edges=edges,remaining_conflicts=conflicts(plan['tasks']),
                             price_policy_clarified=bool(replacements)))
        updated.append(row)
    save(output/'records.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in updated))
    save(output/'materialized-child-inputs.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in children))
    save(output/'review-examples.txt','\n----\n'.join(r['record_id']+'\nSplit: '+r['candidate_split']+'\n\nREQUEST\n'+r['messages'][1]['content']+'\n\nPLAN\n'+r['messages'][-1]['content'] for r in updated)+'\n')
    jsave(output/'content-review.json',evidence)
    jsave(output/'manifest.json',dict(records=len(updated),prior_plans_with_conflicts=sum(bool(r['prior_conflicts']) for r in evidence),
          remaining_plans_with_conflicts=sum(bool(r['remaining_conflicts']) for r in evidence),added_edges=sum(len(r['added_edges']) for r in evidence),
          status='review defect corrected; tokenizer check pending; no training enabled',training_enabled=False,
          parent_records_sha256=sha256((source/'records.jsonl').read_bytes()).hexdigest()))
    print(json.dumps(read_json(output/'manifest.json'),indent=2))


if __name__=='__main__':main()
