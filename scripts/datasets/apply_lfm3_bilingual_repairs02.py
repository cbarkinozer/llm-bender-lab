"""Build immutable repair revision, validate, and safely merge Argilla text edits."""
import copy
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import argilla as rg
import requests
from dotenv import load_dotenv
from tokenizers import Tokenizer

from bilingual_pilot_repairs02 import prepare_repairs

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
PILOT = BASE / 'bilingual-pilot-v01'
DEST = PILOT / 'revisions/v01-corrections-02'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    source = PILOT / 'revisions/v01-corrections-01/train.jsonl'
    if (DEST/'validation.json').exists():
        report = json.loads((DEST/'validation.json').read_text(encoding='utf-8'))
        assert report['source_sha256'] == sha(source)
        assert report['train_sha256'] == sha(DEST/'train.jsonl')
        print(json.dumps(dict(status='already applied; preserving later owner annotations', revision=str(DEST))))
        return
    originals = [json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    groups = {}
    for row in originals:
        groups.setdefault(row['group_id'], {})[row['direction']] = row
    repairs = prepare_repairs(groups)
    assert len(repairs) == 30
    eval_hashes = {p.name: sha(p) for p in (PILOT / 'eval-v01').glob('*.jsonl')}
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    key = os.getenv('ARGILLA_API_KEY', 'argilla.apikey')
    client = rg.Argilla(api_url=url, api_key=key)
    dataset = client.datasets(name='turkish-bilingual-pilot160-text-v01', workspace='sft-review')

    def fetch():
        items = []
        for offset in (0, 100):
            r = requests.get(f'{url}/api/v1/datasets/{dataset.id}/records',
                params={'limit': 100, 'offset': offset, 'include': 'responses'},
                headers={'X-Argilla-Api-Key': key}, timeout=30)
            r.raise_for_status()
            items.extend(r.json()['items'])
        assert len(items) == 160
        return {r['external_id']: r for r in items}

    snapshot = fetch()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = BASE / f'crosslingual-runtime-local/bilingual-review-backups/repairs02-{stamp}.json'
    save(backup, snapshot)
    targets, changes, conflicts = {}, [], []
    for gid, variants in groups.items():
        record = snapshot[gid]
        values = {}
        for lang in ('tr', 'en'):
            r = variants[f'{lang}-{lang}']
            values.update({lang + '_input': r['messages'][1]['content'],
                           lang + '_thinking': r.get('worked_solution') or '',
                           lang + '_output': r['messages'][-1]['content']})
        for response in record['responses']:
            for k, v in response['values'].items():
                if k in values and v['value'] != record['fields']['original_' + k]:
                    values[k] = v['value']  # Preserve saved owner edits, including drafts.
        for k, new in repairs.get(gid.removeprefix('bp01-'), {}).items():
            displayed = record['fields']['original_' + k]
            if values[k] != displayed and values[k] != new:
                conflicts.append(dict(group_id=gid, field=k, owner_value=values[k], proposed=new))
                continue
            old = values[k]
            values[k] = new
            if old != new:
                changes.append(dict(group_id=gid, field=k, before=old, after=new))
        targets[gid] = values
    # Do not claim a repair complete if it conflicts with a real owner correction.
    assert not conflicts, json.dumps(conflicts, ensure_ascii=False)
    rows = copy.deepcopy(originals)
    for r in rows:
        a, b = r['direction'].split('-')
        values = targets[r['group_id']]
        body = values[a + '_input'].rsplit('\n\n', 1)[0]
        r['messages'][1]['content'] = body + '\n\n' + r['language_instruction']['text']
        r['messages'][-1]['content'] = values[b + '_output']
        reasoning = values[b + '_thinking']
        assert bool(reasoning) == bool(r['worked_solution']), 'Reasoning presence must remain unchanged'
        r['worked_solution'] = reasoning or None
        if r != next(x for x in originals if x['id'] == r['id']):
            r['correction_revision'] = 'v01-corrections-02'
            r['quality_status'] = 'owner-authorized agent repair; not an individual owner annotation'
    DEST.mkdir(parents=True, exist_ok=True)
    for name, selected in [('train.jsonl', rows), ('train-arm-a-tr-only.jsonl', [r for r in rows if r['direction'] == 'tr-tr'])]:
        text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in selected)
        p = DEST / name
        if p.exists():
            assert p.read_text(encoding='utf-8') == text, 'Revision already exists with different content'
        else:
            p.write_text(text, encoding='utf-8', newline='\n')
    tok = Tokenizer.from_file(str(BASE / 'base-sft160-runtime-local/tokenizer/tokenizer.json'))
    lengths = []
    grouped = {}
    for r in rows:
        grouped.setdefault(r['group_id'], {})[r['direction']] = r
        assert [m['role'] for m in r['messages']] == ['system', 'user', 'assistant']
        assert r['messages'][1]['content'].strip() and r['messages'][-1]['content'].strip()
        for text in [*(m['content'] for m in r['messages']), r['worked_solution'] or '']:
            assert all(t not in text for t in ('<think>', '</think>', '<thinking>', '</thinking>', '<|im_start|>', '<|im_end|>'))
        ms = r['messages']
        prefix = f"<|startoftext|><|im_start|>system\n{ms[0]['content']}<|im_end|>\n<|im_start|>user\n{ms[1]['content']}<|im_end|>\n<|im_start|>assistant\n"
        full = prefix + '<think>' + (r['worked_solution'] or '') + '</think>' + ms[2]['content'] + '<|im_end|>\n'
        ids = tok.encode(full, add_special_tokens=False).ids
        pids = tok.encode(prefix, add_special_tokens=False).ids
        assert ids[:len(pids)] == pids and len(ids) <= 4096
        assert tok.token_to_id('<|im_end|>') in ids[len(pids):]
        lengths.append(dict(id=r['id'], total=len(ids), masked=len(pids), supervised=len(ids)-len(pids)))
    assert len(rows) == len({r['id'] for r in rows}) == 640
    for gid, variants in grouped.items():
        assert len(variants) == 4
        for d, r in variants.items():
            a, b = d.split('-')
            assert r['messages'][1]['content'].rsplit('\n\n', 1)[0] == variants[a+'-'+a]['messages'][1]['content'].rsplit('\n\n', 1)[0]
            assert r['messages'][-1]['content'] == variants[b+'-'+b]['messages'][-1]['content']
            assert r['worked_solution'] == variants[b+'-'+b]['worked_solution']
    assert sum(bool(r['worked_solution']) for r in rows) == 120
    # Fresh tasks remain independent by ID and exact normalized prompt checks.
    prompts = {' '.join(r['messages'][1]['content'].split()) for r in rows}
    checked_eval = 0
    for p in (PILOT / 'eval-v01').glob('*.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():
            ev = json.loads(line)
            if 'messages' in ev:
                for m in ev['messages']:
                    if m['role'] == 'user':
                        assert ' '.join(m['content'].split()) not in prompts
                        checked_eval += 1
    assert eval_hashes == {p.name: sha(p) for p in (PILOT / 'eval-v01').glob('*.jsonl')}
    save(DEST / 'row-token-lengths.json', lengths)
    save(DEST / 'corrections.json', dict(source_sha256=sha(source), group_count=len(repairs), changes=changes,
        eval_hashes_unchanged=eval_hashes, reasoning_presence_unchanged=True,
        files={name: sha(DEST/name) for name in ('train.jsonl', 'train-arm-a-tr-only.jsonl')}))
    # Apply to display fields and only response values still equal to their original.
    updated = []
    for gid in sorted(groups):
        record = snapshot[gid]
        values = targets[gid]
        relevant = {k: v for k, v in values.items() if record['fields']['original_'+k] != v}
        if not relevant:
            continue
        current = fetch()[gid]
        assert current['responses'] == record['responses'], 'Concurrent owner edit; rerun with a fresh revision'
        fields = dict(record['fields'])
        for k, value in relevant.items():
            fields['original_'+k] = value
        context = json.loads(fields['context'])
        context['active_revision'] = 'revisions/v01-corrections-02'
        context['repair_note'] = 'Reviewed anomalies repaired under owner authorization; prior flags retained as history, not current unresolved verdicts.'
        fields['context'] = json.dumps(context, ensure_ascii=False, indent=2)
        responses = []
        for response in record['responses']:
            for k, obj in response['values'].items():
                value = obj['value']
                if k in relevant and value == record['fields']['original_'+k]:
                    value = relevant[k]
                responses.append(rg.Response(question_name=k, value=value, user_id=response['user_id'], status=response['status']))
        dataset.records.log([rg.Record(id=gid, fields=fields, responses=responses)], batch_size=1)
        updated.append(gid)
    actual = fetch()
    for gid, old in snapshot.items():
        if gid not in updated:
            assert actual[gid]['fields'] == old['fields'] and actual[gid]['responses'] == old['responses']
            continue
        for k, v in targets[gid].items():
            assert actual[gid]['fields']['original_'+k] == v
        for prior in old['responses']:
            current = next(x for x in actual[gid]['responses'] if x['user_id'] == prior['user_id'])
            assert current['status'] == prior['status']
            expected = {k: v['value'] for k, v in prior['values'].items()}
            for k in targets[gid]:
                if k in expected and expected[k] == old['fields']['original_'+k]:
                    expected[k] = targets[gid][k]
            assert {k: v['value'] for k, v in current['values'].items()} == expected
    report = dict(status='passed', rows=640, groups=160, repaired_groups=len(repairs),
        changed_text_fields=len(changes), max_tokens=max(r['total'] for r in lengths),
        reasoning_rows=120, direct_rows=520, cross_direction_mismatches=0,
        eval_prompt_exact_checks=checked_eval, eval_unchanged=True, owner_response_statuses_preserved=True,
        argilla_updated_groups=updated, source_sha256=sha(source), train_sha256=sha(DEST/'train.jsonl'),
        limitations=['This CPU audit does not replace the GPU native-template and smoke gates.',
                    'Existing source-verification uncertainties are not certified by the repair pass.',
                    'Old experiment configs must be explicitly retargeted and token budgets recomputed before training.'])
    save(DEST/'validation.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
