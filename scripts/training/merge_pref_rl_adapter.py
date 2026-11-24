"""Merge a preference-rl LoRA adapter into the pinned original LFM3-1.7B (bf16, CPU) so the evaluation stack can load it as a plain model.

  python merge_pref_rl_adapter.py --adapter DIR --out DIR     (the output directory must not exist)
The merged model is checked against the adapter model on a few trained-style texts (the difference must be far below the adapter's own effect).
"""
import argparse
import json
from pathlib import Path

import pref_rl_common as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--adapter', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    assert not args.out.exists(), 'output exists'
    import torch
    from peft import PeftModel
    tok = C.load_tokenizer()
    model = PeftModel.from_pretrained(C.load_model('cpu', torch.bfloat16), str(args.adapter)).eval()
    msgs = [dict(role='system', content="Use only the documents the user provides to answer their question. Reply in at most two sentences. When the documents do not contain the answer, reply with exactly: I couldn't find the answer in the provided documents."),
            dict(role='user', content='Documents:\n\n[1] Pickup schedule\nChemical waste pickups for room B214 are made on Tuesdays by Laura Petrov (ext. 4423).\n\nQuestion: Who do I contact for the pickup in B214?')]
    texts = [tok.apply_chat_template(msgs + [dict(role='assistant', content=a)], tokenize=False, enable_thinking=False)
             for a in ('Contact Laura Petrov at extension 4423.', "I couldn't find the answer in the provided documents.")]
    ids = [tok(t, add_special_tokens=False, return_tensors='pt').input_ids for t in texts]

    def logps(m):
        with torch.inference_mode():
            return torch.cat([m(input_ids=i, use_cache=False).logits.float().log_softmax(-1).flatten() for i in ids])
    on = logps(model)
    with model.disable_adapter():
        off = logps(model)
    merged = model.merge_and_unload()
    after = logps(merged)
    effect, noise = (on - off).abs().mean().item(), (on - after).abs().mean().item()
    # bf16 rounds the merged weights once; the merge must stay well below what the adapter changes
    assert effect > 0 and noise <= 0.25 * effect, f'merge differs from the adapter model: noise {noise}, adapter effect {effect}'
    diff = dict(noise=noise, effect=effect)
    merged.save_pretrained(str(args.out), safe_serialization=True)
    tok.save_pretrained(str(args.out))
    (args.out / 'merge-receipt.json').write_text(json.dumps(dict(adapter=str(args.adapter), merge_check=diff,
        adapter_files={p.name: C.sha256_file(p) for p in args.adapter.iterdir() if p.is_file()}), indent=1) + '\n')
    print('MERGED', args.out, 'check', diff)


if __name__ == '__main__':
    main()
