"""Freeze500 fresh, source-group-disjoint inputs; never select using model scores."""
import argparse
import collections
import concurrent.futures
import csv
from difflib import SequenceMatcher
import hashlib
import io
import json
from pathlib import Path
import random
import re
import unicodedata
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PARENT = HERE.parent / 'exp-002-cetvel-tiny'
OLD = HERE.parent / 'exp-000-baseline/results/cetvel-generation-suite/20260914T065945Z'
TRAIN = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft/data-reviewed-v1/train-reviewed.jsonl'
SPECS = {
    'gecturk': dict(repo='mcemilg/GECTurk-generation', revision='36f6a61aca96cafc4149fa823510a3fa81b98ee3',
        file='test.csv', git_blob='e797d51ce5aa06e536a83a86b0edd7b396d27b8f', kind='csv'),
    'tquad': dict(url='https://raw.githubusercontent.com/TQuad/turkish-nlp-qa-dataset/3bece60f62569182476fe00683793745ba92c32e/dev-v0.1.json',
        revision='3bece60f62569182476fe00683793745ba92c32e', file='dev-v0.1.json', kind='squad-json'),
    'xquad_tr': dict(repo='google/xquad', revision='51adfef1c1287aab1d2d91b5bead9bcfb9c68583',
        file='xquad.tr/validation-00000-of-00001.parquet', kind='parquet',
        sha256='6f788cc02246404a76bb890c3fc7beede9b6d4933f0fd23e841de95f7db3f5e9'),
    'wmt_en_tr': dict(repo='wmt/wmt16', revision='41d8a4013aa1489f28fea60ec0932af246086482',
        file='tr-en/validation-00000-of-00001.parquet', kind='parquet',
        sha256='76f7f6c9b43d09ee013ee9494009d0cd1835d773a258bc847c22f3d3ee29fa31'),
    'mlsum_tr': dict(repo='reciTAL/mlsum', revision='0064616e75e0645465d07e98c1447ee6613f61e8',
        file='tu/test/0000.parquet', kind='parquet',
        sha256='fba3e9fd97a09ee3ca86229ccca36a65ce491cd01d5ae1236e6bfeb6d4ddd27e',
        note='HF converted-Parquet snapshot pinned separately; all historical100 documents must match exactly.')}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def load(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def freeze(path, value, jsonl=False):
    text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in value) if jsonl else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    blob = text.encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == blob, f'Frozen file changed: {path}'
    else:
        path.write_bytes(blob)
    return sha(blob)


def download(task, spec, cache):
    path = cache / task / Path(spec['file']).name
    url = spec.get('url') or f"https://huggingface.co/datasets/{spec['repo']}/resolve/{spec['revision']}/{spec['file']}"
    if not path.exists():
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'llm-bender-evaluation'}), timeout=90) as response:
            blob = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    blob = path.read_bytes()
    if 'sha256' in spec:
        assert sha(blob) == spec['sha256'], task
    if 'git_blob' in spec:
        assert hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest() == spec['git_blob'], task
    if spec['kind'] == 'parquet':
        import pyarrow.parquet as pq
        rows = pq.read_table(path).to_pylist()
    elif spec['kind'] == 'csv':
        rows = list(csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))))
        rows = [dict(source=r['source'], target=r['target']) for r in rows]
    else:
        rows = []
        for article in json.loads(blob)['data']:
            for paragraph in article['paragraphs']:
                for qa in paragraph['qas']:
                    rows.append(dict(id=str(qa['id']), title=article.get('title', ''), context=paragraph['context'],
                        question=qa['question'], answers=dict(text=[a['text'] for a in qa['answers']],
                            answer_start=[int(a['answer_start']) for a in qa['answers']])))
    return rows, {**spec, 'url': url, 'bytes': len(blob), 'file_sha256': sha(blob), 'full_split_count': len(rows)}


