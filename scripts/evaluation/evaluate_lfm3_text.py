"""Raw-text token-weighted NLL; disjoint windows, no chat wrapper or padding.

Each token after the first in each document is scored exactly once. Each window
keeps one preceding token; context resets are explicit and fixed across arms.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--adapter', type=Path)
    args = parser.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    cfg = json.loads((args.experiment_dir / 'config-planned.json').read_text())['model']
    tokenizer = AutoTokenizer.from_pretrained(cfg['repo'], revision=cfg['revision'])
    model = AutoModelForCausalLM.from_pretrained(cfg['repo'], revision=cfg['revision'],
        code_revision=cfg['revision'], trust_remote_code=True, dtype=torch.bfloat16).to('cuda').eval()
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(args.adapter)).eval()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    results = {}
    data_manifest = json.loads((args.experiment_dir / 'cpt-data-manifest-v02.json').read_text())
    for name in ('wiki_eval', 'web_eval'):
        file = args.experiment_dir / 'data-local/cpt-v02' / (name + '.jsonl')
        if hashlib.sha256(file.read_bytes()).hexdigest() != data_manifest['splits'][name]['sha256']:
            raise ValueError('Evaluation text checksum mismatch')
        rows = [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()]
        documents = []
        for row in rows:
            ids = tokenizer(row['text'], add_special_tokens=False)['input_ids']
            total_loss, total_tokens = 0., 0
            for start in range(1, len(ids), 2047):
                window = ids[start-1:start+2047]
                inputs = torch.tensor([window], device='cuda')
                labels = inputs.clone()
                labels[:, 0] = -100
                with torch.inference_mode():
                    loss = model(input_ids=inputs, labels=labels, use_cache=False).loss
                count = len(window)-1
                total_loss += loss.item()*count
                total_tokens += count
            documents.append(dict(id=row['id'], nll_sum=total_loss, scored_tokens=total_tokens))
        count = sum(d['scored_tokens'] for d in documents)
        nll = sum(d['nll_sum'] for d in documents)/count
        results[name] = dict(nll=nll, perplexity=math.exp(nll), scored_tokens=count,
            source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(), documents=documents)
        (args.output_dir / 'text-scores.json').write_text(json.dumps(dict(model=cfg,
            adapter=str(args.adapter) if args.adapter else None, context=2048,
            policy='raw text; no BOS/EOS; first token/document not scored; 2047 new targets/window',
            results=results), indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
