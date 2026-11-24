"""Sample answers of the Turkish SFT model (exp-021) to the DPO prompts (GPU pod only, vLLM).

  python sample_tr_dpo_candidates.py --prompts prompts-tr-dpo.jsonl --output-dir DIR \
      [--model cbarkinozer/LFM3-1.7B-Turkish-SFT] [--temperatures 0.1,0.7,0.7,0.7]

Thinking is off (the mode the writing probe measured). Sample 0 uses the model card's general preset (temperature 0.1), the others a
warmer temperature so the answers differ; every sample keeps its seed and temperature. Answers that hit the token cap are kept
(an unfinished answer is one of the weaknesses). The result is `answers.jsonl` plus `run-manifest.json`.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

BASE_REPO = 'LiquidAI/LFM3-1.7B'
BASE_REVISION = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'
TOP_P, TOP_K, REPETITION_PENALTY = 1.0, 50, 1.1  # model card general preset except the temperature
MAX_NEW = 800


def read_jsonl(path):
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompts', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', default='cbarkinozer/LFM3-1.7B-Turkish-SFT')
    parser.add_argument('--model-revision', default='6e4f0b7658b115a28da971f82ff4009f63bed612',
                        help='commit of the model repo (the published exp-021 weights; the manifest records the commit that was used)')
    parser.add_argument('--temperatures', default='0.1,0.7,0.7,0.7')
    parser.add_argument('--seed', type=int, default=3407)
    parser.add_argument('--limit', type=int, default=None, help='first N prompts (smoke test)')
    args = parser.parse_args()

    import torch
    from huggingface_hub import model_info
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    rows = read_jsonl(args.prompts)[:args.limit]
    temperatures = [float(t) for t in args.temperatures.split(',')]
    tokenizer = AutoTokenizer.from_pretrained(BASE_REPO, revision=BASE_REVISION)
    eos = GenerationConfig.from_pretrained(BASE_REPO, revision=BASE_REVISION).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    ids = [tokenizer(tokenizer.apply_chat_template([dict(role='user', content=r['prompt'])], tokenize=False,
                                                   add_generation_prompt=True, enable_thinking=False),
                     add_special_tokens=False)['input_ids'] for r in rows]
    commit = model_info(args.model, revision=args.model_revision).sha if '/' in args.model and not Path(args.model).exists() else None
    args.output_dir.mkdir(parents=True, exist_ok=False)
    llm = LLM(model=args.model, revision=args.model_revision or commit, tokenizer=BASE_REPO, tokenizer_revision=BASE_REVISION,
              dtype='bfloat16', max_model_len=8192, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=64,
              seed=args.seed, trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    jobs = [(r, p, k, t) for r, p in zip(rows, ids) for k, t in enumerate(temperatures)]
    outs = llm.generate([dict(prompt_token_ids=p) for _, p, _, _ in jobs],
                        [SamplingParams(max_tokens=MAX_NEW, seed=args.seed + 1000 * k, temperature=t, top_p=TOP_P, top_k=TOP_K,
                                        repetition_penalty=REPETITION_PENALTY, stop_token_ids=eos, ignore_eos=True,
                                        detokenize=False) for _, _, k, t in jobs])
    with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8', newline='\n') as handle:
        for (r, _, k, t), out in zip(jobs, outs):
            res = out.outputs[0]
            tokens = list(res.token_ids)
            handle.write(json.dumps(dict(
                id=r['id'], sample=k, temperature=t, seed=args.seed + 1000 * k,
                raw_output=tokenizer.decode(tokens, skip_special_tokens=False), generated_tokens=len(tokens),
                finish_reason='eos' if res.finish_reason == 'stop' else res.finish_reason,
                hit_max_new_tokens=len(tokens) >= MAX_NEW), ensure_ascii=False) + '\n')
    (args.output_dir / 'run-manifest.json').write_text(json.dumps(dict(
        model=args.model, model_commit=args.model_revision or commit, base_model=BASE_REPO, base_revision=BASE_REVISION,
        temperatures=temperatures, top_p=TOP_P, top_k=TOP_K, repetition_penalty=REPETITION_PENALTY, max_new_tokens=MAX_NEW,
        thinking='off', prompts=len(rows), prompts_sha256=hashlib.sha256(args.prompts.read_bytes()).hexdigest(),
        gpu=torch.cuda.get_device_name(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        finished=time.strftime('%Y-%m-%dT%H:%M:%S%z')), indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
