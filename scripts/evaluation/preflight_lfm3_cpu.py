"""CPU validation: pinned tokenizer, tiny architecture, reference scorer controls.

Never loads pretrained model weights or treats synthetic controls as model scores.
"""
import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    args = parser.parse_args()
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from score_cetvel_generation import SCORERS
    experiment = args.experiment_dir
    config = json.loads((experiment / 'config-planned.json').read_text())
    repo, revision = config['model']['repo'], config['model']['revision']
    tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision)
    packet = experiment / 'data-local/questions-500.jsonl'
    if hashlib.sha256(packet.read_bytes()).hexdigest() != config['historical_comparison']['questions_sha256']:
        raise ValueError('Packet hash mismatch')
    rows = [json.loads(line) for line in packet.read_text(encoding='utf-8').splitlines()]
    profile = []
    for row in rows:
        rendered = tokenizer.apply_chat_template(row['messages'], tokenize=False,
            add_generation_prompt=True, enable_thinking=False)
        if not rendered.endswith('<think></think>'):
            raise ValueError('Thinking-off native template mismatch')
        tokens = tokenizer(rendered, add_special_tokens=False)['input_ids']
        profile.append(dict(id=row['id'], task=row['task'], tokens=len(tokens)))
    if any(r['tokens'] + 4096 > 8192 for r in profile):
        raise ValueError('Context overflow; never silently drop or truncate rows')
    tiny_config = AutoConfig.from_pretrained(repo, revision=revision, code_revision=revision, trust_remote_code=True)
    for key, value in dict(hidden_size=32, intermediate_size=64, num_hidden_layers=3,
        num_attention_heads=4, num_key_value_heads=2, head_dim=8, vocab_size=128,
        layer_types=['conv', 'sliding_attention', 'full_attention'], pad_token_id=0,
        bos_token_id=1, eos_token_id=2).items():
        setattr(tiny_config, key, value)
    tiny = AutoModelForCausalLM.from_config(tiny_config, code_revision=revision, trust_remote_code=True).eval()
    ids = torch.tensor([[3, 4, 5, 6]])
    with torch.inference_mode():
        logits = tiny(ids).logits
        generated = tiny.generate(ids, max_new_tokens=3, do_sample=False, pad_token_id=0)
    if logits.shape != (1, 4, 128) or not torch.isfinite(logits).all() or generated.shape[1] < 5:
        raise ValueError('Tiny architecture forward/generation failed')
    metrics = {}
    keys = dict(gecturk='exact_match_rate', tquad='exact_match', xquad_tr='exact_match',
        wmt_en_tr='corpus_chrf', mlsum_tr='mean_rougeL')
    # Validate each scorer's real row schema on all 100 rows/task.
    for task, scorer in SCORERS.items():
        original = [r for r in rows if r['task'] == task]
        positive, negative = [], []
        for row in original:
            target = row['target']
            answer = target['answers']['text'][0] if isinstance(target, dict) and target['answers']['text'] else ('' if isinstance(target, dict) else target)
            positive.append(dict(copy.deepcopy(row), raw_output=answer, hit_max_new_tokens=False))
            negative.append(dict(copy.deepcopy(row), raw_output='zzzz_invalid_output_987654321', hit_max_new_tokens=True))
        pos, neg = scorer(positive), scorer(negative)
        key = keys[task]
        if key not in pos:
            raise ValueError(f'Update metric key for {task}: {list(pos)}')
        if pos[key] <= neg[key]:
            raise ValueError(f'Positive control does not beat invalid output: {task}')
        metrics[task] = dict(metric=key, correct_reference=pos[key], invalid_output=neg[key], count=len(original))
    report = dict(status='cpu_checks_passed_not_gpu_validated', model_revision=revision,
        packages={name: importlib.metadata.version(name) for name in ('torch','transformers','tokenizers','huggingface-hub','sacrebleu','rouge-score')},
        chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
        count=len(rows), max_input_tokens=max(r['tokens'] for r in profile),
        mean_input_tokens=statistics.mean(r['tokens'] for r in profile),
        population_std_input_tokens=statistics.pstdev(r['tokens'] for r in profile),
        context_overflows=0, tiny_random_model_forward_and_generation=True,
        scorer_controls=metrics,
        caveats=['Controls are not generated model results', 'Reference overlap is not semantic quality',
            'Legacy SQuAD/ROUGE normalization retained for historical parity; not Turkish linguistic normalization',
            'GPU BF16, cache, memory and throughput still require smoke validation'])
    (experiment / 'cpu-preflight-v01.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
