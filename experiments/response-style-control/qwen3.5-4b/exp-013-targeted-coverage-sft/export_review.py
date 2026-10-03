"""Freeze shared C/D data only after all twelve actual submitted human reviews."""
import copy
import json
import os
import urllib.request
from collections import Counter
from prepare_next_pair import (HERE, D, PARENT, candidates, assemble, leakage,
    make_config, tokenize, save, sha, encoded, jsonl, load_rows)
from import_review import payload


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
    train, validation = assemble(approved)
    leak = leakage(approved)
    leak['semantic_review'] += ' All12 user accept/rewrite reviews are present; pending text describes original draft authoring stage.'
    config_c = make_config(HERE.name, True, sha(jsonl(train)))
    config_d = make_config(D.name, True, sha(jsonl(train)))
    tokenize(train+validation, HERE/'training-preflight-v1', True, config_c)
    tokenize(train+validation, D/'training-preflight-v1', True, config_d)
    for split in ('train','validation'):
        name = split+'-tokenized.jsonl'
        assert (HERE/'training-preflight-v1'/name).read_bytes() == (D/'training-preflight-v1'/name).read_bytes()
    save(output/'train-reviewed.jsonl', jsonl(train))
    save(output/'validation-reviewed.jsonl', (PARENT/'reviewed-v2/validation-reviewed.jsonl').read_bytes())
    save(output/'argilla-snapshot.json', encoded(snapshot))
    save(output/'leakage-report.json', encoded(leak))
    manifest = dict(status='human-reviewed-local-preflight-passed', training_started=False,
        retained_rows=68, new_rows=12, decisions=dict(Counter(r['review_decision'] for r in approved)),
        shared_training_hash=sha(jsonl(train)), original_validation_unchanged=True,
        draft_manifest_sha256=sha((HERE/'data-draft-v2/manifest.json').read_bytes()),
        files={p.name:sha(p.read_bytes()) for p in output.iterdir()})
    save(output/'manifest.json', encoded(manifest))
    save(HERE/'config-reviewed-v1.yaml', encoded(config_c))
    save(D/'config-reviewed-v1.yaml', encoded(config_d))
    print(json.dumps(manifest, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
