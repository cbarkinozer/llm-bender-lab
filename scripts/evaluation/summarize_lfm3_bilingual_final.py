"""Local diagnostics; numeric extraction is a review aid, not a correctness judge."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
RUN = BASE / 'final-eval-v01-local'
MODELS = ['base', 'turkish60', 'bilingual69']


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def main():
    assert json.loads((RUN / 'completion.json').read_text())['outputs'] == 444
    packet = BASE / 'bilingual-pilot-v01/eval-v01'
    refs = {r['id']: r for r in rows(packet / 'eval-references.jsonl')}
    refs.update({r['id']: r for r in rows(packet / 'symbolic-controls-references.jsonl')})
    report = {
        'status': 'automatic-diagnostics-awaiting-owner-review',
        'caveats': [
            'These diagnostics do not measure semantic correctness or language quality.',
            'Symbolic exact match checks output format as well as the value; inspect nonmatches.',
            'Symbolic terminal-integer extraction checks the final value separately from value-only formatting.',
            'The four directions share 35 underlying tasks; they are not 140 independent tasks.',
            'Arithmetic review includes every answer, including apparent matches.',
        ],
        'models': {},
    }
    review = []
    for model in MODELS:
        path = RUN / 'inference' / model / 'answers.jsonl'
        values = rows(path)
        assert len(values) == len({r['id'] for r in values}) == 148
        assert set(r['id'] for r in values) == set(refs)
        by_direction = {}
        for direction in ['tr-tr', 'en-tr', 'tr-en', 'en-en', 'symbolic']:
            selected = [r for r in values if r.get('direction', 'symbolic') == direction]
            if not selected:
                continue
            lengths = sorted(r['generated_tokens'] for r in selected)
            by_direction[direction] = dict(
                count=len(selected),
                finish_reasons=dict(Counter(r['finish_reason'] for r in selected)),
                tokens_median=statistics.median(lengths),
                tokens_p90=lengths[min(len(lengths)-1, int(.9 * len(lengths)))],
                tokens_max=max(lengths),
                length_limit_hits=sum(r['hit_max_new_tokens'] for r in selected),
                exposed_think_tags=sum(any(t in r['raw_output'] for t in ['<think>', '</think>', '<thinking>', '</thinking>']) for r in selected),
            )
        controls = [r for r in values if 'symbolic' in r['id']]
        assert len(controls) == 8
        symbolic = []
        for r in controls:
            match = re.search(r'(?<![\d.])(-?\d+)\s*[.!]?\s*$', r['prediction'])
            parsed = match.group(1) if match else None
            symbolic.append(dict(id=r['id'], expected=refs[r['id']]['final_answer'],
                terminal_integer=parsed, correct=(parsed == refs[r['id']]['final_answer']) if parsed is not None else None,
                value_only_format=bool(re.fullmatch(r'-?\d+', r['prediction'].strip()))))
        report['models'][model] = dict(
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            by_direction=by_direction,
            symbolic_strict_value_only_matches=sum(r['prediction'].strip() == refs[r['id']]['final_answer'] for r in controls),
            symbolic_count=8,
            symbolic_terminal_numeric_matches=sum(r['correct'] is True for r in symbolic),
            symbolic_extraction_failures=sum(r['terminal_integer'] is None for r in symbolic),
            symbolic_details=symbolic,
        )
        for r in values:
            if '-ar0' in r['id'] or 'symbolic' in r['id']:
                ref = refs[r['id']]
                review.append(dict(model=model, id=r['id'], direction=r.get('direction', 'symbolic'),
                    expected=ref['final_answer'], rubric=ref.get('rubric', ref.get('verification', '')),
                    answer=r['prediction'], finish_reason=r['finish_reason'],
                    correctness='', reviewer_notes=''))
    out = RUN / 'analysis'
    out.mkdir(exist_ok=True)
    (out / 'automatic-diagnostics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    target = out / 'arithmetic-review.csv'
    # Never overwrite human correctness labels on a repeated diagnostic run.
    if not target.exists():
        with target.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(review[0]))
            writer.writeheader()
            writer.writerows(review)
    print(json.dumps(dict(models=3, outputs=444, arithmetic_review_rows=len(review), report=str(out)), indent=2))


if __name__ == '__main__':
    main()
