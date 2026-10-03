"""Freeze shared C/D data only after all twelve actual submitted human reviews."""
import copy
import argparse
import json
import os
import urllib.request
from collections import Counter
from prepare_next_pair import (HERE, D, PARENT, candidates, assemble, leakage,
    make_config, tokenize, save, sha, encoded, jsonl, load_rows)
from import_review import payload


def apply_postreview_qa(rows, approval):
    """Only two explicit, hash-bound edits; preserve submitted review provenance."""
    if (approval.get('source') != 'user-conversation' or
        approval.get('decision') != 'apply-two-scoped-postreview-corrections' or
        approval.get('reviewed_candidates_sha256') != sha(jsonl(rows)) or
        not approval.get('user_message') or not approval.get('approval_date') or
        len(approval.get('authorized_changes',[])) != 2 or
        {r['id'] for r in approval['authorized_changes']} != {'tc-005','tc-010'}):
        raise ValueError('Explicit scoped approval must bind the exact reviewed candidates')
    result = copy.deepcopy(rows)
    changes = []
    for row in result:
        before = copy.deepcopy(row)
        if row['id'] == 'tc-010':
            suffix = " 'Doktora' sözcüğünü meslek adıyla karıştırmadan yanıtla."
            if not row['messages'][0]['content'].endswith(suffix):
                raise ValueError('Expected lexical-trap hint differs')
            row['messages'][0]['content'] = row['messages'][0]['content'][:-len(suffix)]
            row['prompt_tr'] = 'user: '+row['messages'][0]['content']
            row['input_messages_sha256'] = sha(json.dumps(row['messages'],ensure_ascii=False,separators=(',',':')).encode())
            fields = ['messages','prompt_tr','input_messages_sha256']
        elif row['id'] == 'tc-005':
            old = 'görüntü gelirse sorun kablodadır.'
            new = 'görüntü gelirse eski kablo veya bağlantısı güçlü bir şüpheli olur.'
            if row['desired_answer'].count(old) != 1:
                raise ValueError('Expected categorical cable diagnosis differs')
            row['desired_answer'] = row['desired_answer'].replace(old,new)
            fields = ['desired_answer']
        else:
            continue
        row.update(answer_status='human-reviewed-with-user-authorized-qa',
            qa_approval_sha256=sha(encoded(approval)), qa_changed_fields=fields,
            parent_reviewed_candidate_sha256=sha(encoded(before)))
        changes.append(dict(id=row['id'], fields=fields,
            before={f:before[f] for f in fields}, after={f:row[f] for f in fields},
            original_review_response_id=before['review_response_id']))
    if len(changes) != 2:
        raise ValueError('Expected exactly two scoped changes')
    return result, changes


