"""Prompts of the skill-preserving lane of the Turkish DPO data (preference-rl exp-003).

  python tr_dpo_skill_prompts.py build --out DIR

Why: DPO on Turkish repairs alone can move the model away from what it does well. These prompts have automatic right and wrong answers
(math number, MBPP tests, tool call, countable constraints), so pairs need no editor: chosen = a verified answer of the model itself,
rejected = a wrong answer of the model itself. Sources are the SFT core pack prompts (leakage-audited against the eval sets; the held-out
GSM8K final test, HumanEval and IFEval are not used):
  math EN and TR   GSM8K train prompts (TR = machine translations), only those where the original model was not always right
  code             MBPP train prompts, same selection
  tool             Glaive function-calling prompts, same selection
  ifeval_like      English prompts with countable constraints written here (topics and wording of our own, not IFEval's)
Output rows use the SFT core render schema, so generate_lfm3_sft_samples.py and verify_lfm3_sft_samples.py run on them unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SFT = ROOT / 'experiments/turkish-capability/lfm3-1.7b/sft-core-v01/samples-local'
RENDERS = [SFT / 'prompts-render-en.jsonl', SFT / 'prompts-render-phaseC.jsonl']
VERIFIED = [SFT / 'verified-base-en.jsonl', SFT / 'verified-base-tr.jsonl']
KEEP = {'math', 'code', 'tool'}  # math_final_test and en_general (no checker) are not used

TOPICS = ['a morning walk', 'recycling at home', 'a small bakery', 'learning to swim', 'a rainy day in the city',
          'saving money as a student', 'a trip by train', 'keeping a daily journal', 'a neighbourhood library',
          'cooking dinner for friends', 'a mountain village', 'why sleep matters']
# (instruction template, constraint items in the format of lfm3_sft_constraints.check_constraints)
FORMS = [
    ('Write a short note about {t}. Use at most {n} words.', lambda n: [dict(type='max_words', n=n)], (30, 40, 60)),
    ('Give exactly {n} tips related to {t} as a bulleted list.', lambda n: [dict(type='bullets', n=n)], (3, 4, 5)),
    ('Describe {t} in at most {n} sentences.', lambda n: [dict(type='max_sentences', n=n)], (2, 3)),
    ('Write about {t} in at least {n} words.', lambda n: [dict(type='min_words', n=n)], (80, 120)),
]


def read_jsonl(path):
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def hard_ids():
    """Prompts where the original model was not right in every sample (a wrong answer is likely)."""
    hard = set()
    for path in VERIFIED:
        for row in read_jsonl(path):
            if row['category'] in KEEP and not all(row['verified']):
                hard.add(row['id'])
    return hard


def ifeval_like():
    rows, i = [], 0
    for form, items, sizes in FORMS:
        for topic in TOPICS:
            n = sizes[i % len(sizes)]
            i += 1
            rows.append(dict(id=f'dpo-ifl-{i:03d}', core_id=f'dpo-ifl-{i:03d}', lang='en', category='ifeval_like',
                             messages=[dict(role='user', content=form.format(t=topic, n=n))], thinking=False,
                             check=dict(type='constraints', items=items(n))))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', choices=['build'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    hard = hard_ids()
    rows, seen = [], set()
    for path in RENDERS:
        for row in read_jsonl(path):
            if row['category'] in KEEP and row['id'] in hard and row['id'] not in seen:
                seen.add(row['id'])
                rows.append(row)
    rows += ifeval_like()
    args.out.mkdir(parents=True, exist_ok=True)
    text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    (args.out / 'prompts-skills-dpo.jsonl').write_text(text, encoding='utf-8', newline='\n')
    by = {}
    for r in rows:
        key = f"{r['category']}/{r['lang']}/{'think-on' if r['thinking'] else 'think-off'}"
        by[key] = by.get(key, 0) + 1
    manifest = dict(rows=len(rows), by_cell=by, hard_selection='original model not right in every one of its 4 samples',
                    sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
    (args.out / 'prompts-skills-dpo.manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=1))


if __name__ == '__main__':
    main()
