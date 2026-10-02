"""Read-only Argilla snapshot and versioned reviewed targets; never modifies annotations."""
import argparse
import copy
import csv
import hashlib
import json
import os
import re
import unicodedata
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASETS = {'train': '6e0e8b05-c083-4945-815b-d38b372d5cb5',
            'validation': '6be3e4a7-a5c0-4ab0-9b05-ea56ae3b2566'}
NEW_PROMPT = 'Dünkü sunumum kötü geçti. Bu yüzden artık benimle konuşmak istemezsin, değil mi?'

def digest(value):
    return hashlib.sha256(value).hexdigest()

def normalized(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('Refusing to overwrite snapshot')
    prompts = [json.loads(line) for line in (HERE/'data-v2/prompts-100.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = {p['id']: p for p in prompts}
    raw = {}
    rows = []
    for split, dataset_id in DATASETS.items():
        req = urllib.request.Request(os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900') +
            f'/api/v1/datasets/{dataset_id}/records?limit=100&include=responses',
            headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw[split] = json.load(response)
        expected = {p['id'] for p in prompts if p['split'] == split}
        records = raw[split]['items']
        if len(records) != len(expected) or {r['external_id'] for r in records} != expected:
            raise ValueError('Wrong record identities/counts')
        for record in records:
            p = by_id[record['external_id']]
            conversation = '\n\n'.join(m['role']+': '+m['content'] for m in p['messages'])
            if record['fields']['conversation'] != conversation or record['fields']['evaluation_criteria'] != p['evaluation_criteria']:
                raise ValueError('Frozen fields changed: '+p['id'])
            submitted = [r for r in record['responses'] if r['status'] == 'submitted']
            if len(submitted) != 1:
                raise ValueError('Expected exactly one submitted review: '+p['id'])
            review = submitted[0]
            decision = review['values']['decision']['value']
            if decision not in ('accept', 'rewrite', 'reject'):
                raise ValueError('Invalid decision')
            original = record['fields']['original_answer']
            target = original if decision == 'accept' else review['values'].get('rewritten_response', {}).get('value', '')
            if decision != 'reject' and not target.strip():
                raise ValueError('Empty target: '+p['id'])
            item = copy.deepcopy(p)
            item.update(original_messages=copy.deepcopy(p['messages']), original_answer=original,
                        desired_answer=target, review_decision=decision,
                        review_notes=review['values'].get('review_notes', {}).get('value', ''),
                        review_response_id=review['id'], reviewed_at=review['updated_at'],
                        dataset_version='reviewed-v1', answer_status='human-reviewed-qa-pending',
                        loss_policy='final assistant only; all earlier turns masked',
                        evaluation_only=(split == 'validation'))
            if p['id'] == 'me-088':
                item['messages'][-1]['content'] = NEW_PROMPT
                item['prompt_tr'] = NEW_PROMPT
                item['prompt_change'] = 'User-approved wording correction; original base output belongs to original_messages only'
                item['base_comparison_eligible'] = False
            else:
                item['base_comparison_eligible'] = True
            item['parent_input_messages_sha256'] = p['input_messages_sha256']
            item['input_messages_sha256'] = digest(json.dumps(item['messages'], ensure_ascii=False, separators=(',', ':')).encode())
            rows.append(item)
    rows.sort(key=lambda r: r['id'])
    flags = []
    train = [r for r in rows if r['split'] == 'train']
    val = [r for r in rows if r['split'] == 'validation']
    for a in train:
        for b in val:
            ta = normalized('\n'.join(m['content'] for m in a['messages']))
            tb = normalized('\n'.join(m['content'] for m in b['messages']))
            tokens_a, tokens_b = set(ta.split()), set(tb.split())
            seq = SequenceMatcher(None, ta, tb).ratio()
            jac = len(tokens_a & tokens_b)/len(tokens_a | tokens_b)
            if ta == tb or a['scenario_group_id'] == b['scenario_group_id'] or (a['source_path'], a['source_id']) == (b['source_path'], b['source_id']):
                raise ValueError('Cross-split overlap')
            if seq >= .60 or jac >= .45:
                flags.append({'train': a['id'], 'validation': b['id'], 'sequence': seq, 'jaccard': jac})
    args.output_dir.mkdir(parents=True)
    def write_json(name, value):
        (args.output_dir/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    for split in DATASETS:
        write_json(f'argilla-{split}-snapshot.json', raw[split])
        selected = [r for r in rows if r['split'] == split]
        (args.output_dir/f'{split}-reviewed.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in selected), encoding='utf-8', newline='\n')
        with (args.output_dir/f'{split}-reviewed.csv').open('x', encoding='utf-8-sig', newline='') as handle:
            keys = ['id','split','category','review_decision','original_answer','desired_answer','review_notes']
            writer = csv.DictWriter(handle, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(selected)
    report = dict(created_at=datetime.now(timezone.utc).isoformat(), status='exported-qa-pending',
        rows=len(rows), splits=dict(Counter(r['split'] for r in rows)),
        decisions=dict(Counter(r['review_decision'] for r in rows)),
        cross_split_pairs=1600, exact_group_source_overlap=0, near_flags=flags,
        prompt_changes=['me-088'], training_started=False,
        warning='Review artifacts are not yet training-ready; original drafts immutable; validation evaluation-only.',
        files={p.name:digest(p.read_bytes()) for p in args.output_dir.iterdir()})
    write_json('manifest.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
