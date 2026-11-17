"""Materialize a saved epoch3/5 LoRA against the pinned untouched base for vLLM."""
import argparse
from pathlib import Path
import time
from run_lfm3_base_sft160 import BASE, RUNTIME, dump, sha, environment


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--experiment',required=True)
    p.add_argument('--step',type=int,choices=[60,100],required=True)
    a=p.parse_args();environment()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM,AutoTokenizer
    source=BASE/a.experiment/'results-local/sft'/f'checkpoint-{a.step}'
    destination=BASE/a.experiment/'results-local'/f'merged-step{a.step}'
    assert all((source/n).exists() for n in ['adapter_model.safetensors','optimizer.pt','scheduler.pt','trainer_state.json','rng_state.pth'])
    assert not destination.exists(),'Refusing to overwrite existing inference export'
    tokenizer=AutoTokenizer.from_pretrained(RUNTIME/'tokenizer',trust_remote_code=True)
    model=AutoModelForCausalLM.from_pretrained(RUNTIME/'init-model',trust_remote_code=True,dtype=torch.bfloat16).to('cuda')
    model=PeftModel.from_pretrained(model,source).eval()
    probe=tokenizer('Merhaba.',return_tensors='pt').to('cuda')
    with torch.inference_mode():before=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    model=model.merge_and_unload(safe_merge=True).eval();model.config.use_cache=True
    with torch.inference_mode():merged=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    model.save_pretrained(destination,safe_serialization=True);tokenizer.save_pretrained(destination)
    del model
    import gc
    gc.collect();torch.cuda.empty_cache()
    model=AutoModelForCausalLM.from_pretrained(destination,trust_remote_code=True,dtype=torch.bfloat16).to('cuda').eval()
    with torch.inference_mode():after=model(**probe,use_cache=False).logits[:,-1].float().cpu()
    assert torch.equal(merged,after),'Merged save/reload parity failed'
    dump(destination/'merge-receipt.json',dict(status='passed',step=a.step,source_adapter_sha256=sha(source/'adapter_model.safetensors'),
        initialization_sha256=sha(RUNTIME/'init-model.json'),reload_exact=True,max_abs_merge_difference=float((before-merged).abs().max()),
        files={f.name:sha(f) for f in destination.iterdir() if f.is_file()}))


if __name__=='__main__':main()
