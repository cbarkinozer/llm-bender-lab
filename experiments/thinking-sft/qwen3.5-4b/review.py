"""Prepare blinded paired review and summarize completed semantic ratings."""
import argparse
import json
from pathlib import Path
import random

from pipeline import DATA, read_rows, sha, write_json


def prepare(base, candidate, output):
    if output.exists():
        raise ValueError('Review output exists; preserve prior judgments')
    for folder, condition in ((base, 'base'), (candidate, 'adapter')):
        manifest = json.loads((folder / 'evaluation-manifest.json').read_text())
        if not (manifest['complete'] and manifest['split'] == 'test' and manifest['items'] == 20
                and manifest['condition'] == condition and manifest['backend'] == 'hf'
                and manifest['outputs_sha256'] == sha(folder / 'outputs.jsonl')):
            raise ValueError('Expected complete, identity-verified primary test runs')
    manifests = [json.loads((f / 'evaluation-manifest.json').read_text()) for f in (base, candidate)]
    for field in ('model', 'revision', 'settings', 'config_sha256', 'prompts_sha256', 'template_sha256', 'versions', 'gpu', 'evaluate_script_sha256'):
        if manifests[0][field] != manifests[1][field]:
            raise ValueError(f'Unmatched primary evaluation: {field}')
    if manifests[0]['prompts_sha256'] != sha(DATA / 'test-prompts.jsonl'):
        raise ValueError('Current scoring prompts differ from evaluation prompts')
    by_condition = [{r['id']: r for r in read_rows(folder / 'outputs.jsonl')} for folder in (base, candidate)]
    keys = {r['id']: r for r in read_rows(DATA / 'test-keys.jsonl')}
    prompts = {r['id']: r for r in read_rows(DATA / 'test-prompts.jsonl')}
    if any(set(rows) != set(keys) for rows in by_condition):
        raise ValueError('Paired IDs differ')
    rng = random.Random(3407)
    records, mapping = [], {}
    for identity in keys:
        order = [0, 1]
        rng.shuffle(order)
        record = dict(id=identity, prompt=prompts[identity]['messages'][-1]['content'],
                      reference=keys[identity]['reference_answer'])
        mapping[identity] = {}
        for label, condition in zip(('A', 'B'), order):
            result = by_condition[condition][identity]
            response = result['response']
            record[label] = dict(answer=response['content'], reasoning=response['reasoning_content'],
                finish_reason=response['finish_reason'], generated_tokens=response['generated_tokens'],
                elapsed_s=result['elapsed_s'], semantic_score=None, unsupported_facts=None,
                reasoning_contradiction=None, turkish_reasoning=None, notes='')
            mapping[identity][label] = ['base', 'adapter'][condition]
        records.append(record)
    output.mkdir(parents=True)
    write_json(output / 'ratings.json', records)
    write_json(output / 'mapping.json', mapping)
    write_json(output / 'review-provenance.json', dict(base_outputs_sha256=sha(base/'outputs.jsonl'),
        candidate_outputs_sha256=sha(candidate/'outputs.jsonl'), test_keys_sha256=sha(DATA/'test-keys.jsonl'),
        warning='Keep mapping hidden during initial review; collaborative review is assisted adjudication, not independent agreement.'))


def summarize(folder):
    rows = json.loads((folder / 'ratings.json').read_text())
    mapping = json.loads((folder / 'mapping.json').read_text())
    if len(rows) != 20 or {r['id'] for r in rows} != set(mapping):
        raise ValueError('Need all20 paired ratings')
    counts = {k: dict(correct=0, partial=0, wrong=0, natural_stop=0) for k in ('base', 'adapter')}
    wins = losses = ties = 0
    for row in rows:
        scores = {}
        for label in ('A', 'B'):
            score = row[label]['semantic_score']
            if isinstance(score, bool) or score not in (0, .5, 1):
                raise ValueError(f'Unrated or invalid score: {row["id"]}/{label}')
            condition = mapping[row['id']][label]
            scores[condition] = score
            counts[condition][{0:'wrong', .5:'partial', 1:'correct'}[score]] += 1
            counts[condition]['natural_stop'] += row[label]['finish_reason'] == 'stop'
        wins += scores['adapter'] > scores['base']
        losses += scores['adapter'] < scores['base']
        ties += scores['adapter'] == scores['base']
    report = dict(items=20, counts=counts, adapter_wins=wins, adapter_losses=losses, ties=ties,
        full_pass_accuracy_delta_pp=5*(counts['adapter']['correct']-counts['base']['correct']),
        limitation='One small synthetic holdout and one seeded sample per model; no broad Turkish or causal reasoning-language claim.')
    write_json(folder / 'summary.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    create = sub.add_parser('prepare')
    create.add_argument('--base', required=True, type=Path)
    create.add_argument('--candidate', required=True, type=Path)
    create.add_argument('--output', required=True, type=Path)
    summary = sub.add_parser('summarize')
    summary.add_argument('--review', required=True, type=Path)
    args = p.parse_args()
    if args.command == 'prepare':
        prepare(args.base, args.candidate, args.output)
    else:
        summarize(args.review)
