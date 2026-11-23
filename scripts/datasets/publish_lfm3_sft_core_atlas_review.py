"""Select 60 Atlas rows of the SFT core v01 pack (stratified) and publish them as a new local Argilla review dataset.

  python publish_lfm3_sft_core_atlas_review.py [--dry-run] [--api-url URL] [--workspace NAME] [--name NAME]

Rows come from the 422 Atlas (tr_general) rows of the exp-019 pack: 26 with countable constraints, 19 with a context, 15 plain;
chosen by a seeded hash rank. The reviewer sees the Atlas prompt, the answer used as the training target (LFM3's own reply, with
its English reasoning in a separate field) and the Atlas original answer (never trained on). Nothing is pre-filled. Creates a new
dataset only and aborts if the name exists, so earlier reviews are never replaced. The committed manifest holds ids only; the
packet with Atlas text stays in the ignored samples-local directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / 'experiments/turkish-capability/lfm3-1.7b/sft-core-v01'
ENV = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
SEED = 'sft-core-v01-atlas-review-60-20261123'
QUOTA = dict(constrained=26, context=19, plain=15)
CONTEXT_MARK = re.compile(r'(?:pasaj|metin|veri|orijinal|rapor|bağlam)\s*:', re.I)
PACKET = CORE / 'samples-local/atlas-review-60.jsonl'
MANIFEST = CORE / 'atlas-review-60-manifest.json'
RECEIPT = CORE / 'atlas-review-receipt.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def message_text(messages):
    return '\n'.join(m['content'] for m in messages)


def build_packet():
    pack_path = CORE / 'pack-local/lfm3-base-v1/train.jsonl'
    pack = [r for r in read_jsonl(pack_path) if r['category'] == 'tr_general']
    core = {r['id']: r for r in read_jsonl(CORE / 'prompts-en.jsonl')}
    pools = dict(constrained=[], context=[], plain=[])
    for r in pack:
        c = core[r['core_id']]
        items = c['check']['items']
        user = c['tr']['user']
        group = 'constrained' if items else 'context' if CONTEXT_MARK.search(user) else 'plain'
        pools[group].append((hashlib.sha256((SEED + r['id']).encode()).hexdigest(), r, c, items, group))
    rows = []
    for group, quota in QUOTA.items():
        for _, r, c, items, g in sorted(pools[group], key=lambda p: p[0])[:quota]:
            assistant = r['completion'][0]
            rows.append(dict(id=r['id'], core_id=r['core_id'], group=g, thinking='on' if r['chat_template_kwargs'].get('enable_thinking') else 'off',
                             constraints=items, atlas_row=c['source']['row'], prompt=message_text(r['prompt']),
                             trained_answer=assistant['content'], trained_thinking=assistant.get('thinking') or '',
                             atlas_reference=c['reference']['answer']))
    rows.sort(key=lambda x: hashlib.sha256((SEED + 'order' + x['id']).encode()).hexdigest())
    return rows, dict(pool_sizes={k: len(v) for k, v in pools.items()}, pack_sha256=sha(pack_path), core_prompts_sha256=sha(CORE / 'prompts-en.jsonl'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--api-url', default=os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'))
    parser.add_argument('--workspace', default=os.getenv('ARGILLA_WORKSPACE', 'sft-review'))
    parser.add_argument('--name', default='lfm3-sft-core-v01-atlas-review-60')
    args = parser.parse_args()
    rows, provenance = build_packet()
    if len(rows) != 60:
        raise ValueError(f'expected 60 rows, got {len(rows)}')
    PACKET.parent.mkdir(parents=True, exist_ok=True)
    PACKET.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8', newline='\n')
    MANIFEST.write_text(json.dumps(dict(seed=SEED, quota=QUOTA, rows=60, ids=[r['id'] for r in rows], groups={r['id']: r['group'] for r in rows},
                                        packet_sha256=sha(PACKET), publisher_sha256=sha(Path(__file__)), **provenance), indent=1) + '\n',
                        encoding='utf-8', newline='\n')
    print('packet', PACKET, 'groups', {g: sum(r['group'] == g for r in rows) for g in QUOTA})
    if args.dry_run:
        return
    for line in (ENV.read_text(encoding='utf-8-sig').splitlines() if ENV.exists() else []):
        key, sep, value = line.partition('=')
        if sep and key.strip() in ('ARGILLA_API_KEY', 'ARGILLA_WORKSPACE'):
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    import argilla as rg
    client = rg.Argilla(api_url=args.api_url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    if client.workspaces(name=args.workspace) is None:
        raise ValueError('Expected the existing local review workspace')
    if client.datasets(name=args.name, workspace=args.workspace) is not None:
        raise FileExistsError('Dataset already exists; preserve its reviews rather than replace it')
    settings = rg.Settings(
        guidelines=('Review of Atlas rows that were used to train the Turkish SFT v1. The PROMPT is taken from the Atlas dataset as it is. '
                    'The TRAINED ANSWER is the model\'s own reply used as the training target (its English reasoning is shown apart). '
                    'The ATLAS ORIGINAL ANSWER is shown for comparison only and was never trained on. Judge: (1) is the prompt itself a '
                    'sensible task in natural Turkish (typos, missing diacritics, broken or contradictory instructions count against it); '
                    '(2) is the Turkish of the trained answer natural; (3) does the answer do the task, keep every stated limit and avoid '
                    'wrong facts. Decide keep / edit / drop for using this row as a training example. For edit, write the corrected '
                    'prompt and/or the complete corrected answer. Nothing is pre-filled.'),
        fields=[rg.TextField(name='row_info', title='Row, group and constraints'),
                rg.TextField(name='prompt', title='Prompt (Atlas, as it is)'),
                rg.TextField(name='trained_answer', title='Trained answer (the model\'s own reply)'),
                rg.TextField(name='trained_thinking', title='Reasoning used with the answer (English)', required=False),
                rg.TextField(name='atlas_reference', title='Atlas original answer (never trained on)', required=False)],
        questions=[rg.LabelQuestion(name='prompt_quality', title='Is the prompt good?', labels=['good', 'fixable', 'bad']),
                   rg.LabelQuestion(name='answer_turkish', title='Turkish of the trained answer', labels=['good', 'needs_edit', 'poor']),
                   rg.LabelQuestion(name='answer_correct', title='Does the answer do the task, keep the limits, no wrong facts?',
                                    labels=['pass', 'fail', 'unsure']),
                   rg.LabelQuestion(name='decision', title='Use this row for training?', labels=['keep', 'edit', 'drop']),
                   rg.TextQuestion(name='corrected_prompt', title='Corrected prompt (only if needed)', required=False),
                   rg.TextQuestion(name='corrected_answer', title='Complete corrected answer (for edit)', required=False),
                   rg.TextQuestion(name='notes', title='Notes', required=False)],
        metadata=[rg.TermsMetadataProperty(name='group', options=list(QUOTA)), rg.TermsMetadataProperty(name='thinking', options=['on', 'off'])])
    records = []
    for r in rows:
        info = f'{r["id"]}  (Atlas row {r["atlas_row"]})\ngroup: {r["group"]}   thinking: {r["thinking"]}\nconstraints checked by code: ' + \
               (json.dumps(r['constraints'], ensure_ascii=False) if r['constraints'] else 'none')
        records.append(rg.Record(id=r['id'], fields=dict(row_info=info, prompt=r['prompt'], trained_answer=r['trained_answer'],
                                                         trained_thinking=r['trained_thinking'], atlas_reference=r['atlas_reference']),
                                 metadata=dict(group=r['group'], thinking=r['thinking'])))
    dataset = rg.Dataset(name=args.name, workspace=args.workspace, settings=settings, client=client)
    dataset.create()
    dataset.records.log(records, batch_size=20)
    count = len(list(dataset.records))
    if count != 60:
        raise ValueError(f'Partial upload: {count}/60. Preserve and inspect before retrying.')
    receipt = dict(dataset_name=args.name, dataset_id=str(dataset.id), workspace=args.workspace,
                   url=f'{args.api_url}/dataset/{dataset.id}/annotation-mode', records=count, packet_sha256=sha(PACKET),
                   publisher_sha256=sha(Path(__file__)), note='New dataset only; no labels or suggestions prefilled.')
    RECEIPT.write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt, indent=1))


if __name__ == '__main__':
    main()
