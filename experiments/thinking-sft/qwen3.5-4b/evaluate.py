"""Save one original thinking-enabled attempt per prompt; never sends answer keys.

HF/CUDA is the primary baseline/candidate protocol. Local HTTP is development-only.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import urllib.request

from pipeline import ROOT, DATA, MODEL, REVISION, read_rows, sha, write_json, write_rows


def split_reasoning(raw):
    if '</think>' not in raw:
        return raw.removeprefix('<think>').strip(), ''
    reasoning, answer = raw.split('</think>', 1)
    return reasoning.removeprefix('<think>').strip(), answer.replace('<|im_end|>', '').strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend', choices=['hf', 'http'], default='hf')
    p.add_argument('--split', choices=['dev', 'test', 'regression'], default='dev')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--adapter', type=Path)
    p.add_argument('--base-url', default='http://127.0.0.1:18182')
    p.add_argument('--served-model', default='occam2-dev-base')
    p.add_argument('--gguf', type=Path, help='Required identity evidence for local development server')
    args = p.parse_args()
    if args.backend == 'http' and (args.split != 'dev' or args.adapter or not args.gguf):
        raise ValueError('HTTP is for pinned-GGUF development probes only; use HF for matched primary evaluation')
    if args.adapter and args.backend != 'hf':
        raise ValueError('Adapter evaluation requires HF backend')
    config = json.loads((ROOT / 'experiment-config.json').read_text())
    if args.split == 'test' and not config.get('data_selection_ready', False):
        raise ValueError('Failure-guided data revision is pending; do not freeze a baseline on the generic draft')
    settings = config['evaluation']
    prompt_file = DATA / 'test-prompts.jsonl' if args.split == 'test' else ROOT / f'{args.split}-prompts.jsonl'
    prompts = read_rows(prompt_file)
    if args.split == 'test' and len(prompts) != 20:
        raise ValueError('Expected exactly20 held-out prompts')
    if args.adapter:
        run_file = args.adapter.parent / 'run-manifest.json'
        training = json.loads(run_file.read_text())
        if training['mode'] != 'full' or not training['mechanical_pass']:
            raise ValueError('Only final completed full-run adapter may be evaluated on held-out tests')
        for name, digest in training['adapter_files_sha256'].items():
            if sha(args.adapter / name) != digest:
                raise ValueError('Adapter identity changed')
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = dict(complete=False, backend=args.backend, split=args.split, model=MODEL, revision=REVISION,
        condition='adapter' if args.adapter else 'base', settings=settings,
        config_sha256=sha(ROOT / 'experiment-config.json'), prompts_sha256=sha(prompt_file),
        evaluate_script_sha256=sha(Path(__file__)), platform=platform.platform(), items=0)
    write_json(args.output / 'evaluation-manifest.json', manifest)
    if args.backend == 'hf':
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, set_seed
        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise SystemExit('Primary evaluation requires CUDA BF16; use local HTTP for dev checks only.')
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
        model = Qwen3_5ForConditionalGeneration.from_pretrained(MODEL, revision=REVISION,
            dtype=torch.bfloat16, trust_remote_code=False, device_map={'': 0}, attn_implementation='sdpa')
        if args.adapter:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, args.adapter)
            manifest['training_manifest_sha256'] = sha(args.adapter.parent / 'run-manifest.json')
        model.eval()
        manifest.update(gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda,
            versions={k: importlib.metadata.version(k) for k in ['torch', 'transformers', 'peft']},
            template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest())
    else:
        manifest['gguf_sha256'] = sha(args.gguf)
        with urllib.request.urlopen(args.base_url + '/props', timeout=15) as response:
            props = json.load(response)
        if Path(props.get('model_path', '')).resolve() != args.gguf.resolve():
            raise ValueError('Server loaded a different GGUF')
        write_json(args.output / 'server-props.json', props)
    results = []
    try:
        for index, row in enumerate(prompts):
            if any(m['role'] == 'assistant' for m in row['messages']):
                raise ValueError('Evaluation must contain prompts only')
            start = time.monotonic()
            request = dict(model=args.served_model, messages=row['messages'],
                max_tokens=settings['max_new_tokens'], temperature=settings['temperature'],
                top_p=settings['top_p'], top_k=settings['top_k'], seed=settings['seed'] + index,
                repeat_penalty=settings['repetition_penalty'],
                chat_template_kwargs={'enable_thinking': True}, stream=False)
            if args.backend == 'hf':
                set_seed(settings['seed'] + index)
                text = tokenizer.apply_chat_template(row['messages'], tokenize=False,
                    add_generation_prompt=True, enable_thinking=True)
                inputs = tokenizer(text, add_special_tokens=False, return_tensors='pt').to('cuda')
                with torch.inference_mode():
                    sequence = model.generate(**inputs, do_sample=True,
                        max_new_tokens=settings['max_new_tokens'], temperature=settings['temperature'],
                        top_p=settings['top_p'], top_k=settings['top_k'],
                        repetition_penalty=settings['repetition_penalty'], use_cache=True)
                tokens = sequence[0, inputs['input_ids'].shape[-1]:].tolist()
                raw = tokenizer.decode(tokens, skip_special_tokens=False)
                reasoning, answer = split_reasoning(raw)
                eos = model.generation_config.eos_token_id
                eos = [eos] if isinstance(eos, int) else eos
                finish = 'stop' if tokens and tokens[-1] in (eos or []) else 'length'
                response = dict(raw_completion=raw, reasoning_content=reasoning, content=answer,
                    finish_reason=finish, generated_tokens=len(tokens), input_tokens=inputs['input_ids'].shape[-1],
                    rendered_prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
            else:
                req = urllib.request.Request(args.base_url + '/v1/chat/completions',
                    data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=600) as resp:
                    response = json.load(resp)
            results.append(dict(id=row['id'], category=row.get('category'),
                request=request, response=response, elapsed_s=time.monotonic()-start))
            write_rows(args.output / 'outputs.jsonl', results)
            print(f'{args.split}: saved {index+1}/{len(prompts)}', flush=True)
    finally:
        manifest.update(items=len(results), complete=len(results) == len(prompts),
                        outputs_sha256=sha(args.output / 'outputs.jsonl') if results else None)
        write_json(args.output / 'evaluation-manifest.json', manifest)


if __name__ == '__main__':
    main()
