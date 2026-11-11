"""Sequential BF16 LFM3 evaluation on the restored historical CETVEL cohort.

GPU runner, not a validated environment installer. Model custom code must be
reviewed before using --allow-reviewed-remote-code. No silent input truncation.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--limit', type=int, default=0, help='0 = all; positive = diagnostic only')
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--allow-reviewed-remote-code', action='store_true')
    args = parser.parse_args()
    if not args.allow_reviewed_remote_code:
        parser.error('Review pinned model Python files first; then explicitly enable custom code')
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
    class Guard(StoppingCriteria):
        def __init__(self, prompt_length):
            self.prompt_length = prompt_length
            self.started = time.perf_counter()
            self.reason = None

        def __call__(self, input_ids, scores, **kwargs):
            tail = input_ids[0, self.prompt_length:].tolist()
            if time.perf_counter() - self.started >= 180:
                self.reason = 'timeout'
            if len(tail) >= 128:
                for width in (8, 16, 32):
                    if tail[-width:] * 4 == tail[-width * 4:]:
                        self.reason = 'exact_loop'
            return self.reason is not None
    config = json.loads((args.experiment_dir / 'config-planned.json').read_text(encoding='utf-8'))
    packet = args.experiment_dir / 'data-local/questions-500.jsonl'
    blob = packet.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != config['historical_comparison']['questions_sha256']:
        raise ValueError('Evaluation packet hash mismatch')
    rows = [json.loads(line) for line in blob.decode('utf-8').splitlines()]
    if len(rows) != 500 or args.limit < 0:
        raise ValueError('Expected 500 rows and a nonnegative diagnostic limit')
    if args.limit:
        # Round-robin diagnostic includes every task before additional examples.
        tasks = list(dict.fromkeys(r['task'] for r in rows))
        groups = [[r for r in rows if r['task'] == task] for task in tasks]
        rows = [r for group in zip(*groups) for r in group][:args.limit]
    model_cfg = config['model']
    torch.manual_seed(3407)
    tokenizer = AutoTokenizer.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'], trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_cfg['repo'], revision=model_cfg['revision'],
        code_revision=model_cfg['revision'], trust_remote_code=True, dtype=torch.bfloat16).to('cuda').eval()
    adapter_hashes = {}
    if args.adapter:
        from peft import PeftModel
        for path in sorted(args.adapter.iterdir()):
            if path.is_file():
                adapter_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        model = PeftModel.from_pretrained(model, str(args.adapter)).eval()
    if not tokenizer.chat_template:
        raise ValueError('Native chat template missing')
    eos = model.generation_config.eos_token_id
    if eos is None:
        raise ValueError('Model EOS missing; do not substitute Qwen token IDs')
    eos_ids = eos if isinstance(eos, list) else [eos]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = dict(status='running', diagnostic=bool(args.limit), model=model_cfg,
        adapter_hashes=adapter_hashes,
        questions_sha256=digest, expected_count=len(rows), seed=3407,
        chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
        eos_token_ids=eos_ids, decoding=dict(do_sample=False, repetition_penalty=1.05,
        max_new_tokens=4096, context_budget=8192, enable_thinking=False),
        packages={name: importlib.metadata.version(name) for name in ('torch', 'transformers')},
        gpu=torch.cuda.get_device_name(), count=0)
    def save():
        (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8') as stream:
            for row in rows:
                rendered = tokenizer.apply_chat_template(row['messages'], tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
                inputs = tokenizer(rendered, add_special_tokens=False, return_tensors='pt').to('cuda')
                count = inputs.input_ids.shape[1]
                if count + 4096 > 8192:
                    raise ValueError(f"Input exceeds frozen context budget: {row['id']}")
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                start = time.perf_counter()
                guard = Guard(count)
                with torch.inference_mode():
                    output = model.generate(**inputs, do_sample=False, max_new_tokens=4096,
                        repetition_penalty=1.05, eos_token_id=eos_ids,
                        stopping_criteria=StoppingCriteriaList([guard]),
                        pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_ids[0])
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - start
                tokens = output[0, count:].tolist()
                prediction = tokenizer.decode(tokens, skip_special_tokens=True)
                record = dict(row, prediction=prediction, raw_output=prediction, rendered_prompt=rendered,
                    prompt_token_ids=inputs.input_ids[0].tolist(), generated_token_ids=tokens,
                    generated_tokens=len(tokens), generation_seconds=elapsed,
                    peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    hit_max_new_tokens=len(tokens) >= 4096,
                    finish_reason=guard.reason or ('eos' if tokens and tokens[-1] in eos_ids else 'length_or_other'))
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
                manifest['count'] += 1
                save()
                print(f"{manifest['count']}/{len(rows)} {row['id']} {record['finish_reason']}", flush=True)
        manifest['status'] = 'completed'
    except BaseException:
        manifest['status'] = 'failed'
        raise
    finally:
        save()


if __name__ == '__main__':
    main()
