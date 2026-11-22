"""Understanding diagnostic for LFM3 (GPU pod only): where does the Turkish math gap come from?

Same 152 paired GSM8K items as eval v2, crossed over problem language, reply language and a translate-first pipeline:
  A en problem, reply en (reference)      D tr problem, reply tr (eval v2 prompt, current result)
  B en problem, reply tr (writing cost)   F tr problem, restate in English first, reply en
  C tr problem, reply en (reading cost)   G tr problem -> model translates -> solves the English text (no training)
Several sampling seeds per cell. Scoring is separate (score_lfm3_understanding_diagnostic.py).
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/turkish-capability/lfm3-1.7b/eval-v2'
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
MATH_PRESET = dict(temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0)  # model card, math
GREEDY = dict(temperature=0.0, top_p=1.0, top_k=-1, repetition_penalty=1.0)
MAX_MODEL_LEN = 12288
EN_SPLIT, TR_SPLIT = '\n\nSolve it step by step.', '\n\nAdım adım çöz.'
EN_END = 'End your reply with a line of the form "Final answer: <number>".'
WRAPPERS = {
    'B': 'Solve it step by step. Write your whole reply in Turkish. End your reply with a line of the form "Nihai cevap: <number>".',
    'C': f'Solve it step by step. Write your whole reply in English. {EN_END}',
    'F': f'First restate the problem in English in one or two sentences, then solve it step by step in English. {EN_END}',
    'G': f'Solve it step by step. {EN_END}',
}
TRANSLATE = 'Translate the following Turkish text into English. Output only the English translation, nothing else.\n\n{body}'
ALL_CONDITIONS = 'A,B,C,D,F,G'
NUMBERS = re.compile(r'\d+(?:[.,]\d+)*')


def numbers_of(text):
    return sorted(re.sub(r'[.,]', '', n) for n in NUMBERS.findall(text))


def load_pairs(data_dir, manifest, limit):
    rows = []
    for entry in manifest['packets']:
        blob = (data_dir / entry['file']).read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry['sha256']:
            raise ValueError(f'Packet checksum mismatch: {entry["file"]}')
        rows.extend(r for r in map(json.loads, blob.decode('utf-8').splitlines()) if r['family'] == 'math')
    pairs = {}
    for r in rows:
        pairs.setdefault(r['pair_id'], {})[r['language']] = r
    items = []
    for pair_id in sorted(pairs):
        en, tr = pairs[pair_id]['en'], pairs[pair_id]['tr']
        assert en['gold'] == tr['gold'], pair_id
        en_text, tr_text = en['messages'][0]['content'], tr['messages'][0]['content']
        assert EN_SPLIT in en_text and TR_SPLIT in tr_text, pair_id
        items.append(dict(pair_id=pair_id, gold=en['gold'], en_prompt=en_text, tr_prompt=tr_text,
                          tr_body=tr_text.split(TR_SPLIT)[0]))
    return items[:limit] if limit else items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', help='Local merged-model directory (default: pinned base)')
    parser.add_argument('--thinking', choices=['on', 'off'], required=True)
    parser.add_argument('--seeds', default='3407,3408,3409,3410')
    parser.add_argument('--conditions', default=ALL_CONDITIONS)
    parser.add_argument('--limit-pairs', type=int)
    parser.add_argument('--max-num-seqs', type=int, default=96)
    parser.add_argument('--data-dir', type=Path, default=EXP / 'data-local')
    args = parser.parse_args()

    import torch
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    manifest = json.loads((EXP / 'manifest-core.json').read_text(encoding='utf-8'))
    items = load_pairs(args.data_dir, manifest, args.limit_pairs)
    conditions = args.conditions.split(',')
    assert set(conditions) <= set(ALL_CONDITIONS.split(',')), conditions
    seeds = [int(s) for s in args.seeds.split(',')]
    thinking = args.thinking == 'on'
    max_new = 8192 if thinking else 2048
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]

    def encode(user_text, think):
        text = tokenizer.apply_chat_template([dict(role='user', content=user_text)], tokenize=False,
                                             add_generation_prompt=True, enable_thinking=think)
        assert text.endswith('<think>' if think else '<think></think>'), text[-60:]
        ids = tokenizer(text, add_special_tokens=False)['input_ids']
        assert len(ids) + max_new <= MAX_MODEL_LEN
        return ids

    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'], dtype='bfloat16',
                       max_model_len=MAX_MODEL_LEN, gpu_memory_utilization=0.85, enforce_eager=True,
                       max_num_seqs=args.max_num_seqs, seed=3407, trust_remote_code=True, generation_config='vllm',
                       enable_prefix_caching=False)
    if not args.model:
        engine_args.update(revision=base['revision'], code_revision=base['revision'])
    args.output_dir.mkdir(parents=True, exist_ok=False)
    run = dict(name=args.name, status='initializing', thinking=args.thinking, model=model_id, base_model=base,
               conditions=conditions, seeds=seeds, pairs=len(items), max_new_tokens=max_new, preset=MATH_PRESET,
               wrappers=WRAPPERS, translate_prompt=TRANSLATE, builder_sha256=manifest['builder_sha256'],
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), engine_args=engine_args,
               packages={n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'vllm')},
               gpu=torch.cuda.get_device_name(), started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))

    def save():
        (args.output_dir / 'run-manifest.json').write_text(json.dumps(run, indent=1) + '\n', encoding='utf-8')
    save()
    try:
        llm = LLM(**engine_args)
        run['status'] = 'running'
        translations = {}
        if 'G' in conditions:  # stage 1: greedy translation with thinking off, one per item
            outs = llm.generate([dict(prompt_token_ids=encode(TRANSLATE.format(body=i['tr_body']), False))
                                 for i in items],
                                SamplingParams(max_tokens=768, stop_token_ids=eos, detokenize=True, **GREEDY))
            for item, out in zip(items, outs):
                text = out.outputs[0].text.strip()
                translations[item['pair_id']] = dict(
                    text=text, numbers_preserved=numbers_of(text) == numbers_of(item['tr_body']),
                    finished=out.outputs[0].finish_reason == 'stop')
            (args.output_dir / 'translations.json').write_text(
                json.dumps(translations, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print('translated', len(translations), 'numbers preserved',
                  sum(t['numbers_preserved'] for t in translations.values()), flush=True)
        jobs = []
        for item in items:
            for cond in conditions:
                if cond == 'A':
                    user = item['en_prompt']
                elif cond == 'D':
                    user = item['tr_prompt']
                elif cond == 'B':
                    user = item['en_prompt'].split(EN_SPLIT)[0] + '\n\n' + WRAPPERS['B']
                elif cond == 'G':
                    user = translations[item['pair_id']]['text'] + '\n\n' + WRAPPERS['G']
                else:
                    user = item['tr_body'] + '\n\n' + WRAPPERS[cond]
                ids = encode(user, thinking)
                for seed in seeds:
                    jobs.append(dict(item=item, cond=cond, seed=seed, ids=ids))
        started = time.perf_counter()
        outputs = llm.generate(
            [dict(prompt_token_ids=j['ids']) for j in jobs],
            [SamplingParams(max_tokens=max_new, seed=j['seed'], stop_token_ids=eos, ignore_eos=True,
                            detokenize=False, **MATH_PRESET) for j in jobs])
        with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8') as f:
            for j, out in zip(jobs, outputs):
                result = out.outputs[0]
                tokens = list(result.token_ids)
                f.write(json.dumps(dict(
                    id=f'{j["item"]["pair_id"]}-{j["cond"]}-s{j["seed"]}', pair_id=j['item']['pair_id'],
                    condition=j['cond'], seed=j['seed'], gold=j['item']['gold'],
                    raw_output=tokenizer.decode(tokens, skip_special_tokens=False), generated_tokens=len(tokens),
                    finish_reason='eos' if result.finish_reason == 'stop' else result.finish_reason,
                    hit_max_new_tokens=len(tokens) >= max_new), ensure_ascii=False) + '\n')
        run['wall_seconds'] = round(time.perf_counter() - started, 1)
        run['generations'] = len(jobs)
        run['status'] = 'completed'
        print(f'done: {len(jobs)} generations in {run["wall_seconds"]}s', flush=True)
    except BaseException:
        run['status'] = 'failed'
        raise
    finally:
        run['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        save()


if __name__ == '__main__':
    main()
