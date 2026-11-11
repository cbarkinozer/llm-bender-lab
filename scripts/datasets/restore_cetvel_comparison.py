"""Restore the historical evaluation packet by pinned IDs; never resample."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    historical = root / 'experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500'
    spec = importlib.util.spec_from_file_location('historical_prepare', historical / 'prepare.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    manifest = json.loads((historical / 'data-v1/manifest.json').read_text(encoding='utf-8'))
    profile = json.loads((historical / 'data-v1/tokenization-profile.json').read_text(encoding='utf-8'))
    selected = collections.defaultdict(list)
    for item in profile['items']:
        task, index = item['id'].rsplit('-', 1)
        selected[task].append(int(index))
    rows = []
    for task in builder.SPECS:
        documents, source = builder.download(task, builder.SPECS[task], args.cache_root)
        if source['file_sha256'] != manifest['sources'][task]['file_sha256']:
            raise ValueError(f'Source hash mismatch: {task}')
        for index in sorted(selected[task]):
            doc = documents[index]
            prompt, target = builder.prompt_target(task, doc)
            group = builder.norm(builder.group_text(task, doc))
            rows.append(dict(id=f'{task}-{index:05}', task=task, index=index, document=doc,
                document_sha256=builder.sha(builder.canonical(doc).encode()),
                source_group_sha256=builder.sha(group.encode()), semantic_prompt=prompt,
                target=target, messages=[dict(role='user', content=prompt)], evaluation_only=True))
        print(f'{task}: {len(selected[task])} restored', flush=True)
    blob = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows).encode('utf-8')
    actual = hashlib.sha256(blob).hexdigest()
    if len(rows) != 500 or actual != manifest['questions_sha256']:
        raise ValueError(f'Historical packet mismatch: count={len(rows)}, sha256={actual}')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / 'questions-500.jsonl'
    if output.exists() and output.read_bytes() != blob:
        raise ValueError('Refusing to replace a different packet')
    output.write_bytes(blob)
    receipt = dict(status='verified', count=len(rows), questions_sha256=actual,
        selection='historical frozen IDs; no new sampling or score-based selection',
        evaluation_only=True, per_task=dict(collections.Counter(r['task'] for r in rows)),
        historical_manifest=str(historical.relative_to(root) / 'data-v1/manifest.json'))
    (args.output_dir / 'restoration-receipt.json').write_text(
        json.dumps(receipt, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
