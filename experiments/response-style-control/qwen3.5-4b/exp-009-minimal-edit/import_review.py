"""Import verified review CSVs into separate train/validation Argilla queues."""
import argparse
import csv
import json
import os
from pathlib import Path
import argilla as rg


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--review-dir', required=True, type=Path)
    args = p.parse_args()
    verification = json.loads((args.review_dir/'verification.json').read_text(encoding='utf-8'))
    if verification['status'] != 'passed' or verification['rows'] != 100:
        raise ValueError('Missing verified complete run')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900')
    client = rg.Argilla(api_url=url, api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    workspace = 'sft-review'
    subsets = []
    for split, count in [('train', 80), ('validation', 20)]:
        name = f'exp-009-minimal-edit-{split}'
        if client.datasets(name=name, workspace=workspace) is not None:
            raise RuntimeError(f'{name} already exists; preserve annotations')
        with (args.review_dir/f'{split}-review-{count}.csv').open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        if len(rows) != count or any(r['split'] != split for r in rows):
            raise ValueError('Wrong review split')
        subsets.append((split, name, rows))
    links = []
    for split, name, rows in subsets:
        guidelines = ('Edit the final assistant reply only. Preserve correct wording where practical, '
                      'but correct factual/semantic errors even if substantial rewriting is necessary. '
                      'Remove filler and fabricated feelings, memories or experience. Preserve natural Turkish, '
                      'uncertainty, negation, quantities and useful explanation. Clarify only when necessary; '
                      'do not ask again after missing information is supplied. Accept unchanged, rewrite '
                      'with a COMPLETE replacement, or reject. Raw base answers are drafts, not gold. ')
        guidelines += ('TRAIN: approved replies may become training targets.' if split == 'train' else
                       'VALIDATION ONLY: edited replies are evaluation references, NEVER training targets.')
        settings = rg.Settings(guidelines=guidelines,
            fields=[rg.TextField(name=n, use_markdown=False) for n in
                    ['conversation', 'original_answer', 'category', 'evaluation_criteria']],
            questions=[rg.LabelQuestion(name='decision', labels=['accept', 'rewrite', 'reject'], required=True),
                       rg.TextQuestion(name='rewritten_response', title='Complete replacement answer (when rewriting)', required=False, use_markdown=False),
                       rg.TextQuestion(name='review_notes', required=False, use_markdown=False)])
        dataset = rg.Dataset(name=name, workspace=workspace, settings=settings, client=client).create()
        dataset.records.log([rg.Record(id=r['id'], fields={n: r[n] for n in
                    ['conversation', 'original_answer', 'category', 'evaluation_criteria']}) for r in rows])
        links.append(dict(name=name, rows=len(rows), id=str(dataset.id),
                          url=f'{url}/dataset/{dataset.id}/annotation-mode?page=1&status=pending'))
    (args.review_dir/'argilla-links.json').write_text(json.dumps(links, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(links, indent=2))


if __name__ == '__main__':
    main()