def approved_targets(records, draft):
    expected = {r['id']:r for r in draft}
    if len(records) != 12 or len({r['external_id'] for r in records}) != 12 or {r['external_id'] for r in records} != set(expected):
        raise ValueError('Missing, extra or duplicate review candidate IDs')
    approved = []
    for record in records:
        row = expected[record['external_id']]
        if record['fields'] != payload(row):
            raise ValueError('Frozen candidate fields changed: '+row['id'])
        submitted = [r for r in record.get('responses',[]) if r['status']=='submitted']
        if len(submitted) != 1:
            raise ValueError('Exactly one submitted human review required: '+row['id'])
        response = submitted[0]
        values = response['values']
        decision = values['decision']['value']
        if decision not in ('accept','rewrite'):
            raise ValueError('Rejected or unapproved candidate: '+row['id'])
        correction = (values.get('corrected_answer',{}).get('value') or '').strip()
        if decision == 'accept' and correction:
            raise ValueError('Correction supplied with accept; choose rewrite: '+row['id'])
        target = row['desired_answer'] if decision=='accept' else correction
        if not target.strip() or '\ufffd' in target or '<think>' in target or '<|im_' in target:
            raise ValueError('Empty/invalid target: '+row['id'])
        result = copy.deepcopy(row)
        result.update(desired_answer=target, review_decision=decision,
            review_response_id=response['id'], reviewed_at=response['updated_at'],
            review_provenance='argilla-submitted', review_notes=values.get('notes',{}).get('value',''),
            answer_status='human-reviewed', dataset_version='targeted-reviewed-v1')
        approved.append(result)
    return sorted(approved, key=lambda r:r['id'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qa-approval-file', type=str, help='Explicit hash-bound authority for the two agreed corrections')
    args = parser.parse_args()
    output = HERE/'data-reviewed-v1'
    if output.exists() or (HERE/'config-reviewed-v1.yaml').exists() or (D/'config-reviewed-v1.yaml').exists():
        raise ValueError('Reviewed artifacts already exist; never overwrite frozen data/config')
    info = json.loads((HERE/'annotation-link-v2.json').read_text(encoding='utf-8'))
    draft = load_rows(HERE/'data-draft-v2/candidates-12.jsonl')
    assert draft == candidates() and sha(jsonl(draft)) == info['candidate_sha256']
    req = urllib.request.Request(os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900')+
        f"/api/v1/datasets/{info['id']}/records?limit=100&include=responses",
        headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')})
    with urllib.request.urlopen(req, timeout=30) as response:
        snapshot = json.load(response)
    approved = approved_targets(snapshot['items'], draft)
    reviewed_before_qa = copy.deepcopy(approved)
    approval, changes = None, []
    if args.qa_approval_file:
        from pathlib import Path
        approval = json.loads(Path(args.qa_approval_file).read_text(encoding='utf-8'))
        if approval.get('dataset_id') != info['id'] or approval.get('snapshot_sha256') != sha(encoded(snapshot)):
            raise ValueError('Approval must bind this exact live review snapshot')
        approved, changes = apply_postreview_qa(approved, approval)
    train, validation = assemble(approved)
    leak = leakage(approved)
    leak['semantic_review'] += ' All12 user accept/rewrite reviews are present; pending text describes original draft authoring stage.'
    config_c = make_config(HERE.name, True, sha(jsonl(train)))
    config_d = make_config(D.name, True, sha(jsonl(train)))
    if approval:
        for config in (config_c,config_d):
            config['dataset']['review_status'] = '12-human-approved-argilla-plus-2-user-authorized-QA'
            config['notes'].append('Two explicit post-review edits; raw12 responses retained; see data-reviewed-v1/qa-changes.json.')
    tokenize(train+validation, HERE/'training-preflight-v1', True, config_c)
    tokenize(train+validation, D/'training-preflight-v1', True, config_d)
    for split in ('train','validation'):
        name = split+'-tokenized.jsonl'
        assert (HERE/'training-preflight-v1'/name).read_bytes() == (D/'training-preflight-v1'/name).read_bytes()
    save(output/'train-reviewed.jsonl', jsonl(train))
    save(output/'validation-reviewed.jsonl', (PARENT/'reviewed-v2/validation-reviewed.jsonl').read_bytes())
    save(output/'argilla-snapshot.json', encoded(snapshot))
    save(output/'reviewed-candidates-before-qa.jsonl', jsonl(reviewed_before_qa))
    save(output/'approved-candidates-12.jsonl', jsonl(approved))
    if approval:
        save(output/'postreview-qa-approval.json', encoded(approval))
        save(output/'qa-changes.json', encoded(changes))
    save(output/'leakage-report.json', encoded(leak))
    manifest = dict(status='human-reviewed-local-preflight-passed', training_started=False,
        retained_rows=68, new_rows=12, decisions=dict(Counter(r['review_decision'] for r in approved)),
        postreview_qa_rows=len(changes), original_argilla_annotations_unchanged=True,
        shared_training_hash=sha(jsonl(train)), original_validation_unchanged=True,
        draft_manifest_sha256=sha((HERE/'data-draft-v2/manifest.json').read_bytes()),
        files={p.name:sha(p.read_bytes()) for p in output.iterdir()})
    save(output/'manifest.json', encoded(manifest))
    save(HERE/'config-reviewed-v1.yaml', encoded(config_c))
    save(D/'config-reviewed-v1.yaml', encoded(config_d))
    print(json.dumps(manifest, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
