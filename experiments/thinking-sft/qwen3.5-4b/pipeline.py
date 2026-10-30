"""Build Occam 2 data and audit the actual native-template training labels."""
import argparse
import collections
import csv
import difflib
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'exp-001-thinking-sft/data-v1'
MODEL = 'Qwen/Qwen3.5-4B'
REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
SYSTEM = ('Verilen Türkçe kaynaklara dayanarak soruyu çöz. Akıl yürütmeni Türkçe yap. '
          'Gerekli hesapları ve koşulları kontrol et; kaynakta olmayan bilgi ekleme. '
          'Son yanıtını Türkçe, doğrudan ve kısa ver. Bilgi gerçekten yetersizse '
          'eksik bilgiyi belirt; yeterliyse gereksiz açıklama isteme.')
CATEGORIES = ('updates', 'rules', 'quantities', 'evidence')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalize(text):
    return re.sub(r'\W+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def validate(cases):
    counts = collections.Counter((r['split'], r['category']) for r in cases)
    expected = {(s, c): n for s, n in [('train', 20), ('test', 5)] for c in CATEGORIES}
    if dict(counts) != expected:
        raise ValueError(f'Expected 80/20 with balanced categories; got {counts}')
    for key in ('group_id', 'prompt'):
        values = [normalize(r[key]) for r in cases]
        if len(values) != len(set(values)):
            raise ValueError(f'Duplicate {key}; variants must share a split and be reviewed')
    for r in cases:
        if any(not r[k].strip() for k in ('prompt', 'reasoning', 'answer', 'group_id')):
            raise ValueError('Empty field')
        if any(t in r[k] for k in ('prompt', 'reasoning', 'answer')
               for t in ('<think>', '</think>', '<|im_start|>', '<|im_end|>')):
            raise ValueError('Native control delimiters must not occur in semantic data')
    near = []
    for a in cases:
        for b in cases:
            if a['split'] == 'train' and b['split'] == 'test':
                score = difflib.SequenceMatcher(None, normalize(a['prompt']), normalize(b['prompt'])).ratio()
                if score >= .65:
                    near.append(dict(train=a['group_id'], test=b['group_id'], similarity=round(score, 3)))
    return counts, near


def build():
    with (DATA / 'authored-cases.tsv').open(newline='') as stream:
        cases = list(csv.DictReader(stream, delimiter='\t'))
    counts, near = validate(cases)
    train, prompts, keys = [], [], []
    for r in cases:
        identity = dict(id='occam2-' + r['group_id'], group_id=r['group_id'], category=r['category'])
        messages = [dict(role='system', content=SYSTEM), dict(role='user', content=r['prompt'])]
        if r['split'] == 'train':
            train.append(identity | dict(messages=messages + [dict(role='assistant',
                         reasoning_content=r['reasoning'], content=r['answer'])]))
        else:
            prompts.append(identity | dict(messages=messages))
            keys.append(identity | dict(reference_answer=r['answer'], worked_solution=r['reasoning'],
                        scoring='Semantic correctness of all requested conclusions; equivalent wording accepted.'))
    write_rows(DATA / 'train.jsonl', train)
    write_rows(DATA / 'test-prompts.jsonl', prompts)
    write_rows(DATA / 'test-keys.jsonl', keys)
    files = ['authored-cases.tsv', 'train.jsonl', 'test-prompts.jsonl', 'test-keys.jsonl']
    write_json(DATA / 'manifest.json', dict(version='occam2-data-v1', train=80, test=20,
        counts={f'{s}/{c}': n for (s, c), n in sorted(counts.items())},
        source='Assistant-authored synthetic Turkish worked examples, 2026-10-28; no external teacher API.',
        review_status='Draft: structural and arithmetic checks do not replace semantic/human review.',
        split_rule='Distinct authored source scenarios; related reasoning skills intentionally shared.',
        near_duplicate_flags=near, near_duplicate_threshold=.65,
        limitations='Synthetic small specialization set; group names alone do not prove semantic independence.',
        files_sha256={name: sha(DATA / name) for name in files}, builder_sha256=sha(Path(__file__))))
    print(json.dumps(dict(train=len(train), test=len(prompts), near_duplicate_flags=near)))


def encode_training(tokenizer, row, max_length):
    messages = row['messages']
    target = messages[-1]
    if [m['role'] for m in messages] != ['system', 'user', 'assistant']:
        raise ValueError('Only single-turn system/user/assistant examples supported')
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False,
                                         enable_thinking=True)
    prefix = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=False)
    prefix += '<|im_start|>assistant\n'
    if not full.startswith(prefix):
        raise ValueError('Native template assistant prefix changed')
    suffix = full[len(prefix):]
    expected = '<think>\n' + target['reasoning_content'] + '\n</think>\n\n' + target['content'] + '<|im_end|>\n'
    if suffix != expected:
        raise ValueError('Reasoning/answer/template was changed or stripped')
    encoded = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
    if len(encoded['input_ids']) > max_length:
        raise ValueError(f'{row["id"]}: would truncate {len(encoded["input_ids"])} > {max_length}')
    boundary = len(prefix)
    labels = []
    for token, (start, end) in zip(encoded['input_ids'], encoded['offset_mapping']):
        if start < boundary < end:
            raise ValueError('Token crosses user/assistant loss boundary')
        labels.append(token if start >= boundary and end > start else -100)
    selected = [token for token in labels if token != -100]
    # Actual decoded labels must include the complete worked solution, answer,
    # delimiters and end-of-turn; this catches wrong masks, not merely raw text.
    if tokenizer.decode(selected, skip_special_tokens=False) != suffix:
        raise ValueError('Decoded supervised labels do not equal the assistant target')
    end_id = tokenizer.convert_tokens_to_ids('<|im_end|>')
    if end_id not in selected:
        raise ValueError('End-of-turn token is not supervised')
    result = {k: encoded[k] for k in ('input_ids', 'attention_mask')}
    result['labels'] = labels
    stats = dict(id=row['id'], total_tokens=len(labels), supervised_tokens=len(selected),
                 reasoning_tokens=len(tokenizer.encode(target['reasoning_content'], add_special_tokens=False)),
                 answer_tokens=len(tokenizer.encode(target['content'], add_special_tokens=False)))
    return result, stats, suffix


