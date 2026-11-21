"""Generate answers for LFM3 eval v2 packets with vLLM (GPU pod only).

Protocol (frozen in eval-v2/README.md): native chat template, `tools=` passed to the template for
tool rows, model-card sampling presets per family, thinking on or off, one answers file per seed.
Scoring is done separately by score_lfm3_eval_v2.py from the saved raw outputs.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/turkish-capability/lfm3-1.7b/eval-v2'
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
# Model card presets (LiquidAI/LFM3-1.7B): general T=0.1/top_k 50/rp 1.1; math and STEM T=1.0/top_p .95/top_k 20.
PRESETS = {
    'general': dict(temperature=0.1, top_p=1.0, top_k=50, repetition_penalty=1.1),
    'math': dict(temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0),
    'greedy': dict(temperature=0.0, top_p=1.0, top_k=-1, repetition_penalty=1.0),
}
FAMILY_PRESET = {'math': 'math', 'symbolic': 'math', 'toolcall': 'general'}
MAX_MODEL_LEN = 12288


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, help='Describes the model and mode, e.g. base-think-off')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', help='HF repo id or local merged-model directory (default: pinned base)')
    parser.add_argument('--revision', help='Revision for --model when it is a Hub repo')
    parser.add_argument('--thinking', choices=['on', 'off'], required=True)
    parser.add_argument('--seeds', default='3407', help='Comma-separated sampling seeds')
    parser.add_argument('--preset', choices=['card', 'greedy'], default='card',
                        help='card = per-family model-card presets; greedy = temperature 0 sensitivity check')
    parser.add_argument('--families', default='math,symbolic,toolcall')
    parser.add_argument('--limit-pairs', type=int, help='Smoke test: only the first N pair ids per family')
    parser.add_argument('--max-new-tokens', type=int)
    parser.add_argument('--max-num-seqs', type=int, default=32)
    parser.add_argument('--data-dir', type=Path, default=EXP / 'data-local')
    args = parser.parse_args()

    import torch
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    manifest = json.loads((EXP / 'manifest-core.json').read_text(encoding='utf-8'))
    wanted = set(args.families.split(','))
    rows = []
    for entry in manifest['packets']:
        blob = (args.data_dir / entry['file']).read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry['sha256']:
            raise ValueError(f'Packet checksum mismatch: {entry["file"]}')
        rows.extend(r for r in map(json.loads, blob.decode('utf-8').splitlines()) if r['family'] in wanted)
    if args.limit_pairs:
        keep = {}
        for r in rows:
            keep.setdefault(r['family'], [])
            if r['pair_id'] not in keep[r['family']] and len(keep[r['family']]) < args.limit_pairs:
                keep[r['family']].append(r['pair_id'])
        rows = [r for r in rows if r['pair_id'] in keep[r['family']]]
    ids = [r['id'] for r in rows]
    assert rows and len(ids) == len(set(ids)), 'Packet rows missing or ids not unique'

    thinking = args.thinking == 'on'
    max_new = args.max_new_tokens or (8192 if thinking else 2048)
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    prompts = []
    for r in rows:
        text = tokenizer.apply_chat_template(r['messages'], tools=r.get('tools'), tokenize=False,
                                             add_generation_prompt=True, enable_thinking=thinking)
        token_ids = tokenizer(text, add_special_tokens=False)['input_ids']
        assert len(token_ids) + max_new <= MAX_MODEL_LEN, (r['id'], len(token_ids))
        prompts.append(dict(text=text, ids=token_ids))
    sample_tokens = prompts[0]['text'][-80:]
    assert sample_tokens.endswith('<think>' if thinking else '<think></think>'), sample_tokens

    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'],
                       dtype='bfloat16', max_model_len=MAX_MODEL_LEN, gpu_memory_utilization=0.85,
                       enforce_eager=True, max_num_seqs=args.max_num_seqs, seed=3407, trust_remote_code=True,
                       generation_config='vllm', enable_prefix_caching=False)
    revision = args.revision or (None if args.model else base['revision'])
    if revision:
        engine_args.update(revision=revision, code_revision=revision if not args.model else None)
    engine_args = {k: v for k, v in engine_args.items() if v is not None}

    args.output_dir.mkdir(parents=True, exist_ok=False)
    run = dict(name=args.name, status='initializing', thinking=args.thinking, model=model_id, revision=revision,
               base_model=base, preset_mode=args.preset, family_presets=FAMILY_PRESET, presets=PRESETS,
               max_new_tokens=max_new, seeds=[int(s) for s in args.seeds.split(',')], families=sorted(wanted),
               rows=len(rows), limit_pairs=args.limit_pairs, engine_args=engine_args, eos_token_ids=eos,
               chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
               packets=manifest['packets'], builder_sha256=manifest['builder_sha256'],
               packages={n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'vllm')},
               gpu=torch.cuda.get_device_name(), started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))

    def save():
        (args.output_dir / 'run-manifest.json').write_text(json.dumps(run, indent=1) + '\n', encoding='utf-8')
    save()
    try:
        llm = LLM(**engine_args)
        run['status'] = 'running'
        save()
        for seed in run['seeds']:
            started = time.perf_counter()
            params = []
            for r in rows:
                preset = PRESETS['greedy' if args.preset == 'greedy' else FAMILY_PRESET[r['family']]]
                params.append(SamplingParams(max_tokens=max_new, seed=seed, stop_token_ids=eos, ignore_eos=True,
                                             detokenize=False, **preset))
            outputs = llm.generate([dict(prompt_token_ids=p['ids']) for p in prompts], params)
            with (args.output_dir / f'answers-seed{seed}.jsonl').open('w', encoding='utf-8') as f:
                for r, p, out in zip(rows, prompts, outputs):
                    result = out.outputs[0]
                    tokens = list(result.token_ids)
                    f.write(json.dumps(dict(
                        id=r['id'], family=r['family'], language=r['language'], seed=seed,
                        raw_output=tokenizer.decode(tokens, skip_special_tokens=False),
                        generated_tokens=len(tokens), prompt_tokens=len(p['ids']),
                        finish_reason='eos' if result.finish_reason == 'stop' else result.finish_reason,
                        hit_max_new_tokens=len(tokens) >= max_new), ensure_ascii=False) + '\n')
            run.setdefault('wall_seconds', {})[str(seed)] = round(time.perf_counter() - started, 1)
            save()
            print(f'seed {seed} done: {len(rows)} rows in {run["wall_seconds"][str(seed)]}s', flush=True)
        run['status'] = 'completed'
    except BaseException:
        run['status'] = 'failed'
        raise
    finally:
        run['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        save()


if __name__ == '__main__':
    main()
