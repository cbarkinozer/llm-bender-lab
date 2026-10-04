"""Read-only export of the original A/C/D queue the user actually completed."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

DATASET = 'e3b691cb-79fc-4bd8-a358-39f9a23770b5'
ANCHORS = {'me-' + x for x in ('049', '050', '059', '069', '070', '079', '089', '090')}


def summarize(rows):
    return dict(count=len(rows), preferences=dict(Counter(r['preferred'] for r in rows)),
        substance={arm: dict(Counter(r[arm] for r in rows)) for arm in 'ACD'},
        paired_pass={f'{left}_vs_{right}': {
            'left_only_pass': [r['id'] for r in rows if r[left] == 'pass' and r[right] != 'pass'],
            'right_only_pass': [r['id'] for r in rows if r[left] != 'pass' and r[right] == 'pass']}
            for left, right in [('C', 'A'), ('D', 'C'), ('D', 'A')]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    req = urllib.request.Request(f'{url}/api/v1/datasets/{DATASET}/records?limit=100&include=responses',
        headers={'X-Argilla-Api-Key': os.getenv('ARGILLA_API_KEY', 'argilla.apikey')})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    snapshot = json.loads(raw)
    assert snapshot['total'] == len(snapshot['items']) == 20
    assert len({r['external_id'] for r in snapshot['items']}) == 20
    rows = []
    for record in snapshot['items']:
        responses = record.get('responses', [])
        assert len(responses) == 1 and responses[0]['status'] == 'submitted', record['external_id']
        response = responses[0]
        values = {k: v['value'] for k, v in response['values'].items()}
        assert values['preferred'] in ('A', 'C', 'D', 'tie', 'neither')
        assert all(values[f'{arm}_substance'] in ('pass', 'partial', 'fail') for arm in 'ACD')
        notes = values.get('notes', '')
        # Parse only an explicit first-line ranking, never infer ties from matching grades.
        ranking = re.match(r'^\s*([ACD](?:\s*=\s*[ACD])+)(?:\s*>\s*[ACD])?\s*$',
                           notes.splitlines()[0] if notes else '')
        explicit = re.sub(r'\s+', '', ranking.group(0)) if ranking else None
        row = dict(id=record['external_id'], category=record['fields']['category'],
            preferred=values['preferred'], **{arm: values[f'{arm}_substance'] for arm in 'ACD'},
            notes=notes, explicit_note_ranking=explicit, response_id=response['id'],
            issues={arm: values.get(f'{arm}_issues', []) for arm in 'ACD'})
        rows.append(row)
    rows.sort(key=lambda r: r['id'])
    summary = dict(dataset_id=DATASET, exported_at=datetime.now(timezone.utc).isoformat(),
        snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        source='Original queue, explicitly chosen by user; v2 is not authoritative.',
        policy='Structured labels are primary; notes retained without overriding grades or preferences.',
        all20=summarize(rows), without_disputed089=summarize([r for r in rows if r['id'] != 'me-089']),
        high_signal8=summarize([r for r in rows if r['id'] in ANCHORS]),
        high_signal_without089=summarize([r for r in rows if r['id'] in ANCHORS - {'me-089'}]),
        explicit_tie_notes={r['id']: r['explicit_note_ranking'] for r in rows
                           if r['preferred'] == 'tie' and r['explicit_note_ranking']},
        unresolved_ties=[r['id'] for r in rows if r['preferred'] == 'tie' and not r['explicit_note_ranking']],
        preference_note_conflicts=[r['id'] for r in rows
            if r['preferred'] in 'ACD' and r['explicit_note_ranking']],
        limitations=['20 reused development items; single reviewer/seed; non-blind.',
                    'User notes may contain assistant-assisted rationale; authorship not assumed.',
                    'No global accuracy, statistical significance or forgetting claim.'])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'argilla-snapshot.json').write_bytes(raw)
    (args.output / 'per-item.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
