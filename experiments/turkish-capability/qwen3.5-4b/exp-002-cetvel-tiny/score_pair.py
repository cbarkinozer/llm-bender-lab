"""Validate arm parity, then reuse task-native CPU scorers; never an LLM judge."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'scripts/evaluation'))
from score_cetvel_generation import SCORERS


def load(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    answers = folder / 'answers.jsonl'
    expected = manifest['config'].get('expected_count', 100)
    assert manifest['status'] == 'completed' and manifest['count'] == expected
    assert hashlib.sha256(answers.read_bytes()).hexdigest() == manifest['answers_sha256']
    rows = [json.loads(line) for line in answers.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == expected
    return manifest, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    bm, base = load(args.results_root / 'base')
    fm, adapted = load(args.results_root / 'F')
    assert bm['arm'] == 'base' and fm['arm'] == 'F'
    for key in ('config', 'questions_sha256', 'packages', 'backend', 'precision', 'chat_template_sha256', 'eos_token_ids', 'source_hashes'):
        assert bm[key] == fm[key], key
    for a, b in zip(base, adapted):
        for key in ('id', 'task', 'document', 'target', 'semantic_prompt', 'rendered_prompt', 'prompt_token_ids'):
            assert a[key] == b[key], (a['id'], key)
    results = {}
    for arm, rows in [('base', base), ('F', adapted)]:
        results[arm] = {}
        for task, scorer in SCORERS.items():
            group = [r for r in rows if r['task'] == task]
            assert len(group) == bm['config'].get('per_task_count', 20)
            results[arm][task] = scorer(group)
        results[arm]['termination'] = dict(collections.Counter(r['finish_reason'] for r in rows))
        results[arm]['output_tokens'] = sorted(r['generated_tokens'] for r in rows)
        (args.results_root / arm / 'scored-samples.jsonl').write_text(
            ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    report = dict(status='scored', prompt_parity_verified=True, results=results,
        note='Reference-overlap scores are not semantic accuracy. Inspect frozen human20, '
             'all terminations and failures; do not average different metrics into one score.')
    (args.results_root / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
