"""Validate completed base run and export separate editable review CSVs."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from generate_base import HERE, json_file, sha256, validate_inputs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    cfg, _, prompts = validate_inputs(HERE / 'generation-config.json')
    run = args.run_dir
    manifest = json.loads((run/'run-manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'completed' or manifest['incomplete_ids']:
        raise ValueError('Run not complete')
    if manifest['dataset_sha256'] != cfg['dataset_sha256'] or manifest['backend'] != 'vllm':
        raise ValueError('Wrong dataset or engine')
    for name in ['drafts', 'attempts']:
        if sha256(run/f'{name}.jsonl') != manifest[f'{name}_sha256']:
            raise ValueError(f'Artifact hash mismatch: {name}')
    drafts = [json.loads(s) for s in (run/'drafts.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = {r['id']: r for r in drafts}
    if len(drafts) != 100 or len(by_id) != 100 or set(by_id) != {r['id'] for r in prompts}:
        raise ValueError('Wrong identities/counts')
    for prompt in prompts:
        draft = by_id[prompt['id']]
        if draft['split'] != prompt['split'] or draft['input_messages_sha256'] != prompt['input_messages_sha256']:
            raise ValueError('Prompt/split mismatch')
        if not draft['review_eligible'] or draft['finish_reason'] != 'native_eos' or draft['output_tokens'] >= draft['max_new_tokens']:
            raise ValueError('Incomplete or truncated draft')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    fields = ['id', 'split', 'category', 'conversation', 'original_answer', 'desired_answer', 'decision', 'notes', 'evaluation_criteria']
    for split, count in [('train', 80), ('validation', 20)]:
        subset = [r for r in prompts if r['split'] == split]
        assert len(subset) == count
        with (args.output_dir/f'{split}-review-{count}.csv').open('x', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in subset:
                answer = by_id[row['id']]['output']
                writer.writerow(dict(id=row['id'], split=split, category=row['category'],
                                     conversation='\n\n'.join(m['role']+': '+m['content'] for m in row['messages']),
                                     original_answer=answer, desired_answer=answer, decision='', notes='',
                                     evaluation_criteria=row['evaluation_criteria']))
    json_file(args.output_dir/'verification.json', dict(status='passed', rows=len(drafts),
              splits=dict(Counter(r['split'] for r in drafts)), backend=manifest['backend'],
              native_stop_rows=100, length_limited_rows=0, drafts_sha256=manifest['drafts_sha256'],
              max_output_tokens=max(r['output_tokens'] for r in drafts),
              instructions='Edit desired_answer; preserve original_answer. Validation is evaluation-only, never training.'))
    print('Verified 100 complete drafts; exported 80 training / 20 evaluation-only review rows.')


if __name__ == '__main__':
    main()
