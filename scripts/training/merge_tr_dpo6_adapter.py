"""Merge an exp-006 LoRA adapter into its parent (exp-021) as a 16-bit model for the evaluation stack.

  python merge_tr_dpo6_adapter.py --parent DIR --adapter DIR --out DIR [--expect-sha256 HEX]
Same operation as the trainer's own merge (merge_and_unload on the bf16 parent); the output sha256 is compared with the one the trainer recorded.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--adapter', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--expect-sha256', default=None)
    args = ap.parse_args()
    assert not args.out.exists(), 'output exists'
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(args.parent), trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(str(args.parent), trust_remote_code=True, dtype=torch.bfloat16)
    merged = PeftModel.from_pretrained(model, str(args.adapter)).merge_and_unload()
    merged.save_pretrained(str(args.out), safe_serialization=True)
    tok.save_pretrained(str(args.out))
    got = sha(args.out / 'model.safetensors')
    receipt = dict(parent=str(args.parent), adapter=str(args.adapter), adapter_sha256=sha(args.adapter / 'adapter_model.safetensors'),
                   merged_sha256=got, expected_sha256=args.expect_sha256, matches_trainer=(got == args.expect_sha256) if args.expect_sha256 else None)
    (args.out / 'merge-receipt.json').write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
