"""Publish 30 random exp-005 pilot pairs as a new local Argilla review dataset (the owner reads them before the data gate is decided).

  python publish_exp005_pair_review.py --run DIR [--dry-run] [--api-url URL] [--workspace NAME] [--name NAME] [--seed N]

DIR is the validation output folder that holds validated.jsonl and pairs-pilot.jsonl (the pairs that survived the brevity guard). The 30
pairs are a seeded sample of those pairs, `larger` repairs over-sampled (18 larger, 12 minimal). The reviewer sees the prompt, the repaired
answer (chosen), the model's own answer (rejected) and the repairer's change notes. Nothing is pre-filled. Creates a new dataset only and
aborts if the name exists. Packet and receipt stay in results-local (not in Git).
"""
import argparse
import hashlib
import json
import os
import random
from pathlib import Path

QUOTA = dict(larger=18, minimal=12)


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def text_of(messages):
    return messages[-1]['content'] if isinstance(messages, list) else messages


def build_packet(run, seed):
    validated = {(r['prompt'], r['rejected']): r for r in read_jsonl(run / 'validated.jsonl')}
    pairs = []
    for p in read_jsonl(run / 'pairs-pilot.jsonl'):
        key = (text_of(p['prompt']), text_of(p['rejected']))
        assert key in validated, f'pair without a validated row: {p["id"]}'
        v = validated[key]
        assert text_of(p['chosen']) == v['chosen'], f'chosen differs from the validated row: {p["id"]}'
        pairs.append(dict(id=v['id'], verdict=v['verdict'], group=v['group'], kind=v['kind'], prompt=v['prompt'], chosen=v['chosen'],
                          rejected=v['rejected'], changes=v['changes'], length_ratio=v['length_ratio']))
    by_verdict = {k: [p for p in pairs if p['verdict'] == k] for k in QUOTA}
    rng = random.Random(seed)
    picked = [p for k, n in QUOTA.items() for p in rng.sample(by_verdict[k], min(n, len(by_verdict[k])))]
    rng.shuffle(picked)
    return picked, {k: len(v) for k, v in by_verdict.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--api-url', default=os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'))
    ap.add_argument('--workspace', default=os.getenv('ARGILLA_WORKSPACE', 'sft-review'))
    ap.add_argument('--name', default='exp005-pilot-pairs-read-30')
    ap.add_argument('--seed', type=int, default=5)
    args = ap.parse_args()
    rows, pool = build_packet(args.run, args.seed)
    assert len(rows) == 30, f'expected 30 rows, got {len(rows)}'
    packet = args.run / 'pair-review-30.jsonl'
    packet.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8', newline='\n')
    sha = hashlib.sha256(packet.read_bytes()).hexdigest()
    groups = {g: sum(r['group'] == g for r in rows) for g in sorted({r['group'] for r in rows})}
    print('packet', packet, 'pool by verdict', pool, 'sample by group', groups, 'sha256', sha[:16])
    if args.dry_run:
        return
    import argilla as rg
    client = rg.Argilla(api_url=args.api_url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    if client.workspaces(name=args.workspace) is None:
        raise ValueError('Expected the existing local review workspace')
    if client.datasets(name=args.name, workspace=args.workspace) is not None:
        raise FileExistsError('Dataset already exists; preserve its reviews rather than replace it')
    settings = rg.Settings(
        guidelines=('Data gate for exp-005, before any training. For one prompt that carries its own data, REJECTED is the small model\'s own answer '
                    'and CHOSEN is the same answer repaired by a strong model (it should differ only where the original was wrong). Judge: '
                    '(1) is CHOSEN correct against the prompt\'s data and limits, in natural Turkish, with nothing invented; a dull correct answer is '
                    'fine; (2) is CHOSEN better than REJECTED. The gate needs at least 27 of 30 with CHOSEN good AND better. If CHOSEN is wrong, '
                    'write the complete corrected answer in the text box. Nothing is pre-filled.'),
        fields=[rg.TextField(name='changes', title='What the repairer says it changed'),
                rg.TextField(name='prompt', title='Prompt'),
                rg.TextField(name='chosen', title='CHOSEN (repaired answer)'),
                rg.TextField(name='rejected', title='REJECTED (the model\'s own answer)')],
        questions=[rg.LabelQuestion(name='chosen_quality', title='CHOSEN: correct against the data and limits, natural Turkish, nothing invented?',
                                    labels=['good', 'minor_issues', 'wrong']),
                   rg.LabelQuestion(name='vs_rejected', title='CHOSEN compared with REJECTED', labels=['chosen_better', 'about_same', 'rejected_better']),
                   rg.TextQuestion(name='corrected_chosen', title='Corrected chosen answer (only if CHOSEN is wrong or needs a fix; write the COMPLETE answer)', required=False),
                   rg.TextQuestion(name='notes', title='Notes (what is wrong)', required=False)],
        metadata=[rg.TermsMetadataProperty(name='verdict', options=list(QUOTA)),
                  rg.TermsMetadataProperty(name='group', options=sorted({r['group'] for r in rows}))])
    records = []
    for r in rows:
        notes = [r['id'], f'verdict: {r["verdict"]}, group: {r["group"]}, chosen/rejected words: {r["length_ratio"]}'] + [f'- {c}' for c in r['changes']]
        records.append(rg.Record(id=r['id'], fields=dict(changes='\n'.join(notes), prompt=r['prompt'], chosen=r['chosen'], rejected=r['rejected']),
                                 metadata=dict(verdict=r['verdict'], group=r['group'])))
    dataset = rg.Dataset(name=args.name, workspace=args.workspace, settings=settings, client=client)
    dataset.create()
    dataset.records.log(records, batch_size=10)
    count = len(list(dataset.records))
    if count != 30:
        raise ValueError(f'Partial upload: {count}/30. Preserve and inspect before retrying.')
    receipt = dict(dataset_name=args.name, dataset_id=str(dataset.id), workspace=args.workspace,
                   url=f'{args.api_url}/dataset/{dataset.id}/annotation-mode', records=count, packet_sha256=sha, seed=args.seed)
    (args.run / f'pair-review-receipt-{args.name}.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt, indent=1))


if __name__ == '__main__':
    main()
