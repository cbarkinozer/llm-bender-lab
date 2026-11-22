"""SFT core v01: write oracle samples for the code rows (the MBPP reference solution as the answer) so the verifier can
prove that every code checker accepts its own reference. Run on the pod; the verifier executes the code.

  python oracle_lfm3_sft_core_code.py --core prompts-en.jsonl --output oracle-code-samples.jsonl
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(s) for s in args.core.read_text(encoding='utf-8').split('\n') if s.strip()]
    with args.output.open('w', encoding='utf-8') as out:
        for row in rows:
            if row['category'] != 'code':
                continue
            raw = f'```python\n{row["reference"]["code"]}\n```<|im_end|>'
            if row['thinking']:
                raw = '<think>reference</think>' + raw
            out.write(json.dumps(dict(id=f'{row["id"]}-en', thinking=row['thinking'],
                                      samples=[dict(raw_output=raw, tokens=1, finish_reason='eos')])) + '\n')
    print('wrote', args.output)


if __name__ == '__main__':
    main()
