"""Strict total sentence likelihood preference on the cleaned frozen subset."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--adapter', type=Path)
    args = parser.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    cfg = json.loads((args.experiment_dir/'config-planned.json').read_text())['model']
    packet = args.experiment_dir/'data-local/turblimp-1600.jsonl'
    receipt = json.loads((args.experiment_dir/'turblimp-manifest-v01.json').read_text())
    if hashlib.sha256(packet.read_bytes()).hexdigest() != receipt['sha256']:
        raise ValueError('TurBLiMP packet checksum mismatch')
    tokenizer = AutoTokenizer.from_pretrained(cfg['repo'],revision=cfg['revision'])
    model = AutoModelForCausalLM.from_pretrained(cfg['repo'],revision=cfg['revision'],code_revision=cfg['revision'],
        trust_remote_code=True,dtype=torch.bfloat16).to('cuda').eval()
    if args.adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,str(args.adapter)).eval()
    def logprob(text):
        ids=tokenizer(text,add_special_tokens=False)['input_ids']
        # Shared BOS permits scoring the first sentence token too.
        inputs=torch.tensor([[tokenizer.bos_token_id]+ids],device='cuda')
        with torch.inference_mode():
            logits=model(inputs,use_cache=False).logits[0,:-1].float()
            values=logits.log_softmax(-1).gather(-1,inputs[0,1:,None]).squeeze(-1)
        return values.sum().item()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    groups=defaultdict(list)
    with (args.output_dir/'pairs.jsonl').open('w',encoding='utf-8') as stream:
        for line in packet.read_text(encoding='utf-8').splitlines():
            row=json.loads(line)
            good,bad=logprob(row['sentence_good']),logprob(row['sentence_bad'])
            result=dict(id=row['id'],phenomenon=row['linguistic_phenomenon'],good_logprob=good,bad_logprob=bad,
                win=good>bad,tie=good==bad)
            groups[result['phenomenon']].append(result)
            stream.write(json.dumps(result)+'\n'); stream.flush()
    metrics={k:dict(count=len(v),accuracy=sum(r['win'] for r in v)/len(v),ties=sum(r['tie'] for r in v)) for k,v in groups.items()}
    report=dict(model=cfg,adapter=str(args.adapter) if args.adapter else None,packet_sha256=receipt['sha256'],
        policy='BOS + raw sentence, no EOS, summed log probabilities; ties are not wins',per_phenomenon=metrics,
        macro_accuracy=sum(v['accuracy'] for v in metrics.values())/len(metrics),official_full_benchmark=False)
    (args.output_dir/'scores.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
