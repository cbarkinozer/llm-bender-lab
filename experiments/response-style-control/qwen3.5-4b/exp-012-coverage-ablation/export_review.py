"""Read-only Argilla export; freeze B only after all 24 accept/rewrite reviews."""
import copy
import argparse
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

from prepare_pair import (HERE, PARENT, candidates, original, audit, load_rows,
    make_config, tokenize, save, encoded, jsonl, sha)

def approved_targets(records, draft, approval=None):
    expected={r['id']:r for r in draft}
    if len(records)!=24 or {r['external_id'] for r in records}!=set(expected):
        raise ValueError('Missing, extra or duplicate candidate IDs')
    if approval is not None:
        if (approval.get('decision')!='accept-all-as-is' or
            approval.get('source')!='user-conversation' or
            approval.get('candidate_sha256')!=sha(jsonl(draft)) or
            len(approval.get('candidate_ids',[]))!=24 or
            set(approval.get('candidate_ids',[]))!=set(expected) or
            not approval.get('user_message') or not approval.get('approval_date')):
            raise ValueError('Explicit approval must bind all 24 exact draft candidates')
        if any(record['responses'] for record in records):
            raise ValueError('Existing annotation responses must be resolved; do not override them with blanket approval')
    targets={}
    for record in records:
        row=expected[record['external_id']]
        fields=dict(conversation='\n\n'.join(m['role']+': '+m['content'] for m in row['messages']),
            proposed_answer=row['desired_answer'],substance_check=row['evaluation_criteria'],
            category=row['category'],replacement=row['replaces_id'])
        if record['fields']!=fields:
            raise ValueError('Frozen candidate fields changed: '+row['id'])
        submitted=[r for r in record['responses'] if r['status']=='submitted']
        if approval is None and len(submitted)!=1:
            raise ValueError('Exactly one submitted human review required: '+row['id'])
        response=submitted[0] if submitted else None
        values=response['values'] if response else {'decision':{'value':'accept'}}
        decision=values['decision']['value']
        if decision not in ['accept','rewrite']:
            raise ValueError('Rejected/unapproved row must be resolved before training: '+row['id'])
        correction=values.get('corrected_answer',{}).get('value','') or ''
        if decision=='accept' and correction.strip():
            raise ValueError('Correction supplied with accept; choose rewrite: '+row['id'])
        target=row['desired_answer'] if decision=='accept' else correction.strip()
        if not target or '\ufffd' in target or '<think>' in target or '<|im_' in target:
            raise ValueError('Invalid/empty target: '+row['id'])
        approved=copy.deepcopy(row)
        approved.update(desired_answer=target,review_decision=decision,
            review_response_id=response['id'] if response else None,
            reviewed_at=response['updated_at'] if response else approval['approval_date'],
            review_provenance='argilla-submitted' if response else 'user-conversation-approval',
            review_notes=values.get('notes',{}).get('value',''),
            answer_status='human-reviewed',dataset_version='coverage-reviewed-v1')
        targets[row['replaces_id']]=approved
    return targets

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-file',type=Path,
        help='Explicit hash-bound user approval record; only when Argilla has no responses')
    args=parser.parse_args()
    output=HERE/'data-reviewed-v1'
    if output.exists():
        raise ValueError('Reviewed output already exists; never overwrite frozen review')
    info=json.loads((HERE/'annotation-link.json').read_text(encoding='utf-8'))
    draft=load_rows(HERE/'data-draft-v1/candidates-24.jsonl')
    assert draft==candidates() and sha(jsonl(draft))==info['candidate_sha256']
    req=urllib.request.Request(os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')+
        f"/api/v1/datasets/{info['id']}/records?limit=100&include=responses",
        headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')})
    with urllib.request.urlopen(req,timeout=30) as response:
        snapshot=json.load(response)
    approval=json.loads(args.approval_file.read_text(encoding='utf-8')) if args.approval_file else None
    mapping=approved_targets(snapshot['items'],draft,approval)  # No implicit approval fallback.
    train,validation=original()
    reviewed=[mapping.get(r['id'],r) for r in train]
    assert len(reviewed)==80 and sum(r['id'].startswith('me-') for r in reviewed)==56
    leak=audit(list(mapping.values()),train,validation)
    config=make_config(HERE.name,False,sha(jsonl(reviewed)))
    config['status']='prepared-needs-gpu-gates'
    config['dataset'].update(review_required=False,review_status=(
        '24-human-approved-conversation' if approval else '24-human-approved-argilla'))
    # CPU roundtrip first; failure cannot produce a trainable report or reviewed config.
    report=tokenize(reviewed+validation,HERE/'training-preflight-v1',True,config)
    save(output/'train-reviewed.jsonl',jsonl(reviewed))
    save(output/'validation-reviewed.jsonl',(PARENT/'reviewed-v2/validation-reviewed.jsonl').read_bytes())
    save(output/'argilla-snapshot.json',encoded(snapshot))
    if approval:
        save(output/'user-approval.json',encoded(approval))
    save(output/'leakage-report.json',encoded(leak))
    manifest=dict(status='human-reviewed-local-preflight-passed',retained_rows=56,new_rows=24,
        decisions=dict(Counter(r['review_decision'] for r in mapping.values())),
        validation_unchanged=True,training_started=False,
        approval_source='user-conversation' if approval else 'argilla-submitted',
        draft_manifest_sha256=sha((HERE/'data-draft-v1/manifest.json').read_bytes()),
        files={p.name:sha(p.read_bytes()) for p in output.iterdir()})
    save(output/'manifest.json',encoded(manifest))
    save(HERE/'config-reviewed-v1.yaml',encoded(config))
    original()
    print(json.dumps(dict(status=manifest['status'],target_tokens=report['split_stats']['train']['target'],
        next='Review exported changes, commit frozen source, then obtain GPU gates; no training launched.'),indent=2))

if __name__=='__main__':
    main()