def prompt_target(task, doc):
    if task == 'gecturk':
        return f"Verilen cumlenin yazım hatalarını duzeltin.\nHatalı Cümle: {doc['source']}\nDüzeltilmiş hali: ", doc['target']
    if task in ('tquad', 'xquad_tr'):
        return f"Kaynak: {doc['context']}\n\nSoru: {doc['question']}\n\nCevap:", dict(id=doc['id'], answers=doc['answers'])
    if task == 'wmt_en_tr':
        return f"Translate English to Turkish.\n\nEnglish: {doc['translation']['en']}\nTurkish:", doc['translation']['tr']
    return f"Başlık: {doc['title']}\n\nMetin: {doc['text']}\n\nÖzet:", doc['summary']


def group_text(task, doc):
    if task == 'gecturk':
        return doc['target']  # Same intended sentence with different corruptions is one group.
    if task in ('tquad', 'xquad_tr'):
        return doc['context']
    if task == 'wmt_en_tr':
        return doc['translation']['en']
    return doc['text']


def shingles(text):
    words = re.findall(r'\w+', norm(text))
    return {tuple(words[i:i+5]) for i in range(len(words)-4)}


def containment(a, b):
    return len(a & b) / min(len(a), len(b)) if a and b else 0


def train_candidates(task, doc, prompt, training):
    view = doc.get('question', doc.get('source', doc.get('text', doc.get('translation', {}).get('en', ''))))
    candidates = []
    for text, item_id in training:
        for content in {norm(prompt), norm(view)} - {''}:
            ratio = SequenceMatcher(None, content, text).ratio() if min(len(content), len(text)) >= 15 else 0
            overlap = containment(shingles(content), shingles(text))
            if content == text or ratio >= .75 or overlap >= .5:
                candidates.append(dict(train_id=item_id, character_similarity=ratio, shingle_containment=overlap))
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-root', type=Path, required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer
    base_config = json.loads((PARENT / 'results-v1/base/manifest.json').read_text())['config']
    tokenizer = AutoTokenizer.from_pretrained(base_config['model'], revision=base_config['revision'])
    training_rows = load(TRAIN)
    assert len(training_rows) == 104 and sha(TRAIN.read_bytes()) == 'fe8ff4c9ff74a8618754bd2f5c25d1794bad9263cbc5fa3a436d593599085950'
    training = [(norm(m['content']), r['id']) for r in training_rows for m in r['messages'] if m['role'] == 'user']
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {task: pool.submit(download, task, spec, args.cache_root) for task, spec in SPECS.items()}
        pools = {task: future.result() for task, future in futures.items()}
    rows, provenance, audit, lengths, human = [], {}, {}, [], []
    for task, (documents, source) in pools.items():
        historical = load(OLD / task / 'samples.jsonl')
        for old in historical:
            assert documents[old['index']] == old['document'], ('Historical source changed', task, old['index'])
            assert prompt_target(task, old['document']) == (old['semantic_prompt'], old['target'])
        old_groups = {norm(group_text(task, r['document'])) for r in historical}
        old_urls = {r['document'].get('url') for r in historical} - {None, ''}
        old_shingles = [shingles(s) for s in old_groups]
        groups = collections.defaultdict(list)
        excluded = collections.Counter()
        for index, doc in enumerate(documents):
            group = norm(group_text(task, doc))
            if index < len(historical) or group in old_groups or doc.get('url', '') in old_urls:
                excluded['historical_row_or_source_group'] += 1
                continue
            groups[group].append(index)
        rng = random.Random('cetvel-fresh500-v1-3407-' + task)
        keys = sorted(groups)
        rng.shuffle(keys)
        selected_groups, selected_shingles, selected = set(), [], []
        withheld = []
        for group in keys:
            if len(selected) == 100:
                break
            index = rng.choice(groups[group])
            doc = documents[index]
            prompt, target = prompt_target(task, doc)
            words = shingles(group)
            if any(containment(words, other) >= .8 for other in old_shingles + selected_shingles):
                excluded['near_source_group_candidate'] += 1
                withheld.append(dict(index=index, reason='source five-word containment>=.8'))
                continue
            candidates = train_candidates(task, doc, prompt, training)
            if candidates:
                excluded['training_similarity_candidate'] += 1
                withheld.append(dict(index=index, reason='training similarity', candidates=candidates))
                continue
            ids = tokenizer.apply_chat_template([dict(role='user', content=prompt)], tokenize=True,
                add_generation_prompt=True, enable_thinking=False, return_dict=False)
            assert isinstance(ids, list) and all(isinstance(t, int) for t in ids)
            if len(ids) + 4096 > 8192:
                excluded['outside_frozen_context_budget'] += 1
                withheld.append(dict(index=index, reason='input>4096', input_tokens=len(ids)))
                continue
            group_hash = sha(group.encode())
            assert group_hash not in selected_groups
            selected_groups.add(group_hash)
            selected_shingles.append(words)
            row = dict(id=f'{task}-{index:05}', task=task, index=index, document=doc,
                document_sha256=sha(canonical(doc).encode()), source_group_sha256=group_hash,
                semantic_prompt=prompt, target=target, messages=[dict(role='user', content=prompt)], evaluation_only=True)
            selected.append(row)
            lengths.append(dict(id=row['id'], input_tokens=len(ids)))
        assert len(selected) == 100, (task, len(selected), len(groups), excluded)
        selected.sort(key=lambda r: r['index'])
        rows.extend(selected)
        human.extend(random.Random('fresh500-human-v1-3407-' + task).sample([r['id'] for r in selected], 6))
        provenance[task] = dict(**source, historical_documents_verified=len(historical),
            eligible_exact_disjoint_groups=len(groups), source_group_policy='one item per normalized underlying source',
            exclusions=dict(excluded))
        audit[task] = dict(selected_count=100, selected_unique_groups=len(selected_groups),
            training_candidates_in_selected=0, old_source_groups_in_selected=0, withheld_candidates=withheld)
        print(task, 'selected100', dict(excluded), flush=True)
    assert len(rows) == len({r['id'] for r in rows}) == len({norm(r['semantic_prompt']) for r in rows}) == 500
    pilot = load(PARENT / 'data-v1/questions-100.jsonl')
    assert {r['id'] for r in rows}.isdisjoint(r['id'] for r in pilot)
    data = HERE / 'data-v1'
    questions_hash = freeze(data / 'questions-500.jsonl', rows, jsonl=True)
    audit_hash = freeze(data / 'leakage-audit.json', dict(training_sha256=sha(TRAIN.read_bytes()),
        train_rows=104, eval_rows=500, tasks=audit,
        note='Conservative string/group screening, not semantic or pretraining contamination proof. Candidates withheld, not relabeled as true duplicates.'))
    human_hash = freeze(data / 'human-review-30-ids.json', human)
    freeze(data / 'tokenization-profile.json', dict(count=500, max_input_tokens=max(r['input_tokens'] for r in lengths),
        input_truncated_count=0, max_context_tokens=8192, max_new_tokens=4096, items=lengths))
    freeze(data / 'manifest.json', dict(status='prepared', count=500, per_task_count=100,
        questions_sha256=questions_hash, near_duplicate_candidates=0, sources=provenance,
        seed=3407, selection='seeded shuffled source groups from full splits; one random row per eligible group',
        historical700_excluded=True, pilot100_excluded=True, training104_screened=True,
        outputs_used_for_selection=False, human_review_ids_sha256=human_hash, leakage_sha256=audit_hash,
        whole_cetvel_representative=False, official_cetvel_score=False,
        role='independent-source confirmation of fixed F; development if later used to guide training'))
    config = dict(base_config, experiment_id='exp-003-cetvel-500', parent='exp-002-cetvel-tiny',
        status='prepared-needs-gpu', expected_count=500, per_task_count=100,
        role='external-task-confirmation-frozen-F', questions_file='data-v1/questions-500.jsonl',
        human_review_ids_file='data-v1/human-review-30-ids.json', human_review_count=30,
        human_review_blind_seed='cetvel-fresh500-human-blind-3407',
        argilla_dataset_name='cetvel-500-base-f-blind-30-v1',
        wandb=False, training=False)
    freeze(HERE / 'config.json', config)
    print(json.dumps(dict(count=500, questions_sha256=questions_hash, max_input_tokens=max(r['input_tokens'] for r in lengths))))


if __name__ == '__main__':
    main()
