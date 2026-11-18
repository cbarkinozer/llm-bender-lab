"""Materialize one frozen bilingual-pilot checkpoint; require exact reload parity."""
import argparse
import gc
import time

from run_lfm3_bilingual_gpu import BASE,RUN,load,environment,dump,read,sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',required=True)
    parser.add_argument('--step',required=True,type=int)
    args=parser.parse_args();environment()
    cfg,_,_=load(args.experiment)
    assert args.step in cfg['training']['save_steps']
    source=BASE/args.experiment/'results-local/sft'/f'checkpoint-{args.step}'
    dest=BASE/args.experiment/'results-local'/f'merged-step{args.step}'
    if (dest/'merge-receipt.json').exists():
        receipt=read(dest/'merge-receipt.json')
        assert receipt['source_adapter_sha256']==sha(source/'adapter_model.safetensors')
        assert all(sha(dest/p)==h for p,h in receipt['files'].items())
        return
    assert not dest.exists(),'Incomplete merge; preserve and inspect'
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    tokenizer=AutoTokenizer.from_pretrained(RUN/'native'/args.experiment/'tokenizer',trust_remote_code=True)
    model=AutoModelForCausalLM.from_pretrained(RUN/'parent-prepare/cpt-merged',dtype=torch.bfloat16,trust_remote_code=True).to('cuda')
    model=PeftModel.from_pretrained(model,source).eval()
    probe=tokenizer('Merhaba.',return_tensors='pt').to('cuda')
    with torch.inference_mode():before=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    model=model.merge_and_unload(safe_merge=True).eval();model.config.use_cache=True
    with torch.inference_mode():merged=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    assert torch.isfinite(merged).all()
    model.save_pretrained(dest,safe_serialization=True);tokenizer.save_pretrained(dest)
    del model;gc.collect();torch.cuda.empty_cache()
    model=AutoModelForCausalLM.from_pretrained(dest,dtype=torch.bfloat16,trust_remote_code=True).to('cuda').eval()
    with torch.inference_mode():after=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    assert torch.equal(merged,after)
    dump(dest/'merge-receipt.json',dict(status='passed',step=args.step,reload_exact=True,
        source_adapter_sha256=sha(source/'adapter_model.safetensors'),parent_merge_sha256=sha(RUN/'parent-prepare/cpt-merge.json'),
        max_abs_merge_difference=float((before-merged).abs().max()),
        files={p.name:sha(p) for p in dest.iterdir() if p.is_file()}))


if __name__=='__main__':main()
