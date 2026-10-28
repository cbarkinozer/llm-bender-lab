"""Merge the pinned Occam adapter into BF16 base weights; never trains or uploads.

Weights and logs belong outside Git. See OCCAM-GGUF.md for the full pipeline.
"""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

BASE = 'unsloth/Qwen3.5-4B'
BASE_REVISION = '3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'
ADAPTER_REVISION = '1a8a07ff2a29f51a2b6a635a8c219191a7377996'
HASHES = {
    'adapter_model.safetensors': '7ec9b04a5ecac7a031352fb5d0db281ef018c11951a4b4862c418e2b7a002ca1',
    'adapter_config.json': '6f7f0480fdcf1cc32aed14a1c66981c1a454840ece4f05932b0ef338846a4335',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    base, adapter, output = (args.work / name for name in ('base', 'adapter', 'merged'))
    if output.exists():
        raise SystemExit('Merged directory already exists; choose a fresh work directory.')
    for name, expected in HASHES.items():
        if sha(adapter / name) != expected:
            raise SystemExit(f'Adapter hash mismatch: {name}')
    config = json.loads((adapter / 'adapter_config.json').read_text())
    if config['base_model_name_or_path'] != BASE or config['r'] != 16 or config['lora_alpha'] != 16:
        raise SystemExit('Unexpected adapter identity/scaling')

    import torch
    from transformers import Qwen3_5ForConditionalGeneration, AutoTokenizer
    from peft import PeftModel

    torch.set_num_threads(4)
    started = time.monotonic()
    print('Loading pinned BF16 base on CPU for merge.', flush=True)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        base, dtype=torch.bfloat16, device_map='cpu', local_files_only=True,
        trust_remote_code=False, attn_implementation='eager',
    )
    model = PeftModel.from_pretrained(model, adapter, local_files_only=True)
    model.eval()
    adapter_layers = sum(1 for module in model.modules() if hasattr(module, 'lora_A') and len(module.lora_A))
    if not adapter_layers:
        raise SystemExit('No adapter layers loaded')
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True, trust_remote_code=False)
    prompt = tokenizer.apply_chat_template(
        [{'role': 'user', 'content': 'Merhaba.'}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )
    inputs = tokenizer(prompt, return_tensors='pt')
    print(f'Loaded {adapter_layers} LoRA layers; checking pre/post-merge logits.', flush=True)
    with torch.inference_mode():
        before = model(**inputs, use_cache=False, logits_to_keep=1).logits[0, -1].float().clone()
    merged = model.merge_and_unload(safe_merge=True)
    with torch.inference_mode():
        after = merged(**inputs, use_cache=False, logits_to_keep=1).logits[0, -1].float()
    cosine = torch.nn.functional.cosine_similarity(before, after, dim=0).item()
    max_error = (before - after).abs().max().item()
    if not torch.isfinite(after).all() or cosine < 0.99:
        raise SystemExit('Merge logit sanity check failed')
    if any('lora_' in name for name, _ in merged.named_parameters()):
        raise SystemExit('Adapter tensors remain after merge')
    merged.save_pretrained(output, safe_serialization=True, max_shard_size='3GB')
    # Preserve the exact original tokenizer, config, template and generation metadata.
    for path in base.iterdir():
        if path.is_file() and path.suffix in ('.json', '.jinja', '.txt') and path.name not in (
                'config.json', 'model.safetensors.index.json'):
            shutil.copy2(path, output / path.name)
    for name in ('LICENSE',):
        if (base / name).exists():
            shutil.copy2(base / name, output / name)
    manifest = dict(
        base_model=BASE, base_revision=BASE_REVISION,
        adapter_repo='cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora', adapter_revision=ADAPTER_REVISION,
        source_adapter_sha256=HASHES, adapter_layers=adapter_layers, merge_dtype='bfloat16',
        merge_check=dict(prompt='Merhaba.', cosine=cosine, max_logit_abs_error=max_error,
                         top1_before=int(before.argmax()), top1_after=int(after.argmax()),
                         note='One short pre/post-merge logit sanity check, not semantic equivalence evaluation.'),
        elapsed_s=time.monotonic() - started,
        versions={name: importlib.metadata.version(name) for name in ('torch', 'transformers', 'peft', 'safetensors')},
        export_script_sha256=sha(Path(__file__)),
        merged_files_sha256={p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
    )
    (args.work / 'merge-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('adapter_layers', 'merge_check', 'elapsed_s')}), flush=True)


if __name__ == '__main__':
    main()
