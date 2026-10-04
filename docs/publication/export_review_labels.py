"""Version source-ID keyed human labels without notes, response IDs or timestamps."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    for experiment, count in [('exp-002-cetvel-tiny', 20), ('exp-003-cetvel-500', 30)]:
        folder = ROOT / f'experiments/turkish-capability/qwen3.5-4b/{experiment}/human-review-v1'
        source = folder / 'review.json'
        rows = json.loads(source.read_text(encoding='utf-8'))
        summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
        if len(rows) != count or len({row['id'] for row in rows}) != count:
            raise ValueError('Incomplete/duplicate human review')
        if dict(Counter(row['preference'] for row in rows)) != summary['preferences']:
            raise ValueError('Human preferences do not match frozen summary')
        labels = [{key: row[key] for key in ('id', 'task', 'grades', 'preference', 'selected_position')}
                  for row in rows]
        payload = {'source_review_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                   'count': count, 'reviewers': 1, 'notes_and_private_review_metadata_removed': True,
                   'labels': labels}
        content = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
        destination = folder / 'labels.json'
        if destination.exists() and destination.read_text(encoding='utf-8') != content:
            raise FileExistsError('Preserve earlier labels; use a versioned export instead')
        destination.write_text(content, encoding='utf-8')
        print(experiment, count, 'labels exported; no judgments modified')


if __name__ == '__main__':
    main()
