"""Freeze100 external-task inputs from the existing700-item CETVEL mini pool.

Selection deliberately ignores old model outputs/scores; stdlib only.
"""
import collections
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import random
import re
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE.parent / 'exp-000-baseline/results/cetvel-generation-suite/20260914T065945Z'
FTRAIN = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft/data-reviewed-v1/train-reviewed.jsonl'
COUNTS = dict(gecturk=200, tquad=150, xquad_tr=150, wmt_en_tr=100, mlsum_tr=100)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def load(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == content, f'Frozen artifact changed: {path}'
    else:
        path.write_bytes(content)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    rows, sources = [], {}
    for task, expected in COUNTS.items():
        folder = SOURCE / task
        samples = load(folder / 'samples.jsonl')
        assert len(samples) == expected
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
        assert digest(folder / 'samples.jsonl') == summary['samples_sha256']
        sources[task] = dict(pool_count=expected, dataset=manifest['dataset'],
                             samples_sha256=digest(folder / 'samples.jsonl'))
        # Dedicated task seed is reproducible, independent of all model outcomes.
        rng = random.Random('cetvel-tiny-v1-3407-' + task)
        positions = sorted(rng.sample(range(expected), 20))
        for position in positions:
            sample = samples[position]
            document = sample['document']
            canon = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            assert hashlib.sha256(canon.encode()).hexdigest() == sample['document_sha256']
            rows.append(dict(id=f"{task}-{sample['index']:05}", task=task, index=sample['index'],
                             document=document, document_sha256=sample['document_sha256'],
                             semantic_prompt=sample['semantic_prompt'], target=sample['target'],
                             messages=[dict(role='user', content=sample['semantic_prompt'])],
                             evaluation_only=True))
    assert len(rows) == len({r['id'] for r in rows}) == 100
    assert len({norm(r['semantic_prompt']) for r in rows}) == 100
    training = load(FTRAIN)
    assert len(training) == 104
    assert digest(FTRAIN) == 'fe8ff4c9ff74a8618754bd2f5c25d1794bad9263cbc5fa3a436d593599085950'
    candidates, exact = [], []
    for row in rows:
        doc = row['document']
        views = {norm(row['semantic_prompt']), norm(doc.get('question', doc.get('source', '')))} - {''}
        for train in training:
            for message in train['messages']:
                if message['role'] != 'user':
                    continue
                text = norm(message['content'])
                for view in views:
                    if view == text:
                        exact.append(dict(eval_id=row['id'], train_id=train['id']))
                    elif len(view) >= 15 and len(text) >= 15:
                        similarity = SequenceMatcher(None, view, text).ratio()
                        words = re.findall(r'\w+', view)
                        trainwords = re.findall(r'\w+', text)
                        shingles = {tuple(words[i:i+5]) for i in range(len(words)-4)}
                        other = {tuple(trainwords[i:i+5]) for i in range(len(trainwords)-4)}
                        overlap = len(shingles & other) / min(len(shingles), len(other)) if shingles and other else 0
                        if similarity >= .75 or overlap >= .5:
                            candidates.append(dict(eval_id=row['id'], train_id=train['id'],
                                                   similarity=similarity, shingle_containment=overlap))
    assert not exact, exact
    data = HERE / 'data-v1'
    save(data / 'questions-100.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode())
    save(data / 'leakage-audit.json', json_bytes(dict(train_rows=104, eval_rows=100,
         train_sha256=digest(FTRAIN), exact_overlaps=exact, near_duplicate_candidates=candidates,
         note='String screening only; not proof of semantic independence or pretraining non-contamination.')))
    # Freeze20 blind human-review items before seeing current base/F outputs.
    human = []
    for task in COUNTS:
        group = [r['id'] for r in rows if r['task'] == task]
        human.extend(random.Random('human-review-v1-3407-' + task).sample(group, 4))
    save(data / 'human-review-20-ids.json', json_bytes(human))
    save(data / 'manifest.json', json_bytes(dict(status='prepared', count=100,
         selection='task-balanced random20 per task within frozen historical700 prefix pool',
         seed=3407, sources=sources, counts=dict(collections.Counter(r['task'] for r in rows)),
         questions_sha256=digest(data / 'questions-100.jsonl'),
         human_review_ids_sha256=digest(data / 'human-review-20-ids.json'),
         leakage_sha256=digest(data / 'leakage-audit.json'),
         near_duplicate_candidates=len(candidates), outputs_used_for_selection=False,
         entire_cetvel_representative=False, official_cetvel_score=False)))
    print(json.dumps(dict(count=100, near_duplicate_candidates=len(candidates),
                         questions_sha256=digest(data / 'questions-100.jsonl'))))


if __name__ == '__main__':
    main()
