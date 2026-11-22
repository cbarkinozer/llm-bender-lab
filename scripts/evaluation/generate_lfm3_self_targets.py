"""LFM3 answers prompts itself (vLLM, GPU pod): k samples per prompt in its native mode.

Input rows: {id, messages, thinking}. Output rows: {id, thinking, samples:[{raw_output, finish_reason, tokens}]}.
Presets follow the model card: direct answers T=0.1/top_k 50/rp 1.1; reasoning rows T=1.0/top_p .95/top_k 20.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
DIRECT = dict(temperature=0.1, top_p=1.0, top_k=50, repetition_penalty=1.1)
REASONING = dict(temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--seed', type=int, default=3407)
    args = parser.parse_args()
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams
    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    rows = [json.loads(s) for s in args.prompts.read_text(encoding='utf-8').splitlines()]
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    ids, params = [], []
    for row in rows:
        text = tokenizer.apply_chat_template(row['messages'], tokenize=False, add_generation_prompt=True,
                                             enable_thinking=row['thinking'])
        assert text.endswith('<think>' if row['thinking'] else '<think></think>')
        ids.append(dict(prompt_token_ids=tokenizer(text, add_special_tokens=False)['input_ids']))
        params.append(SamplingParams(n=args.k, max_tokens=6144 if row['thinking'] else 1536, seed=args.seed,
                                     stop_token_ids=eos, ignore_eos=True, detokenize=False,
                                     **(REASONING if row['thinking'] else DIRECT)))
    llm = LLM(model=base['repo'], revision=base['revision'], code_revision=base['revision'], dtype='bfloat16',
              max_model_len=12288, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=32, seed=args.seed,
              trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    outputs = llm.generate(ids, params)
    with args.output.open('w', encoding='utf-8') as stream:
        for row, out in zip(rows, outputs):
            samples = []
            for candidate in out.outputs:
                tokens = list(candidate.token_ids)
                samples.append(dict(raw_output=tokenizer.decode(tokens, skip_special_tokens=False), tokens=len(tokens),
                                    finish_reason='eos' if candidate.finish_reason == 'stop' else candidate.finish_reason))
            stream.write(json.dumps(dict(id=row['id'], thinking=row['thinking'], samples=samples), ensure_ascii=False) + '\n')
    meta = dict(prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(), k=args.k, seed=args.seed,
                model=base, direct=DIRECT, reasoning=REASONING, rows=len(rows))
    args.output.with_suffix('.meta.json').write_text(json.dumps(meta, indent=1) + '\n', encoding='utf-8')
    print('done', len(rows))


if __name__ == '__main__':
    main()
