"""SFT core v01, second round: build the exp-021 pack and the exp-022 (no Atlas) ablation pack from the exp-019 pack (CPU, local).

  python build_lfm3_sft_pack_v2.py
exp-022: the exp-019 pack without its 422 Atlas rows (everything else is still the model's own verified answers).
exp-021: exp-022 plus (a) the Atlas rows after the AI review (keep: unchanged; edit: corrected prompt if given and the complete
corrected answer, trained with thinking off because the saved reasoning no longer matches; drop: removed) and (b) the 80 AI-written
Turkish correspondence rows (thinking off). Corrected answers are checked with the countable-constraint parser.
Inputs: pack-local/lfm3-base-v1/train.jsonl, samples-local/atlas-review-results.json, datasets/turkish-mail-pilot-v01/mail-080.jsonl.
Outputs (ignored): pack-local/lfm3-exp021/train.jsonl, pack-local/lfm3-exp022/train.jsonl; committed report: pack-v2-report.json.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / 'experiments/turkish-capability/lfm3-1.7b/sft-core-v01'
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
from lfm3_sft_constraints import check_constraints  # noqa: E402


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8', newline='\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    base = read_jsonl(CORE / 'pack-local/lfm3-base-v1/train.jsonl')
    core = {r['id']: r for r in read_jsonl(CORE / 'prompts-en.jsonl')}
    review = json.loads((CORE / 'samples-local/atlas-review-results.json').read_text(encoding='utf-8'))['rows']
    mail = read_jsonl(ROOT / 'datasets/turkish-mail-pilot-v01/mail-080.jsonl')
    no_atlas = [r for r in base if r['category'] != 'tr_general']
    atlas_by_id = {r['id']: r for r in base if r['category'] == 'tr_general'}
    assert len(atlas_by_id) == 422 and len(no_atlas) == len(base) - 422
    assert set(review) <= set(atlas_by_id), 'review ids must be pack rows'
    reviewed, failures, decisions = [], [], {'keep': 0, 'edit': 0, 'drop': 0}
    for rid, v in review.items():
        decisions[v['decision']] += 1
        if v['decision'] == 'drop':
            continue
        row = dict(atlas_by_id[rid])
        if v['decision'] == 'edit':
            answer = v['corrected_answer'].strip()
            assert answer, rid
            prompt_text = (v.get('corrected_prompt') or '').strip() or row['prompt'][0]['content']
            row['prompt'] = [{'role': 'user', 'content': prompt_text}]
            row['completion'] = [{'role': 'assistant', 'content': answer}]
            row['chat_template_kwargs'] = {'enable_thinking': False}
            items = parse_items(prompt_text)
            ok, problems = check_constraints(items, answer)
            if items and not ok:
                failures.append(dict(id=rid, problems=problems))
            row['id'] = rid + '-rev'
        reviewed.append(row)
    emails = [dict(id=m['id'], core_id=m['id'], category='tr_email', lang='tr', prompt=[{'role': 'user', 'content': m['prompt']}],
                   completion=[{'role': 'assistant', 'content': m['answer']}], chat_template_kwargs={'enable_thinking': False}) for m in mail]
    exp021 = no_atlas + reviewed + emails
    outputs = {'lfm3-exp022': no_atlas, 'lfm3-exp021': exp021}
    report = dict(base_pack_rows=len(base), atlas_rows_removed=422, review_decisions=decisions, constraint_failures_in_corrected=failures,
                  email_rows=len(emails), outputs={})
    for name, rows in outputs.items():
        out = CORE / 'pack-local' / name / 'train.jsonl'
        write_jsonl(out, rows)
        by_cat = {}
        for r in rows:
            by_cat[r['category']] = by_cat.get(r['category'], 0) + 1
        report['outputs'][name] = dict(rows=len(rows), sha256=sha(out), by_category=by_cat,
                                       thinking_on=sum(bool(r['chat_template_kwargs'].get('enable_thinking')) for r in rows))
    report['inputs_sha256'] = dict(base_pack=sha(CORE / 'pack-local/lfm3-base-v1/train.jsonl'),
                                   mail=sha(ROOT / 'datasets/turkish-mail-pilot-v01/mail-080.jsonl'))
    (CORE / 'pack-v2-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=1, ensure_ascii=False))


def parse_items(prompt):
    from lfm3_sft_constraints import parse_constraints
    return parse_constraints(prompt)


if __name__ == '__main__':
    main()
