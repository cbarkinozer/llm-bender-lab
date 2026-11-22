"""Merge one LoRA adapter into the pinned original LFM3-1.7B (BF16, GPU) and verify reload parity.

The adapter may be a local directory or a Hub repo id (give --adapter-revision for Hub repos).
Writes <output>/merge-receipt.json. The output directory must not exist (nothing is overwritten).
The optional --expected-sha256 compares against a historical merge; a mismatch is recorded, not fatal,
because BF16 merge bytes can change with the torch version.
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
    parser.add_argument('--adapter', required=True)
    parser.add_argument('--adapter-revision')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    adapter = Path(args.adapter)
    if not adapter.exists():
        from huggingface_hub import snapshot_download
        if not args.adapter_revision:
            parser.error('--adapter-revision is required for a Hub adapter')
        adapter = Path(snapshot_download(
            args.adapter, revision=args.adapter_revision,
            allow_patterns=['adapter_model.safetensors', 'adapter_config.json']))
    weights = adapter / 'adapter_model.safetensors'
    assert weights.exists(), f'No adapter_model.safetensors in {adapter}'
    assert not args.output.exists(), 'Output exists; preserve it and choose a new path'

    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'], trust_remote_code=True)
    assert hashlib.sha256(tokenizer.chat_template.encode()).hexdigest() == TEMPLATE_SHA256, 'Chat template changed'
    model = AutoModelForCausalLM.from_pretrained(base['repo'], revision=base['revision'], code_revision=base['revision'],
                                                 dtype=torch.bfloat16, trust_remote_code=True).to('cuda').eval()
    model = PeftModel.from_pretrained(model, str(adapter)).merge_and_unload(safe_merge=True).eval()
    model.config.use_cache = True
    probe = tokenizer('Merhaba.', return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before = model(**probe, use_cache=False).logits[:, -1].cpu()
    args.output.mkdir(parents=True)
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    reloaded = AutoModelForCausalLM.from_pretrained(args.output, dtype=torch.bfloat16, trust_remote_code=True).to('cuda').eval()
    with torch.inference_mode():
        after = reloaded(**probe, use_cache=False).logits[:, -1].cpu()
    assert torch.equal(before, after), 'Merged model changed after save and reload'
    digest = sha256_file(args.output / 'model.safetensors')
    receipt = dict(status='passed', reload_exact=True, weight_sha256=digest, adapter_sha256=sha256_file(weights),
                   adapter=args.adapter, adapter_revision=args.adapter_revision, base=base,
                   expected_sha256=args.expected_sha256,
                   matches_expected=None if not args.expected_sha256 else digest == args.expected_sha256,
                   versions={'torch': torch.__version__, 'peft': __import__('peft').__version__,
                             'transformers': __import__('transformers').__version__})
    (args.output / 'merge-receipt.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('status', 'weight_sha256', 'matches_expected')}), flush=True)


if __name__ == '__main__':
    main()
