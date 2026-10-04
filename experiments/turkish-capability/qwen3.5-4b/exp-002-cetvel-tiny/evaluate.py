"""Run one canonical BF16 base or verified final exp016/F arm; no training/W&B."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PAIR = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft'
sys.path.insert(0, str(PAIR))
from evaluate_models import repeated_tail


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['base', 'F'], required=True)
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((HERE / 'config.json').read_text())
    frozen = json.loads((HERE / 'data-v1/manifest.json').read_text())
    questions = HERE / 'data-v1/questions-100.jsonl'
    assert sha(questions) == frozen['questions_sha256']
    assert frozen['near_duplicate_candidates'] == 0
    assert bool(args.adapter) == (args.arm == 'F')
    assert not args.output_dir.exists(), 'Do not overwrite a run'
    if args.adapter:
        for name, expected in config['adapter_hashes'].items():
            assert sha(args.adapter / name) == expected, ('Wrong adapter', name)
    from unsloth import FastLanguageModel
    import torch
    from peft import PeftModel
    from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, set_seed
    set_seed(config['seed'])
    model, _ = FastLanguageModel.from_pretrained(model_name=config['model'], revision=config['revision'],
        max_seq_length=config['max_context_tokens'], load_in_4bit=False, load_in_16bit=True,
        full_finetuning=False)
    if args.adapter:
        model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
        assert any('lora_' in name for name, _ in model.named_parameters())
    FastLanguageModel.for_inference(model)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(config['model'], revision=config['revision'])
    data = [json.loads(line) for line in questions.read_text(encoding='utf-8').splitlines()]
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    assert eos and len(data) == 100
    encoded = [tokenizer.apply_chat_template(row['messages'], tokenize=True,
               add_generation_prompt=True, enable_thinking=False, return_dict=False) for row in data]
    assert all(len(ids) + config['max_new_tokens'] <= config['max_context_tokens'] for ids in encoded), (
        'Context overflow; do not truncate inputs or quietly alter the frozen protocol')
    args.output_dir.mkdir(parents=True)
    (args.output_dir / 'chat_template.jinja').write_text(tokenizer.chat_template, encoding='utf-8')
    manifest = dict(status='running', count=0, arm=args.arm, config=config,
        adapter_hashes=config['adapter_hashes'] if args.adapter else {},
        questions_sha256=sha(questions), packages={name: importlib.metadata.version(name)
        for name in ('torch', 'transformers', 'unsloth', 'peft')},
        git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        git_diff_sha256=hashlib.sha256(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=ROOT)).hexdigest(),
        device=torch.cuda.get_device_name(), backend='Unsloth/Transformers', precision='BF16',
        chat_template_sha256=sha(args.output_dir / 'chat_template.jinja'), eos_token_ids=eos)
    save(args.output_dir / 'manifest.json', manifest)
    native, incomplete = 0, []
    with (args.output_dir / 'answers.jsonl').open('x', encoding='utf-8') as output:
        for row, ids in zip(data, encoded):
            x = torch.tensor([ids], device=next(model.parameters()).device)
            started = time.monotonic()
            class Guard(StoppingCriteria):
                reason = None
                def __call__(self, input_ids, scores, **kwargs):
                    count = input_ids.shape[1] - len(ids)
                    if count % 16 == 0 and repeated_tail(input_ids[0, len(ids):].tolist()):
                        self.reason = 'repetition_guard'
                    if time.monotonic() - started > config['wall_time_guard_seconds']:
                        self.reason = self.reason or 'wall_time_guard'
                    return self.reason is not None
            guard = Guard()
            with torch.inference_mode():
                generated = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                    do_sample=False, num_beams=1, repetition_penalty=config['repetition_penalty'],
                    max_new_tokens=config['max_new_tokens'], eos_token_id=eos,
                    pad_token_id=tokenizer.pad_token_id, forced_eos_token_id=None, use_cache=True,
                    stopping_criteria=StoppingCriteriaList([guard]))
            tokens = generated[0, len(ids):].tolist()
            complete = bool(tokens and tokens[-1] in eos)
            native += int(complete)
            if not complete:
                incomplete.append(row['id'])
            result = dict(row, raw_output=tokenizer.decode(tokens, skip_special_tokens=True),
                prompt_token_ids=ids, output_token_ids=tokens, generated_tokens=len(tokens),
                rendered_prompt=tokenizer.apply_chat_template(row['messages'], tokenize=False,
                    add_generation_prompt=True, enable_thinking=False),
                native_eos=complete, hit_max_new_tokens=not complete and not guard.reason,
                finish_reason='native_eos' if complete else guard.reason or 'length_limit',
                latency_seconds=time.monotonic() - started)
            output.write(json.dumps(result, ensure_ascii=False) + '\n')
            output.flush()
            print(args.arm, row['id'], len(tokens), result['finish_reason'], flush=True)
            del generated, x
    manifest.update(status='completed', count=len(data), native_eos_count=native,
                    incomplete_ids=incomplete, answers_sha256=sha(args.output_dir / 'answers.jsonl'))
    save(args.output_dir / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
