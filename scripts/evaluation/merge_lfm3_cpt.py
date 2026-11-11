"""Save a deployable BF16 merged model; preserve adapter and merge diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--experiment-dir',type=Path,required=True)
    p.add_argument('--training-dir',type=Path,required=True)
    a=p.parse_args()
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    cfg=json.loads((a.experiment_dir/'config-planned.json').read_text())['model']
    tokenizer=AutoTokenizer.from_pretrained(cfg['repo'],revision=cfg['revision'])
    model=AutoModelForCausalLM.from_pretrained(cfg['repo'],revision=cfg['revision'],
        code_revision=cfg['revision'],trust_remote_code=True,dtype=torch.bfloat16).to('cuda')
    model=PeftModel.from_pretrained(model,str(a.training_dir/'adapter')).eval()
    ids=tokenizer('Bu, model kaydetme ve yeniden yükleme kontrolüdür.',return_tensors='pt').to('cuda')
    with torch.inference_mode():
        before=model(**ids,use_cache=False).logits[:,-1,:].float().cpu()
    model=model.merge_and_unload(safe_merge=True).eval()
    with torch.inference_mode():
        after=model(**ids,use_cache=False).logits[:,-1,:].float().cpu()
    assert torch.isfinite(after).all()
    difference=(before-after).abs()
    output=a.training_dir/'merged-model'
    output.mkdir(exist_ok=False)
    model.save_pretrained(output,safe_serialization=True)
    tokenizer.save_pretrained(output)
    report=dict(status='merged',precision='bfloat16',note='BF16 merge changes rounding; likelihood uses unmerged adapter before/after.',
        probe='Synthetic save/reload engineering check, not benchmark selection',
        max_abs_logit_difference=float(difference.max()),mean_abs_logit_difference=float(difference.mean()),
        top1_agrees=int(before.argmax())==int(after.argmax()),
        files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in output.iterdir() if f.is_file()})
    (a.training_dir/'merge-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)


if __name__=='__main__':
    main()
