"""Export the submitted answers of the Atlas review dataset (read-only) and summarise them.

  python export_lfm3_sft_core_atlas_review.py [--out RESULTS.json]
Reads the dataset named in atlas-review-receipt.json. Writes ids, labels and the reviewer's own corrections/notes; it does not
change anything in Argilla. Rows with no submitted response are listed as pending.
"""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / 'experiments/turkish-capability/lfm3-1.7b/sft-core-v01'
ENV = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=CORE / 'samples-local/atlas-review-results.json',
                        help='full export with the reviewer text (corrections, notes); keep out of Git')
    parser.add_argument('--labels-out', type=Path, default=CORE / 'atlas-review-labels.json', help='labels only, no free text; committed')
    args = parser.parse_args()
    receipt = json.loads((CORE / 'atlas-review-receipt.json').read_text(encoding='utf-8'))
    manifest = json.loads((CORE / 'atlas-review-60-manifest.json').read_text(encoding='utf-8'))
    for line in (ENV.read_text(encoding='utf-8-sig').splitlines() if ENV.exists() else []):
        key, sep, value = line.partition('=')
        if sep and key.strip() == 'ARGILLA_API_KEY':
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    import argilla as rg
    client = rg.Argilla(api_url=os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900'), api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
    dataset = client.datasets(name=receipt['dataset_name'], workspace=receipt['workspace'])
    if dataset is None:
        raise ValueError('Dataset not found')
    rows, pending = {}, []
    for record in dataset.records(with_responses=True):
        submitted = [r for r in record.responses if getattr(r, 'status', 'submitted') == 'submitted']
        if not submitted:
            pending.append(record.id)
            continue
        values = defaultdict(dict)
        for r in submitted:
            values[r.question_name] = r.value
        rows[record.id] = dict(group=manifest['groups'].get(record.id), **values)
    summary = {q: dict(Counter(v.get(q) for v in rows.values() if v.get(q))) for q in ('prompt_quality', 'answer_turkish', 'answer_correct', 'decision')}
    by_group = {g: dict(Counter(v['decision'] for v in rows.values() if v.get('group') == g and v.get('decision'))) for g in manifest['quota']}
    result = dict(dataset=receipt['dataset_name'], submitted=len(rows), pending=sorted(pending), summary=summary, decision_by_group=by_group, rows=rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    labels = ('prompt_quality', 'answer_turkish', 'answer_correct', 'decision')
    reviewer_type = 'AI assistant (not a human review); the owner approved the use' if any('AI review' in (v.get('notes') or '') for v in rows.values()) else 'unspecified'
    args.labels_out.write_text(json.dumps(dict(
        dataset=receipt['dataset_name'], submitted=len(rows), pending=sorted(pending), summary=summary, decision_by_group=by_group,
        reviewer_type=reviewer_type, rows={i: {k: v.get(k) for k in ('group',) + labels} | dict(has_corrected_prompt=bool(v.get('corrected_prompt')),
                                                               has_corrected_answer=bool(v.get('corrected_answer'))) for i, v in rows.items()}),
        indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(submitted=len(rows), pending=len(pending), summary=summary, decision_by_group=by_group), indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
