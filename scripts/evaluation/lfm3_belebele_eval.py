"""Belebele reading comprehension, Turkish vs English on the same 900 items (human-translated, CC-BY-SA 4.0).

  run:   python lfm3_belebele_eval.py run --name base --output-dir DIR [--model DIR] [--limit N]   (GPU pod only)
  score: python lfm3_belebele_eval.py score --run-dir DIR [--run-dir DIR ...]
  compare: python lfm3_belebele_eval.py compare --a DIR --b DIR
Thinking is off, decoding is greedy, one pass. Two readings per item: the text the model generates (format failures count
as wrong) and the best of A-D by first-token log-probability (removes format effects, which matter for the CPT model).
Source files: facebook/belebele pinned revision, fetched into eval-v2/source-cache (ignored by Git).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
CACHE = BASE / 'eval-v2/source-cache'
BASE_CONFIG = BASE / 'exp-000-baseline/config-planned.json'
REVISION = '7899cdfa4e1e0d733fd77c848e2c273cb1d32be2'
SHA256 = {'eng_Latn': None, 'tur_Latn': None}  # filled by the run manifest; the revision pins the content
TEMPLATES = {
    'en': 'Read the passage and answer the question.\n\nPassage:\n{passage}\n\nQuestion: {question}\n\n{options}\n\n'
          'Answer with only the letter of the correct option.',
    'tr': 'Pasajı oku ve soruyu yanıtla.\n\nPasaj:\n{passage}\n\nSoru: {question}\n\n{options}\n\n'
          'Yalnızca doğru seçeneğin harfiyle yanıt ver.',
}
FILES = {'en': 'belebele-eng_Latn.jsonl', 'tr': 'belebele-tur_Latn.jsonl'}
LETTERS = 'ABCD'


def load_items():
    data = {}
    for lang, name in FILES.items():
        blob = (CACHE / name).read_bytes()
        data[lang] = (hashlib.sha256(blob).hexdigest(), [json.loads(x) for x in blob.decode('utf-8').splitlines()])
    en, tr = data['en'][1], data['tr'][1]
    assert len(en) == len(tr) == 900
    items = []
    for e, t in zip(en, tr):
        assert e['link'] == t['link'] and e['question_number'] == t['question_number'], 'EN/TR rows not aligned'
        assert e['correct_answer_num'] == t['correct_answer_num'], 'answer key mismatch'
        for lang, row in (('en', e), ('tr', t)):
            options = '\n'.join(f'{LETTERS[i]}. {row[f"mc_answer{i + 1}"]}' for i in range(4))
            user = TEMPLATES[lang].format(passage=row['flores_passage'], question=row['question'], options=options)
            items.append(dict(id=f'bel-{e["link"]}-{e["question_number"]}-{lang}', pair_id=f'{e["link"]}#{e["question_number"]}',
                              language=lang, gold=LETTERS[int(e['correct_answer_num']) - 1], user=user))
    return items, {lang: sha for lang, (sha, _) in data.items()}


def cmd_run(args):
    import torch
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    items, shas = load_items()
    if args.limit:
        keep = []
        for it in items:
            if it['pair_id'] not in keep and len(keep) < args.limit:
                keep.append(it['pair_id'])
        items = [it for it in items if it['pair_id'] in keep]
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    prompts = [tokenizer(tokenizer.apply_chat_template([dict(role='user', content=it['user'])], tokenize=False,
                                                       add_generation_prompt=True, enable_thinking=False),
                         add_special_tokens=False)['input_ids'] for it in items]
    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'], dtype='bfloat16',
                       max_model_len=4096, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=64, seed=3407,
                       trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    if not args.model:
        engine_args.update(revision=base['revision'], code_revision=base['revision'])
    args.output_dir.mkdir(parents=True, exist_ok=False)
    llm = LLM(**engine_args)
    outs = llm.generate([dict(prompt_token_ids=p) for p in prompts],
                        SamplingParams(max_tokens=8, temperature=0.0, logprobs=20, detokenize=True))
    with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8') as f:
        for it, out in zip(items, outs):
            res = out.outputs[0]
            first = {}
            for token_id, lp in (res.logprobs[0] if res.logprobs else {}).items():
                letter = (lp.decoded_token or '').strip().upper()
                if letter in tuple(LETTERS) and letter not in first:
                    first[letter] = lp.logprob
            f.write(json.dumps(dict(id=it['id'], pair_id=it['pair_id'], language=it['language'], gold=it['gold'],
                                    text=res.text, first_token_letter_logprobs=first), ensure_ascii=False) + '\n')
    (args.output_dir / 'run-manifest.json').write_text(json.dumps(dict(
        name=args.name, model=model_id, base_model=base, revision=REVISION, source_sha256=shas, items=len(items),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), gpu=torch.cuda.get_device_name()),
        indent=1) + '\n', encoding='utf-8')


def read_letter(text):
    m = re.match(r'\s*\**\(?([ABCD])\b', text.strip(), re.I)
    return m.group(1).upper() if m else None


def per_item(run_dir):
    rows = {}
    for line in (run_dir / 'answers.jsonl').read_text(encoding='utf-8').splitlines():
        a = json.loads(line)
        lp = a['first_token_letter_logprobs']
        restricted = max(lp, key=lp.get) if lp else None
        generated = read_letter(a['text'])
        rows[a['id']] = dict(pair_id=a['pair_id'], language=a['language'], generated=generated == a['gold'],
                             parsed=generated is not None, restricted=restricted == a['gold'])
    return rows


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(c - h, 4), round(c + h, 4)


def summarize(run_dir):
    rows = per_item(run_dir)
    out = {}
    for lang in ('en', 'tr'):
        sel = [r for r in rows.values() if r['language'] == lang]
        n = len(sel)
        out[lang] = dict(n=n, generated_acc=round(sum(r['generated'] for r in sel) / n, 4),
                         generated_ci=wilson(sum(r['generated'] for r in sel), n),
                         restricted_acc=round(sum(r['restricted'] for r in sel) / n, 4),
                         restricted_ci=wilson(sum(r['restricted'] for r in sel), n),
                         parse_rate=round(sum(r['parsed'] for r in sel) / n, 4))
    return out, rows


def boot_delta(a, b, reps=4000, seed=3407):
    keys = sorted(a)
    diffs = [float(b[k]) - float(a[k]) for k in keys]
    rng = random.Random(seed)
    means = sorted(statistics.mean(diffs[rng.randrange(len(diffs))] for _ in diffs) for _ in range(reps))
    return round(statistics.mean(diffs), 4), round(means[int(.025 * reps)], 4), round(means[int(.975 * reps) - 1], 4)


def cmd_score(args):
    for run_dir in args.run_dir:
        summary, rows = summarize(run_dir)
        by_pair = {lang: {r['pair_id']: r['restricted'] for r in rows.values() if r['language'] == lang} for lang in ('en', 'tr')}
        summary['tr_minus_en_restricted'] = boot_delta(by_pair['en'], by_pair['tr'])
        (run_dir / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
        print(run_dir.name, json.dumps(summary))


def cmd_compare(args):
    (_, ra), (_, rb) = summarize(args.a), summarize(args.b)
    for lang in ('en', 'tr'):
        for key in ('restricted', 'generated'):
            x = {r['pair_id']: r[key] for r in ra.values() if r['language'] == lang}
            y = {r['pair_id']: r[key] for r in rb.values() if r['language'] == lang}
            print(f'{lang} {key}: b-a = {boot_delta(x, y)}')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('run')
    p.add_argument('--name', required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--model')
    p.add_argument('--limit', type=int)
    p.set_defaults(func=cmd_run)
    p = sub.add_parser('score')
    p.add_argument('--run-dir', type=Path, action='append', required=True)
    p.set_defaults(func=cmd_score)
    p = sub.add_parser('compare')
    p.add_argument('--a', type=Path, required=True)
    p.add_argument('--b', type=Path, required=True)
    p.set_defaults(func=cmd_compare)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
