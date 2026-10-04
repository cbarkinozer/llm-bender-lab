"""Read-only review export; refuse pending/rejected rows, freeze once approved."""
import copy
import json
import os
import urllib.request
from prepare_pair import HERE,ROOT,F,C,DRAFT,CONTROL_DRAFT,REPORT,HASHES,load,save,sha,encoded,jsonl,drafts,leakage,tokenize,config
from import_review import payload

def resolve(rows,snapshot,control=False):
    assert snapshot['total']==len(snapshot['items'])==len(rows)
    actual={r['external_id']:r for r in snapshot['items']}
    assert set(actual)=={r['id'] for r in rows}
    approved=[]
    for source in rows:
        record=actual[source['id']]
        assert record['fields']==payload(source,control),source['id']
        submitted=[r for r in record['responses'] if r['status']=='submitted']
        if len(submitted)!=1:
            raise ValueError(source['id']+': one submitted review required')
        response=submitted[0]; values=response['values']
        decision=values['decision']['value']
        if decision not in ('accept','rewrite'):
            raise ValueError(source['id']+': rejected; resolve with versioned question/data repair')
        answer=source['desired_answer'] if decision=='accept' else values.get('corrected_answer',{}).get('value','').strip()
        if not answer:
            raise ValueError(source['id']+': rewrite needs complete answer')
        row=copy.deepcopy(source)
        row.update(desired_answer=answer,review_decision=decision,answer_status='human-reviewed',
            review_response_id=response['id'],review_notes=values.get('notes',{}).get('value',''),
            reviewed_at=response['updated_at'])
        approved.append(row)
    return approved

def main():
    links=json.loads((HERE/'annotation-links-v2.json').read_text(encoding='utf-8'))
    report=json.loads((HERE/REPORT).read_text(encoding='utf-8'))
    for path,hash_ in report['files'].items():
        assert sha((ROOT/path).read_bytes())==hash_,path
    rows=load(HERE/DRAFT/'review-candidates.jsonl'); controls=load(HERE/CONTROL_DRAFT/'questions-12.jsonl')
    url=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900'); key=os.getenv('ARGILLA_API_KEY','argilla.apikey')
    raw={}; snapshots={}
    for kind in ('train','controls'):
        request=urllib.request.Request(f'{url}/api/v1/datasets/{links[kind]["id"]}/records?limit=100&include=responses',headers={'X-Argilla-Api-Key':key})
        with urllib.request.urlopen(request,timeout=30) as response:
            raw[kind]=response.read(); snapshots[kind]=json.loads(raw[kind])
    # All approvals must pass BEFORE writing reviewed artifacts.
    approved=resolve(rows,snapshots['train']); approved_controls=resolve(controls,snapshots['controls'],True)
    parent,e,_,validation,_,_,audit=drafts()
    fixes={r['id']:r for r in approved if r['review_kind']=='repair'}
    new=[r for r in approved if r['review_kind']=='new-train']
    for row in e:
        if row['id'] in fixes:
            reviewed=fixes[row['id']]
            row.update({k:reviewed[k] for k in ('desired_answer','review_decision','answer_status','review_response_id','review_notes','reviewed_at')},dataset_version='ef-reviewed-v1')
    f=copy.deepcopy(e)+new
    assert len(e)==80 and len(f)==104 and len(new)==24
    assert [r['messages'] for r in e]==[r['messages'] for r in parent]
    leak=leakage(parent,validation,new,approved_controls)
    assert not leak['exact_matches'] and not leak['near_flags']
    # No model outputs have been generated during this workflow; control rows
    # remain separate from training and validation loss.
    for folder,arm,train in [(HERE,'E',e),(F,'F',f)]:
        target=folder/'data-reviewed-v1'
        save(target/'train-reviewed.jsonl',jsonl(train))
        save(target/'validation-reviewed.jsonl',(C/'data-reviewed-v1/validation-reviewed.jsonl').read_bytes())
        conf=config(arm)
        conf.update(status='prepared-needs-gpu-gates')
        conf['dataset'].update(review_required=False,review_status='submitted-human-review-freeze')
        conf['dataset']['hashes']['train-reviewed.jsonl']=sha(jsonl(train))
        save(folder/'config-reviewed-v1.yaml',encoded(conf))
        tokenize(train+validation,folder/'training-preflight-v1',conf,approved=True)
    save(HERE/'controls-reviewed-v1/questions-12.jsonl',jsonl(approved_controls))
    # Control preflight carries evaluation-only records; cannot be used by runner.
    tokenize(approved_controls,HERE/'control-preflight-v1',config('E'))
    for kind,data in raw.items():
        save(HERE/'data-reviewed-v1'/f'argilla-{kind}-snapshot.json',data)
    save(HERE/'data-reviewed-v1/approved-candidates.jsonl',jsonl(approved))
    save(HERE/'data-reviewed-v1/leakage-report.json',encoded(leak))
    save(HERE/'data-reviewed-v1/manifest.json',encoded(dict(status='human-reviewed-CPU-passed-needs-GPU',
        original_hashes=HASHES,train_hashes=dict(E=sha(jsonl(e)),F=sha(jsonl(f))),
        control_sha256=sha(jsonl(approved_controls)),raw_snapshot_hashes={k:sha(v) for k,v in raw.items()},
        actual_target_changes=sum(a['desired_answer']!=b['desired_answer'] for a,b in zip(e,parent)),
        authoring_report_sha256=sha((HERE/REPORT).read_bytes()),
        control_policy='Frozen before model outputs. Never train/replay/no validation loss.12-item diagnostic, not final test.',
        training_started=False)))
    print('Human review frozen. Both experiments still need GPU checks; no training started.')

if __name__=='__main__':
    main()
