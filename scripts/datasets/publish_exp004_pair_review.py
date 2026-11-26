"""Publish 30 random exp-004 DPO pairs as a new local Argilla review dataset (the owner reads them before any training).

  python publish_exp004_pair_review.py [--dry-run] [--api-url URL] [--workspace NAME] [--name NAME] [--seed N]

Pairs come from exp-004 results-local/pairs (clean vs flagged sample of the same prompt), drawn by a seeded sample stratified by the
rejected answer's main reason (14 unknown words, 5 English words, 8 broken constraint, 3 loop). The reviewer sees the prompt, the chosen
answer, the rejected answer and what the detector flagged. Nothing is pre-filled. Creates a new dataset only and aborts if the name exists.
Packet and receipt stay in results-local (not in Git).
"""
import argparse
import hashlib
import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/preference-rl/lfm3-1.7b/exp-004-dpo-onpolicy-turkish/results-local'
QUOTA = dict(unknown_words=14, english_words=5, constraint=8, loop=3)
PRIORITY = ('constraint', 'loop', 'unfinished', 'english_reply', 'english_words', 'unknown_words')


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def text_of(messages):
    return messages[-1]['content'] if isinstance(messages, list) else messages


def build_packet(seed):
    flags = {(r['id'], r['sample']): r for r in read_jsonl(EXP / 'flags/flags.jsonl')}
    pairs = read_jsonl(EXP / 'pairs/pairs-tr-dpo4.jsonl')
    groups = {}
    for p in pairs:
        reason = next((k for k in PRIORITY if k in p['rejected_reasons']), 'other')
        groups.setdefault(reason, []).append(p)
    rng = random.Random(seed)
    picked = [(k, p) for k, n in QUOTA.items() for p in rng.sample(groups.get(k, []), min(n, len(groups.get(k, []))))]
    rng.shuffle(picked)
    rows = []
    for reason, p in picked:
        pid, ab = p['id'].split('#')
        f = flags[(pid, int(ab.split('-')[1]))]
        rows.append(dict(id=p['id'], reason=reason, kind=p['kind'], prompt=text_of(p['prompt']), chosen=text_of(p['chosen']),
                         rejected=text_of(p['rejected']), unknown_words=f['unknown_words'], english_words=f['english_words'],
                         constraint=f['constraint'], loop=f['loop'], unfinished=f['unfinished']))
    return rows, {k: len(v) for k, v in groups.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--api-url', default=os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'))
    ap.add_argument('--workspace', default=os.getenv('ARGILLA_WORKSPACE', 'sft-review'))
    ap.add_argument('--name', default='exp004-dpo-pairs-spotcheck-30-v2')
    ap.add_argument('--copy-from', default=None, help='existing dataset name whose responses (any status) are copied into the new one; it is left untouched')
    ap.add_argument('--seed', type=int, default=4)
    args = ap.parse_args()
    rows, pool = build_packet(args.seed)
    assert len(rows) == 30, f'expected 30 rows, got {len(rows)}'
    packet = EXP / 'pair-review-30.jsonl'
    packet.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8', newline='\n')
    sha = hashlib.sha256(packet.read_bytes()).hexdigest()
    print('packet', packet, 'pool by reason', pool, 'sha256', sha[:16])
    if args.dry_run:
        return
    import argilla as rg
    client = rg.Argilla(api_url=args.api_url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    if client.workspaces(name=args.workspace) is None:
        raise ValueError('Expected the existing local review workspace')
    if client.datasets(name=args.name, workspace=args.workspace) is not None:
        raise FileExistsError('Dataset already exists; preserve its reviews rather than replace it')
    settings = rg.Settings(
        guidelines=('Spot-check of DPO training pairs before any training. For one prompt, the CHOSEN answer is a sample the detectors found clean '
                    'and the REJECTED answer is a sample of the same prompt they flagged. Judge: (1) is the chosen answer correct, natural Turkish '
                    'that does the task (a dull but correct answer is fine; a wrong one is the noise to catch); (2) does the rejected answer really '
                    'have the problem shown under "Flagged" (invented or wrong word, English word, broken limit, loop), or is it a false alarm '
                    '(the flagged word is real Turkish); (3) overall, is the pair usable for teaching the model to prefer the chosen answer. '
                    'Nothing is pre-filled.'),
        fields=[rg.TextField(name='flagged', title='Flagged in the rejected answer (detector output)'),
                rg.TextField(name='prompt', title='Prompt'),
                rg.TextField(name='chosen', title='CHOSEN (clean sample)'),
                rg.TextField(name='rejected', title='REJECTED (flagged sample)')],
        questions=[rg.LabelQuestion(name='chosen_quality', title='Chosen answer: correct and natural Turkish?', labels=['good', 'minor_issues', 'wrong']),
                   rg.LabelQuestion(name='rejected_problem', title='Rejected answer: is the flag right?', labels=['real_problem', 'false_alarm', 'not_worse']),
                   rg.LabelQuestion(name='pair_usable', title='Usable as a training pair?', labels=['yes', 'no']),
                   rg.TextQuestion(name='corrected_chosen', title='Corrected chosen answer (only if the chosen answer is wrong or needs a fix; write the COMPLETE answer for this prompt)', required=False),
                   rg.TextQuestion(name='notes', title='Notes (which word, what is wrong)', required=False)],
        metadata=[rg.TermsMetadataProperty(name='reason', options=list(QUOTA)), rg.TermsMetadataProperty(name='kind', options=sorted({r['kind'] for r in rows}))])
    old = {}
    if args.copy_from:
        source = client.datasets(name=args.copy_from, workspace=args.workspace)
        if source is None:
            raise ValueError('copy-from dataset not found')
        for rec in source.records(with_responses=True):
            old[rec.id] = [rg.Response(question_name=x.question_name, value=x.value, user_id=x.user_id, status=x.status) for x in rec.responses]
        print('copying responses of', len(old), 'records from', args.copy_from)
    records = []
    for r in rows:
        lines = [r['id'], f'main reason: {r["reason"]}']
        if r['unknown_words']:
            lines.append('words the analyzer does not know: ' + ', '.join(r['unknown_words']))
        if r['english_words']:
            lines.append('English words in a Turkish answer: ' + ', '.join(r['english_words']))
        if r['constraint']:
            lines.append('broken limits: ' + '; '.join(r['constraint']))
        if r['loop']:
            lines.append('repeats itself')
        if r['unfinished']:
            lines.append('cut off before the end token')
        records.append(rg.Record(id=r['id'], fields=dict(flagged='\n'.join(lines), prompt=r['prompt'], chosen=r['chosen'], rejected=r['rejected']),
                                 metadata=dict(reason=r['reason'], kind=r['kind']), responses=old.get(r['id'], [])))
    dataset = rg.Dataset(name=args.name, workspace=args.workspace, settings=settings, client=client)
    dataset.create()
    dataset.records.log(records, batch_size=10)
    count = len(list(dataset.records))
    if count != 30:
        raise ValueError(f'Partial upload: {count}/30. Preserve and inspect before retrying.')
    receipt = dict(dataset_name=args.name, dataset_id=str(dataset.id), workspace=args.workspace,
                   url=f'{args.api_url}/dataset/{dataset.id}/annotation-mode', records=count, packet_sha256=sha, seed=args.seed)
    (EXP / f'pair-review-receipt-{args.name}.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt, indent=1))


if __name__ == '__main__':
    main()