def prepare(output, max_length):
    from transformers import AutoTokenizer
    manifest = json.loads((DATA / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha(DATA / name) != expected:
            raise ValueError(f'Dataset changed: {name}; rebuild and review first')
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
    encoded, stats, previews = [], [], []
    for row in read_rows(DATA / 'train.jsonl'):
        data, stat, suffix = encode_training(tokenizer, row, max_length)
        encoded.append(data)
        stats.append(stat)
        if len(previews) < 4:
            previews.append(dict(id=row['id'], supervised_text=suffix))
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output / 'train-tokenized.jsonl', encoded)
    write_json(output / 'label-previews.json', previews)
    lengths = sorted(s['total_tokens'] for s in stats)
    report = dict(model=MODEL, revision=REVISION, rows=len(encoded), max_length=max_length,
                  truncated=0, length_percentiles={str(p): lengths[min(len(lengths)-1, int((len(lengths)-1)*p/100))]
                    for p in (0, 50, 90, 95, 99, 100)},
                  totals={k: sum(s[k] for s in stats) for k in
                          ('total_tokens', 'supervised_tokens', 'reasoning_tokens', 'answer_tokens')},
                  versions={k: importlib.metadata.version(k) for k in ('transformers', 'tokenizers', 'jinja2')},
                  template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
                  manifest_sha256=sha(DATA / 'manifest.json'), pipeline_sha256=sha(Path(__file__)),
                  tokenized_sha256=sha(output / 'train-tokenized.jsonl'), per_item=stats)
    write_json(output / 'representation-report.json', report)
    tokenizer.save_pretrained(output / 'tokenizer')
    print(json.dumps({k: report[k] for k in ('rows', 'truncated', 'length_percentiles', 'totals')}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('build')
    prep = sub.add_parser('prepare')
    prep.add_argument('--output', required=True, type=Path)
    prep.add_argument('--max-length', default=1024, type=int)
    args = p.parse_args()
    if args.command == 'build':
        build()
    else:
        prepare(args.output, args.max_length)


if __name__ == '__main__':
    main()
