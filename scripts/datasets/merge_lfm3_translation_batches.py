"""Merge translation-batches/batch*.py (each defines T = {group id: Turkish rendering}) into translations-tr.jsonl."""
import json
from pathlib import Path
import runpy

EXP = Path(__file__).resolve().parents[2] / 'experiments/turkish-capability/lfm3-1.7b/exp-016-self-distill-targets'


def main():
    merged = {}
    for path in sorted((EXP / 'translation-batches').glob('batch*.py')):
        batch = runpy.run_path(str(path))['T']
        duplicates = set(batch) & set(merged)
        assert not duplicates, f'{path.name} repeats {sorted(duplicates)}'
        merged.update(batch)
    wanted = [json.loads(s)['id'] for s in (EXP / 'data-local/en-answers.jsonl').read_text(encoding='utf-8').splitlines()]
    unused = sorted(set(merged) - set(wanted))
    if unused:
        print('rendered but not used (group dropped by the length cap or no complete own answer):', unused)
    out = EXP / 'translations-tr.jsonl'
    out.write_text(''.join(json.dumps(dict(id=k, answer_tr=merged[k]), ensure_ascii=False) + '\n' for k in wanted if k in merged),
                   encoding='utf-8', newline='\n')
    print(f'{len(merged)} of {len(wanted)} groups rendered; missing: {len(wanted) - len(merged)}')


if __name__ == '__main__':
    main()
