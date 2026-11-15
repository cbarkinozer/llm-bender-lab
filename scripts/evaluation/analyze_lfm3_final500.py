"""Non-destructive, standard-library diagnostics for the recovered CPT cohort.

These are observable string/generation properties, never semantic judgments.
Run from the repository root; original scores and generations are not changed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
SOURCE = BASE / 'exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel'


def normalized(text):
    text = unicodedata.normalize('NFC', text).translate(str.maketrans({'I': 'ı', 'İ': 'i'})).lower()
    return ' '.join(re.findall(r'\w+', text, flags=re.UNICODE))


def has_span(text, answer):
    text, answer = normalized(text), normalized(answer)
    return bool(answer) and (' ' + answer + ' ') in (' ' + text + ' ')


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=BASE / 'response-analysis-v01')
    parser.add_argument('--join-agent-reviews', action='store_true',
                        help='Validate all 500 agent annotations and write a blank owner review index.')
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise ValueError('Analysis must be separate from historical results')
    for name in ['automatic-diagnostics.jsonl', 'automatic-summary.json']:
        if (args.output/name).exists():
            raise FileExistsError(f'Use a new analysis output directory; preserve {args.output/name}')
    if args.join_agent_reviews and (args.output/'review-queue.csv').exists():
        raise FileExistsError('Preserve existing owner review index')
    raw = (args.source / 'scored-samples.jsonl').read_text(encoding='utf-8')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    receipt = json.loads((args.source/'recovery-verification.json').read_text(encoding='utf-8'))
    for name, entry in receipt['files'].items():
        if hashlib.sha256((args.source/name).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'Historical artifact hash differs from receipt: {name}')
    expected_tasks = {'gecturk', 'mlsum_tr', 'tquad', 'wmt_en_tr', 'xquad_tr'}
    if len(rows) != 500 or len({r['id'] for r in rows}) != 500:
        raise ValueError('Expected exactly 500 unique scored IDs')
    if Counter(r['task'] for r in rows) != {task: 100 for task in expected_tasks}:
        raise ValueError('Unexpected task names/counts')
    manifest = json.loads((args.source/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'completed' or manifest['expected_count'] != 500 or len(manifest['selected_ids']) != 500 or set(manifest['selected_ids']) != {r['id'] for r in rows}:
        raise ValueError('Cohort IDs/completion do not match the manifest')
    answers = [json.loads(line) for line in (args.source / 'answers.jsonl').read_text(encoding='utf-8').splitlines()]
    answer_by_id = {r['id']: r for r in answers}
    if len(answers) != 500 or len(answer_by_id) != 500 or set(answer_by_id) != {r['id'] for r in rows}:
        raise ValueError('Answers must contain the same 500 unique IDs')
    for row in rows:
        if row['evaluation_only'] is not True or not all(row[k] == value for k, value in answer_by_id[row['id']].items()):
            raise ValueError(f'Scored row differs from preserved evaluation answer: {row["id"]}')
    records = []
    for row in rows:
        text = row['prediction']
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        counts = Counter(line for line in lines if len(line) >= 20)
        words = normalized(text).split()
        grams = Counter(tuple(words[i:i+8]) for i in range(max(0, len(words)-7)))
        record = dict(id=row['id'], task=row['task'], evaluation_only=True,
                      finish_reason=row['finish_reason'], generated_tokens=row['generated_tokens'],
                      output_characters=len(text), prompt_characters=len(row['semantic_prompt']),
                      nonempty_lines=len(lines),
                      repeated_long_line=any(n >= 3 for n in counts.values()),
                      repeated_8gram_5plus=any(n >= 5 for n in grams.values()),
                      replacement_character_prompt='\ufffd' in row['semantic_prompt'],
                      replacement_character_output='\ufffd' in text,
                      human_reviewed=False, method='deterministic-string-diagnostics-v01')
        if row['task'] == 'gecturk':
            target = row['target'].strip()
            record.update(source_equals_target=row['document']['source'].strip() == target,
                          first_nonempty_line_equals_target=bool(lines) and lines[0] == target,
                          output_starts_with_target=text.lstrip().startswith(target),
                          full_output_equals_target=text.strip() == target)
        if row['task'] in ('tquad', 'xquad_tr'):
            golds = row['target']['answers']['text']
            record.update(reference_span_anywhere=any(has_span(text, g) for g in golds),
                          reference_span_first_300_chars=any(has_span(text[:300], g) for g in golds),
                          reference_span_first_line=any(has_span(lines[0] if lines else '', g) for g in golds))
        records.append(record)
    tasks = {}
    for task in sorted({r['task'] for r in records}):
        group = [r for r in records if r['task'] == task]
        bool_keys = [key for key, value in group[0].items() if isinstance(value, bool)]
        tasks[task] = dict(n=len(group), termination=dict(Counter(r['finish_reason'] for r in group)),
                          median_generated_tokens=statistics.median(r['generated_tokens'] for r in group),
                          total_generated_tokens=sum(r['generated_tokens'] for r in group),
                          counts={key: sum(r[key] for r in group) for key in bool_keys})
    files = ['answers.jsonl', 'scored-samples.jsonl', 'manifest.json', 'scores.json']
    report = dict(status='diagnostic-not-human-approval', n=500, tasks=tasks,
                  source_git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  analysis_provenance=dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     invocation=[sys.executable, *sys.argv], source_directory=str(args.source.resolve()),
                     working_tree_status=subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True).splitlines(),
                     note='Git HEAD identifies the checkout, not uncommitted analysis code; script hash identifies this analyzer.'),
                  input_sha256={name: hashlib.sha256((args.source/name).read_bytes()).hexdigest() for name in files},
                  definitions=dict(repeated_long_line='A stripped nonempty line >=20 characters occurs >=3 times.',
                                   repeated_8gram_5plus='A normalized eight-word sequence occurs >=5 times.',
                                   reference_span='Normalized contiguous whole-word match; not correctness or grounding.',
                                   prefix='Exact stored target prefix; not proof of correction ability when source=target.'),
                  limitations=['No semantic accuracy from these proxies.', 'EOS does not imply a correct or complete answer.',
                               'Full500 has no newly matched original-model full500 comparator.',
                               'Historical inspected cohort is development evidence; exclude all item-derived training material.'])
    if args.join_agent_reviews:
        annotations = []
        for name in ['semantic-gecturk.jsonl', 'semantic-qa.jsonl', 'semantic-mlsum-wmt.jsonl']:
            annotations.extend(json.loads(line) for line in (args.output/name).read_text(encoding='utf-8').splitlines() if line.strip())
        by_id = {r['id']: r for r in annotations}
        if len(annotations) != 500 or len(by_id) != 500 or set(by_id) != {r['id'] for r in rows}:
            raise ValueError('Agent annotations must cover exactly the 500 unique source IDs')
        for row in rows:
            annotation = by_id[row['id']]
            if annotation['task'] != row['task'] or annotation.get('human_reviewed') is not False:
                raise ValueError(f'Invalid task or human-review claim: {row["id"]}')
            if not annotation.get('labels', annotation.get('qualitative_labels')):
                raise ValueError(f'Missing agent triage labels: {row["id"]}')
    # Publish only after input, annotation and provenance validation succeeds.
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'automatic-diagnostics.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records), encoding='utf-8')
    dump(args.output/'automatic-summary.json', report)
    if args.join_agent_reviews:
        queue = args.output/'review-queue.csv'
        # Never overwrite user decisions when regenerating mechanical diagnostics.
        if queue.exists():
            raise FileExistsError(f'Preserve existing review index: {queue}')
        with queue.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['id', 'task', 'finish_reason', 'agent_labels',
                                                       'human_reviewed', 'owner_decision', 'owner_notes'])
            writer.writeheader()
            for row in sorted(rows, key=lambda r: (r['task'], r['id'])):
                labels = by_id[row['id']].get('labels', by_id[row['id']].get('qualitative_labels'))
                writer.writerow(dict(id=row['id'], task=row['task'], finish_reason=row['finish_reason'],
                                     agent_labels=json.dumps(labels, ensure_ascii=False, sort_keys=True),
                                     human_reviewed=False, owner_decision='', owner_notes=''))
        dump(args.output/'review-coverage.json', dict(n=500, unique_ids=500, human_reviewed=0,
             annotation_sha256={name: hashlib.sha256((args.output/name).read_bytes()).hexdigest()
                                for name in ['semantic-gecturk.jsonl', 'semantic-qa.jsonl', 'semantic-mlsum-wmt.jsonl']},
             note='All IDs triaged by agents; inspection scopes vary. No owner semantic approval.'))
    print(json.dumps(dict(n=500, tasks=tasks), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
