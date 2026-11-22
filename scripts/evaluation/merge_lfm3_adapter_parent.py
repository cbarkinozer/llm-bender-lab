"""Merge a LoRA adapter into a local merged parent (for example the Turkish CPT merge) and verify reload parity. GPU pod.

  python merge_lfm3_adapter_parent.py --parent /workspace/lfm3-evalv2/models/cpt --adapter A/adapter --output OUT

Same procedure as the inline merge used for exp-016 arm B (safe_merge, bf16, tokenizer of the pinned base).
Writes <output>/merge-receipt.json. The output directory must not exist.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
TEMPLATE_SHA256 = 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', required=True)
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    assert (args.adapter / 'adapter_model.safetensors').exists(), f'no adapter in {args.adapter}'
    assert not args.output.exists(), 'Output exists; preserve it and choose a new path'
    tok = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest() == TEMPLATE_SHA256, 'Chat template changed'
    model = AutoModelForCausalLM.from_pretrained(args.parent, trust_remote_code=True, dtype=torch.bfloat16).to('cuda')
    model = PeftModel.from_pretrained(model, str(args.adapter)).merge_and_unload(safe_merge=True).eval()
    probe = tok('Merhaba.', return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before = model(**probe, use_cache=False).logits[:, -1].float().cpu()
    args.output.mkdir(parents=True)
    model.save_pretrained(args.output, safe_serialization=True)
    tok.save_pretrained(args.output)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    reloaded = AutoModelForCausalLM.from_pretrained(args.output, trust_remote_code=True, dtype=torch.bfloat16).to('cuda').eval()
    with torch.inference_mode():
        after = reloaded(**probe, use_cache=False).logits[:, -1].float().cpu()
    assert torch.equal(before, after), 'Reload parity failed'
    receipt = dict(parent=args.parent, adapter=str(args.adapter), adapter_sha256=sha256_file(args.adapter / 'adapter_model.safetensors'),
                   reload_exact=True, files={p.name: sha256_file(p) for p in args.output.iterdir() if p.suffix == '.safetensors'})
    (args.output / 'merge-receipt.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    print('MERGED', args.output)


if __name__ == '__main__':
    main()
