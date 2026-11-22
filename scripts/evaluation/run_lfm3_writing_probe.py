"""Generate answers to the 40 native Turkish writing prompts (GPU pod only), thinking off, model-card general preset.

  python run_lfm3_writing_probe.py --name base --output-dir DIR [--model DIR] [--seeds 3407,3408]
Scoring and the blind review sheet are local (score_lfm3_writing_probe.py).
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
PROMPTS = BASE / 'eval-v2/writing-prompts-tr.jsonl'
BASE_CONFIG = BASE / 'exp-000-baseline/config-planned.json'
PRESET = dict(temperature=0.1, top_p=1.0, top_k=50, repetition_penalty=1.1)  # model card, general
MAX_NEW = 800


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model')
    parser.add_argument('--seeds', default='3407')
    args = parser.parse_args()

    import torch
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    rows = [json.loads(x) for x in PROMPTS.read_text(encoding='utf-8').splitlines()]
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    ids = [tokenizer(tokenizer.apply_chat_template([dict(role='user', content=r['prompt'])], tokenize=False,
                                                   add_generation_prompt=True, enable_thinking=False),
                     add_special_tokens=False)['input_ids'] for r in rows]
    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'], dtype='bfloat16',
                       max_model_len=4096, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=64, seed=3407,
                       trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    if not args.model:
        engine_args.update(revision=base['revision'], code_revision=base['revision'])
    args.output_dir.mkdir(parents=True, exist_ok=False)
    llm = LLM(**engine_args)
    seeds = [int(s) for s in args.seeds.split(',')]
    jobs = [(r, p, s) for r, p in zip(rows, ids) for s in seeds]
    outs = llm.generate([dict(prompt_token_ids=p) for _, p, _ in jobs],
                        [SamplingParams(max_tokens=MAX_NEW, seed=s, stop_token_ids=eos, ignore_eos=True,
                                        detokenize=False, **PRESET) for _, _, s in jobs])
    with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8') as f:
        for (r, _, s), out in zip(jobs, outs):
            res = out.outputs[0]
            tokens = list(res.token_ids)
            f.write(json.dumps(dict(
                id=r['id'], seed=s, raw_output=tokenizer.decode(tokens, skip_special_tokens=False),
                generated_tokens=len(tokens), finish_reason='eos' if res.finish_reason == 'stop' else res.finish_reason,
                hit_max_new_tokens=len(tokens) >= MAX_NEW), ensure_ascii=False) + '\n')
    (args.output_dir / 'run-manifest.json').write_text(json.dumps(dict(
        name=args.name, model=model_id, base_model=base, preset=PRESET, max_new_tokens=MAX_NEW, seeds=seeds,
        prompts_sha256=hashlib.sha256(PROMPTS.read_bytes()).hexdigest(), gpu=torch.cuda.get_device_name(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), finished=time.strftime('%Y-%m-%dT%H:%M:%S%z')),
        indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
