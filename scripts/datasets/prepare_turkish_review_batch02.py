"""Select 80 new source candidates and optionally publish the established review UI."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import random
import statistics

from audit_turkish_sources import ROOT, OUT, SOURCES, messages, norm, digest, filehash
from audit_turkish_source_overlap import grams

DEST = OUT / 'review-local/batch02'
NAME = 'turkish-sft-train80-batch02-v01'


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prompt(ms):
    return '\n'.join(m['content'] for m in ms if m['role'] == 'user')


def prepare():
    from tokenizers import Tokenizer
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        assert filehash(DEST / 'candidates80.jsonl') == manifest['packet_sha256']
        return manifest
    old = read(OUT / 'review-local/review-100-train.jsonl') + read(OUT / 'review-local/review-100-test.jsonl')
    old_ids = {r['id'] for r in old}
    seen = {r['source_prompt_sha256'] for r in old}
    old_grams = [grams(prompt(r['original_messages']), 5) for r in old]
    protected = set()
    for r in old:
        if r.get('assigned_split') == 'test':
            for m in r['original_messages']:
                if m['role'] != 'system': protected.update(grams(m['content']))
    for r in read(OUT / 'raw-local/occam/data/validation.jsonl'):
        for m in messages(r):
            if m['role'] != 'system': protected.update(grams(m['content']))
    cohort = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for r in read(cohort):
        doc = r['document']
        texts = [r['semantic_prompt']] + [doc[k] for k in ['question', 'context', 'text', 'source'] if isinstance(doc.get(k), str)] + list(doc.get('translation', {}).values())
        for text in texts: protected.update(grams(text))
    tokpath = OUT / 'raw-local/tokenizer/tokenizer.json'
    tok = Tokenizer.from_file(str(tokpath))
    count = lambda s: len(tok.encode(s, add_special_tokens=False).ids)
    downloads = json.loads((OUT / 'download-manifest.json').read_text(encoding='utf-8'))
    rng = random.Random(3410)
    chosen = []
    rejected = Counter()
    for key, (repo, revision, files) in SOURCES.items():
        index = read(OUT / 'review-local' / (key + '-row-index.jsonl'))
        duplicates = Counter(r['prompt_sha256'] for r in index)
        candidates = [r for r in index if r['source_split'] == 'train' and r['id'] not in old_ids
                      and not r['protected_match_types'] and set(r['flags']) <= ({'reasoning_tag'} if key == 'cot' else set())
                      and duplicates[r['prompt_sha256']] == 1 and r['prompt_sha256'] not in seen
                      and 20 <= r['answer_characters'] <= 8000]
        # Bounded raw loading; exact source-file bytes are checked against the pinned audit.
        raw = {}
        wanted = {(r['filename'], r['line']) for r in candidates}
        for filename in files:
            if 'validation' in filename: continue
            path = OUT / 'raw-local' / key / filename
            expected = next(f['sha256'] for f in downloads[key]['files'] if f['path'] == filename)
            assert filehash(path) == expected, 'Pinned source changed'
            with path.open(encoding='utf-8-sig') as stream:
                for line, text in enumerate(stream, 1):
                    if (filename, line) in wanted: raw[(filename, line)] = json.loads(text)
        # Four answer-length strata, five each; diversify source category within each.
        candidates.sort(key=lambda r: r['answer_characters'])
        categories = Counter()
        source_rows = []
        for band in range(4):
            pool = candidates[len(candidates)*band//4:len(candidates)*(band+1)//4]
            rng.shuffle(pool)
            accepted = 0
            while pool and accepted < 5:
                pool.sort(key=lambda r: categories[str(raw[(r['filename'], r['line'])].get('category', raw[(r['filename'], r['line'])].get('alan', 'unspecified')))])
                meta = pool.pop(0)
                source = raw[(meta['filename'], meta['line'])]
                ms = messages(source)
                p = prompt(ms)
                gp = grams(p, 5)
                if not ms or ms[-1]['role'] != 'assistant' or not ms[-1]['content'].strip():
                    rejected['structure'] += 1; continue
                if meta['prompt_sha256'] in seen or any(grams(m['content']) & protected for m in ms if m['role'] != 'system'):
                    rejected['protected_or_duplicate'] += 1; continue
                if any(len(gp & g)/max(1, min(len(gp), len(g))) >= .35 for g in old_grams if gp and g):
                    rejected['near_prompt_family'] += 1; continue
                pt = count('\n'.join(m['content'] for m in ms[:-1]))
                at = count(ms[-1]['content'])
                if pt + at > 3600:
                    rejected['length_budget'] += 1; continue
                category = source.get('category', source.get('alan', 'unspecified'))
                row = dict(id=meta['id'], source_repo=repo, source_revision=revision,
                    source_filename=meta['filename'], source_line_1based=meta['line'], source_row_id=source.get('id'),
                    original_messages=ms, source_category=category,
                    original_record_sha256=digest(json.dumps(source, ensure_ascii=False, sort_keys=True)),
                    source_prompt_sha256=meta['prompt_sha256'], source_answer_sha256=meta['answer_sha256'],
                    source_split='train', assigned_split='train', reserved_use='training-candidate-review-only',
                    review_status='owner-prior-approval' if key == 'occam' else 'pending',
                    human_reviewed=False, training_eligible=False,
                    owner_decision='keep' if key == 'occam' else None,
                    approval_basis='Explicit standing owner approval of public Occam; no new item review' if key == 'occam' else None,
                    corrected_answer=None, corrected_user=None, owner_notes=None,
                    provenance_status='Pinned source candidate; leakage/publication gates still required',
                    raw_prompt_tokens=pt, raw_answer_tokens=at, answer_length_quartile=band+1)
                source_rows.append(row); accepted += 1
                seen.add(meta['prompt_sha256']); old_grams.append(gp); categories[str(category)] += 1
            assert accepted == 5, f'Insufficient eligible candidates: {key}, band {band}'
        chosen.extend(source_rows)
    assert len(chosen) == len({r['id'] for r in chosen}) == 80
    assert not old_ids & {r['id'] for r in chosen}
    rng.shuffle(chosen)
    packet = DEST / 'candidates80.jsonl'
    packet.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in chosen), encoding='utf-8')
    stats = {}
    for key in SOURCES:
        rows = [r for r in chosen if r['id'].startswith(key+':')]
        lens = sorted(r['raw_answer_tokens'] for r in rows)
        stats[key] = dict(n=len(rows), answer_tokens_total=sum(lens), answer_tokens_min=min(lens),
            answer_tokens_median=statistics.median(lens), answer_tokens_max=max(lens),
            category_counts=dict(Counter(str(r['source_category']) for r in rows)))
    manifest = dict(seed=3410, packet_sha256=filehash(packet), builder_sha256=filehash(Path(__file__)),
        tokenizer_sha256=filehash(tokpath), source_pins={k: {'repo':v[0], 'revision':v[1]} for k,v in SOURCES.items()},
        source_statistics=stats, excluded=dict(rejected), records=80, owner_prior_approved_occam=20,
        new_owner_reviews_required=60, protected_cohort_sha256=filehash(cohort),
        old_packet_sha256={s:filehash(OUT / f'review-local/review-100-{s}.jsonl') for s in ['train','test']},
        selection='20/source; 5 per eligible answer-character quartile; prefer underrepresented source categories; no raw target rewriting',
        limitations=['Raw token counts exclude chat template; re-audit after owner edits.',
            'Count balance is not token balance; no semantic/cross-lingual contamination clearance claimed.',
            'No training export until review, deduplication and native-template gates pass.',
            'Original systems retained for review; shared versioned training system applied only at export.'])
    save(manifest_path, manifest)
    return manifest


def publish(manifest):
    import argilla as rg
    from dotenv import load_dotenv
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    client = rg.Argilla(api_url=url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    workspace = os.getenv('ARGILLA_WORKSPACE', 'sft-review')
    original = client.datasets(name='turkish-sft-source-calibration-v01', workspace=workspace)
    assert original is not None
    dataset = client.datasets(name=NAME, workspace=workspace)
    if dataset is None:
        settings = rg.Settings(fields=original.settings.fields, questions=original.settings.questions,
            metadata=original.settings.metadata, guidelines=original.settings.guidelines + '\n\nBATCH02: 80 NEW TRAINING CANDIDATES. Occam has standing owner approval; review the other60. Direct answers without reasoning tags are intentional when reasoning is unnecessary. Preserve meaning when correcting Turkish. Ratings for edits assess your complete corrected version. No training has started.')
        dataset = rg.Dataset(name=NAME, workspace=workspace, settings=settings, client=client).create()
    existing = {str(r.id): r.to_dict() for r in dataset.records}
    rows = read(DEST / 'candidates80.jsonl')
    assert set(existing) <= {r['id'] for r in rows}
    additions = []
    expected = {}
    for row in rows:
        ms = row['original_messages']; answer = ms[-1]['content']; reason = ''
        if answer.startswith('<think>') and answer.count('<think>') == answer.count('</think>') == 1:
            reason, answer = answer[7:].split('</think>', 1); reason = reason.strip(); answer = answer.strip()
        fields = dict(source='TRAINING CANDIDATE - BATCH02\n' + row['source_repo'] + ' @ ' + row['source_revision'] + '\n' + row['source_filename'] + ':' + str(row['source_line_1based']),
            system='\n'.join(m['content'] for m in ms if m['role']=='system'),
            conversation='\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in ms[:-1] if m['role']!='system'),
            worked_solution=reason, answer=answer)
        expected[row['id']] = fields
        if row['id'] in existing:
            assert existing[row['id']]['fields'] == fields
        else:
            additions.append(rg.Record(id=row['id'], fields=fields, metadata={'source_key':row['id'].split(':')[0]}))
    if additions: dataset.records.log(additions, batch_size=20)
    user = next(u for u in client.users if u.username == 'argilla')
    updates = []
    for record in dataset.records:
        if not str(record.id).startswith('occam:') or len(record.responses): continue
        for question, value in dict(decision='keep', correctness='pass', instruction='pass', turkish='good', detail='appropriate', notes='Standing explicit owner approval of public Occam; no new item-level review performed.').items():
            record.responses.add(rg.Response(question_name=question, value=value, user_id=user.id, status='submitted'))
        updates.append(record)
    if updates: dataset.records.log(updates, batch_size=20)
    after = {str(r.id): r.to_dict() for r in dataset.records}
    assert set(after) == set(expected)
    assert all(after[k]['fields'] == v for k,v in expected.items())
    assert all(after[k] == v for k,v in existing.items()), 'Existing annotation changed'
    assert sum(after[k]['status']=='completed' for k in after if k.startswith('occam:')) == 20
    receipt = dict(name=NAME, dataset_id=str(dataset.id), url=url+'/dataset/'+str(dataset.id)+'/annotation-mode',
        records=80, occam_prior_approved=20, other_sources=60, packet_sha256=manifest['packet_sha256'], full_fields_readback_verified=True)
    save(DEST / 'argilla-receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    manifest = prepare()
    if args.publish: publish(manifest)
    else: print(json.dumps(manifest, indent=2))
