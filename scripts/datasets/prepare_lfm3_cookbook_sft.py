"""Prepare cookbook-style prompt/completion data; no training or GPU access.

CPU rendering uses the pinned native Jinja template with generation tracking
tags removed (not output text). GPU preflight must independently verify the
same bytes and actual TRL completion masks with the pinned runtime.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE / 'cookbook-sft-v01'
SOURCE = BASE / 'bilingual-pilot-v01/revisions/v01-corrections-02/train.jsonl'
TOKENIZER = BASE / 'base-sft160-runtime-local/tokenizer'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer
    assert sha(SOURCE) == '17170506a2510bf938cf196dc08f79729334e267fd1b6b8a718e56b82f499db6'
    text = (TOKENIZER / 'chat_template.jinja').read_text(encoding='utf-8')
    assert hashlib.sha256(text.encode()).hexdigest() == 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(text.replace('{%- generation -%}', '').replace('{%- endgeneration -%}', ''))
    tok = Tokenizer.from_file(str(TOKENIZER / 'tokenizer.json'))

    def render(messages, thinking, generation=False):
        return template.render(messages=messages, bos_token='<|startoftext|>',
                               enable_thinking=thinking, add_generation_prompt=generation)

    rows = [json.loads(line) for line in SOURCE.read_text(encoding='utf-8').splitlines()]
    prepared, audits = [], []
    for row in rows:
        messages = [dict(m) for m in row['messages']]
        reasoning = row['worked_solution']
        if reasoning:
            messages[-1]['thinking'] = reasoning
        else:
            assert not any(messages[-1].get(k) for k in ['thinking', 'reasoning', 'reasoning_content'])
        thinking = bool(reasoning)
        prompt = render(messages[:-1], thinking, True)
        full = render(messages, thinking)
        assert full.startswith(prompt), row['id']
        pids = tok.encode(prompt, add_special_tokens=False).ids
        ids = tok.encode(full, add_special_tokens=False).ids
        assert ids[:len(pids)] == pids and len(ids) <= 4096
        target = full[len(prompt):]
        assert target.endswith('<|im_end|>\n') and tok.token_to_id('<|im_end|>') in ids[len(pids):]
        if not reasoning:
            assert target == messages[-1]['content'] + '<|im_end|>\n'
            assert '<think>' not in target and '</think>' not in target
        else:
            assert target == reasoning + '</think>' + messages[-1]['content'] + '<|im_end|>\n'
        old_prefix = render(messages[:-1], True) + '<|im_start|>assistant\n'
        old_ids = tok.encode(old_prefix, add_special_tokens=False).ids
        assert ids[:len(old_ids)] == old_ids
        prepared.append({'prompt': messages[:-1], 'completion': [messages[-1]],
                         'chat_template_kwargs': {'enable_thinking': thinking}})
        audits.append({'id': row['id'], 'reasoning': thinking, 'length': len(ids),
                       'old_supervised_tokens': len(ids)-len(old_ids),
                       'new_supervised_tokens': len(ids)-len(pids),
                       'prompt_suffix': prompt[-60:], 'decoded_target': target})
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / 'train.jsonl'
    dest.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in prepared), encoding='utf-8')
    dump(OUT / 'audit.json', {'status': 'cpu-render-passed-gpu-trl-mask-check-pending',
         'source_sha256': sha(SOURCE), 'train_sha256': sha(dest), 'rows': len(rows),
         'reasoning_rows': sum(a['reasoning'] for a in audits),
         'old_supervised_tokens': sum(a['old_supervised_tokens'] for a in audits),
         'new_supervised_tokens': sum(a['new_supervised_tokens'] for a in audits),
         'max_length': max(a['length'] for a in audits),
         'reasoning_and_answer_text_unchanged': True, 'examples': audits})
    original = json.loads((BASE / 'exp-012-base-bilingual/config.yaml').read_text(encoding='utf-8'))
    common = {'model': original['model'], 'dataset_file': str(dest.relative_to(ROOT)).replace('\\', '/'),
              'dataset_sha256': sha(dest), 'seed': 3407, 'completion_only_loss': True,
              'assistant_only_loss': False, 'packing': False, 'max_length': 4096,
              'bf16': True, 'fp16': False, 'lr_scheduler_type': 'cosine',
              'target_modules': original['training']['target_modules'],
              'inference': 'Reuse frozen stage-diagnostic settings for matched comparisons; score modes separately.',
              'status': 'prepared-not-trained-gpu-preflight-pending'}
    configs = [
        ('exp-014-completion-mask', {'r': 32, 'lora_alpha': 64, 'lora_dropout': 0.0,
          'learning_rate': 1e-4, 'per_device_train_batch_size': 2, 'gradient_accumulation_steps': 4,
          'max_steps': 69, 'warmup_steps': 6, 'data_order': 'exp-012 order_b first 552 rows; sequential sampler required',
          'hypothesis': 'Change only prompt/completion loss boundary against exp-012 checkpoint69; retain original row order and scheduler horizon of 113 steps. Do not set scheduler horizon to 69.'}),
        ('exp-015-cookbook-recipe', {'r': 16, 'lora_alpha': 32, 'lora_dropout': 0.05,
          'learning_rate': 2e-4, 'per_device_train_batch_size': 4, 'gradient_accumulation_steps': 4,
          'num_train_epochs': 1, 'warmup_steps': 0.05, 'expected_steps_single_gpu': 40,
          'hypothesis': 'Combined official cookbook recipe on existing data; not a single-hyperparameter causal ablation.'})]
    for name, settings in configs:
        dump(BASE / name / 'config.json', dict(common, **settings))
    print(json.dumps({'rows': len(rows), 'reasoning_rows': sum(a['reasoning'] for a in audits),
                      'old_tokens': sum(a['old_supervised_tokens'] for a in audits),
                      'new_tokens': sum(a['new_supervised_tokens'] for a in audits),
                      'max_length': max(a['length'] for a in audits)}))


if __name__ == '__main__':
    main()
