"""exp-006: turn pairs.jsonl from tr_dpo6_pairs.py into the pairs format of scripts/training/run_tr_dpo_train.py.

The sampler asked the parent with a plain user turn and thinking off, so the trainer rows do the same. The lane is the failure type of the
rejected answer, which gives per-type DPO metrics before and after training. The SFT control uses the same file with --dpo-weight 0.
  python scripts/datasets/tr_dpo6_to_trainer.py --pairs pairs.jsonl --out trainer-pairs.jsonl
"""
import argparse
import hashlib
import json
from pathlib import Path


def convert(rows):
    out = []
    for r in rows:
        assert r['chosen'].strip() and r['rejected'].strip() and r['chosen'] != r['rejected'], r['pair_id']
        out.append(dict(id=r['pair_id'], prompt=[dict(role='user', content=r['prompt'])], chosen=[dict(role='assistant', content=r['chosen'])],
                        rejected=[dict(role='assistant', content=r['rejected'])], chat_template_kwargs=dict(enable_thinking=False), lane=r['type']))
    ids = [x['id'] for x in out]
    assert len(ids) == len(set(ids)), 'duplicate pair ids'
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    rows = [json.loads(line) for line in args.pairs.read_text(encoding='utf-8').splitlines() if line.strip()]
    out = convert(rows)
    args.out.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in out), encoding='utf-8', newline='\n')
    print(json.dumps(dict(pairs=len(out), out=str(args.out), sha256=hashlib.sha256(args.out.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
