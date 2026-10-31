"""Validate a portable static AI review and preserve it without human responses."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

try:
    from .tdd_review_rules import validate_submitted_decision
except ImportError:
    from tdd_review_rules import validate_submitted_decision


def parse_review(text):
    records = []
    for block in re.split(r'(?m)^----\s*$', text):
        if not block.strip():
            continue
        fields = {}
        key = None
        for line in block.splitlines():
            match = re.match(r'^([a-z][a-z0-9_]*):\s*(.*)$', line)
            if match:
                key, value = match.groups()
                if key in fields:
                    raise ValueError('Duplicate field: ' + key)
                fields[key] = value
            elif line.strip():
                if key is None:
                    raise ValueError('Text before first field')
                fields[key] += '\n' + line
        records.append(fields)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    reviews = parse_review(raw.decode('utf-8-sig'))
    rows = [json.loads(line) for line in (args.bundle / 'records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    by_id = {row['record_id']: row for row in rows}
    forms = list(args.bundle.glob('human-review-*/presentation-v02/annotation-options.json')) + list(args.bundle.glob('review-schema/annotation-options.json'))
    if len(forms) != 1:
        raise ValueError('Expected exactly one frozen annotation schema')
    form = json.loads(forms[0].read_text(encoding='utf-8'))
    ids = [review.get('record_id') for review in reviews]
    if len(ids) != len(set(ids)) or set(ids) != set(by_id):
        raise ValueError('Review must contain each bundle ID exactly once')
    annotations = []
    for review in reviews:
        row = by_id[review['record_id']]
        digest = sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if review['record_sha256'] != digest or review['reviewed_revision'] != args.bundle.name:
            raise ValueError('Record hash/revision mismatch: ' + review['record_id'])
        if review['reviewer_type'] != 'AI' or not review['reviewer_model'].strip():
            raise ValueError('Missing AI reviewer attribution')
        answers = {}
        for question in form:
            name = question['name']
            value = review.get(name, '').strip()
            if question['required'] and not value:
                raise ValueError('Missing required answer: ' + name)
            if question['kind'] == 'single-choice' and value not in question['options']:
                raise ValueError('Invalid option: ' + name + '=' + value)
            if question['kind'] == 'multi-select':
                value = json.loads(value or '[]')
                if not isinstance(value, list) or any(option not in question['options'] for option in value):
                    raise ValueError('Invalid multi-select: ' + name)
            answers[name] = value
        problems = validate_submitted_decision(answers, row, answers['blocking_issues'])
        if problems:
            raise ValueError(review['record_id'] + ': ' + '; '.join(problems))
        annotations.append(dict(record_id=review['record_id'], record_sha256=digest,
                                reviewer_type='AI', reviewer_model=review['reviewer_model'],
                                method='static review of supplied export; no execution or source inspection',
                                answers=answers))
    # Validate everything before creating any output; never replace existing reviews.
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'original-review.txt').write_bytes(raw)
    (args.output / 'annotations.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in annotations), encoding='utf-8')
    summary = dict(revision=args.bundle.name, records=len(annotations),
                   decisions=dict(Counter(item['answers']['approval'] for item in annotations)),
                   input_sha256=sha256(raw).hexdigest(), human_ratings_submitted=False,
                   argilla_written=False, training_authorized=False)
    (args.output / 'receipt.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
