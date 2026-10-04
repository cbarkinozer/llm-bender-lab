"""CPU-only verify context headroom using the actual pinned tokenizer."""
import argparse
import hashlib
import json
from prepare import HERE, digest, load, save, json_bytes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-files-only', action='store_true')
    args = parser.parse_args()
    from transformers import AutoTokenizer
    config = json.loads((HERE / 'config.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(config['model'], revision=config['revision'],
                                               local_files_only=args.local_files_only)
    rows = load(HERE / 'data-v1/questions-100.jsonl')
    counts = {r['id']: len(tokenizer.apply_chat_template(r['messages'], tokenize=True,
              add_generation_prompt=True, enable_thinking=False, return_dict=False)) for r in rows}
    assert all(n + config['max_new_tokens'] <= config['max_context_tokens'] for n in counts.values())
    result = dict(count=100, maximum_prompt_tokens=max(counts.values()),
                  minimum_prompt_tokens=min(counts.values()), prompt_tokens=counts,
                  questions_sha256=digest(HERE / 'data-v1/questions-100.jsonl'),
                  revision=config['revision'],
                  chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
                  max_context_tokens=config['max_context_tokens'],
                  max_new_tokens=config['max_new_tokens'], input_truncation=False)
    save(HERE / 'data-v1/tokenization-profile.json', json_bytes(result))
    print(json.dumps({key: result[key] for key in ('count', 'maximum_prompt_tokens', 'input_truncation')}))


if __name__ == '__main__':
    main()
