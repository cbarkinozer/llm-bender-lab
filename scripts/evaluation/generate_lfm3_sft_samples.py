"""SFT core v01: LFM3 answers rendered prompts itself (vLLM, GPU pod). k samples per prompt, resumable, chunked.

Input rows (from `lfm3_sft_core.py render`): {id, messages, tools?, thinking, category, check}.
Output rows: {id, thinking, samples:[{raw_output, tokens, finish_reason}]}, appended chunk by chunk; ids already in the
output file are skipped, so a crashed run continues where it stopped.
Presets (model card): math rows T=1.0/top_p .95/top_k 20/rp 1.0 in both thinking modes (as eval v2); code and tool rows
T=0.1/top_k 50/rp 1.1. No length cap other than the token budget (owner assumption: thinking on, 8k+ contexts).
Unlike exp-016 nothing is shortened or filtered here; selection happens in the verify and build steps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
GENERAL = dict(temperature=0.1, top_p=1.0, top_k=50, repetition_penalty=1.1)
REASONING = dict(temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0)
MAX_MODEL_LEN = 12288


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', help='local merged model path; default is the pinned base')
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--seed', type=int, default=3407)
    parser.add_argument('--max-new-on', type=int, default=8192)
    parser.add_argument('--max-new-off', type=int, default=2048)
    parser.add_argument('--chunk', type=int, default=200)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--k-for', action='append', default=[], metavar='CATEGORY=K',
                        help='more samples for one category, e.g. tr_general=8 (best-of-N selection later)')
    args = parser.parse_args()
    k_by_category = {c: int(k) for c, k in (item.split('=') for item in args.k_for)}
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    rows = [json.loads(s) for s in args.prompts.read_text(encoding='utf-8').split('\n') if s.strip()]
    if args.limit:
        rows = rows[:args.limit]
    done = set()
    if args.output.exists():
        done = {json.loads(s)['id'] for s in args.output.read_text(encoding='utf-8').split('\n') if s.strip()}
    todo = [r for r in rows if r['id'] not in done]
    print(f'{len(rows)} prompts, {len(done)} done, {len(todo)} to do', flush=True)
    if not todo:
        return
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'], dtype='bfloat16',
                       max_model_len=MAX_MODEL_LEN, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=128,
                       seed=args.seed, trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    if not args.model:
        engine_args.update(revision=base['revision'], code_revision=base['revision'])
    llm = LLM(**engine_args)
    started = time.perf_counter()
    for start in range(0, len(todo), args.chunk):
        chunk = todo[start:start + args.chunk]
        ids, params = [], []
        for row in chunk:
            text = tokenizer.apply_chat_template(row['messages'], tools=row.get('tools'), tokenize=False,
                                                 add_generation_prompt=True, enable_thinking=row['thinking'])
            assert text.endswith('<think>' if row['thinking'] else '<think></think>'), (row['id'], text[-40:])
            prompt_ids = tokenizer(text, add_special_tokens=False)['input_ids']
            budget = args.max_new_on if row['thinking'] else args.max_new_off
            assert len(prompt_ids) + budget <= MAX_MODEL_LEN, row['id']
            ids.append(dict(prompt_token_ids=prompt_ids))
            preset = REASONING if row['category'].startswith('math') else GENERAL
            params.append(SamplingParams(n=k_by_category.get(row['category'], args.k), max_tokens=budget, seed=args.seed, stop_token_ids=eos, ignore_eos=True,
                                         detokenize=False, **preset))
        outputs = llm.generate(ids, params)
        with args.output.open('a', encoding='utf-8') as stream:
            for row, out in zip(chunk, outputs):
                samples = []
                for candidate in out.outputs:
                    tokens = list(candidate.token_ids)
                    samples.append(dict(raw_output=tokenizer.decode(tokens, skip_special_tokens=False), tokens=len(tokens),
                                        finish_reason='eos' if candidate.finish_reason == 'stop' else candidate.finish_reason))
                stream.write(json.dumps(dict(id=row['id'], thinking=row['thinking'], samples=samples), ensure_ascii=False) + '\n')
        print(f'{start + len(chunk)}/{len(todo)} prompts, {round(time.perf_counter() - started)}s', flush=True)
    meta = dict(prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(), k=args.k, seed=args.seed, model=model_id,
                base=base, general=GENERAL, reasoning=REASONING, max_new_on=args.max_new_on, max_new_off=args.max_new_off,
                engine_args=engine_args, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.with_suffix('.meta.json').write_text(json.dumps(meta, indent=1) + '\n', encoding='utf-8')
    print('done', len(todo), flush=True)


if __name__ == '__main__':
    main()
