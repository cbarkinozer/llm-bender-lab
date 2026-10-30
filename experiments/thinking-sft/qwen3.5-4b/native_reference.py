"""Small native CUDA BF16 reference, before training or full benchmarking."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/workspace/occam2-reference'))
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--adapter',action='store_true')
    p.add_argument('--ids',nargs='+',default=['me-079','me-009','me-090'])
    args=p.parse_args()
    import torch
    from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration,set_seed
    assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    provenance=json.loads((args.root/'download-manifest.json').read_text())
    cases=[json.loads(l) for l in (args.root/'reference-prompts.jsonl').read_text().splitlines()]
    cases=[next(r for r in cases if r['id']==identity) for identity in args.ids]
    args.output.mkdir(parents=True,exist_ok=False)
    settings=dict(do_sample=True,temperature=1.0,top_p=.95,top_k=20,min_p=0.0,
                  repetition_penalty=1.1,max_new_tokens=4096,max_time=600)
    status=dict(complete=False,items=0,error=None,model=provenance['base'],revision=provenance['base_revision'],
        adapter=args.adapter,precision='BF16 original safetensors',backend='Transformers SDPA native generate',
        settings=settings,presence_penalty=0,seed=3407,
        versions={k:importlib.metadata.version(k) for k in ['torch','transformers','peft','accelerate']},
        gpu=torch.cuda.get_device_name(),cuda=torch.version.cuda,
        source_prompts_sha256=sha(args.root/'reference-prompts.jsonl'),script_sha256=sha(Path(__file__)),
        limitation='Three selected development cases, one seed, both thinking modes; no full benchmark or SFT claim.')
    def save():
        (args.output/'manifest.json').write_text(json.dumps(status,indent=2)+'\n')
    save()
    rows=[]
    try:
        tokenizer=AutoTokenizer.from_pretrained(args.root/'base',local_files_only=True,trust_remote_code=False)
        model=Qwen3_5ForConditionalGeneration.from_pretrained(args.root/'base',dtype=torch.bfloat16,
            device_map={'':0},local_files_only=True,trust_remote_code=False,attn_implementation='sdpa')
        if args.adapter:
            from peft import PeftModel
            model=PeftModel.from_pretrained(model,args.root/'adapter',local_files_only=True)
        model.eval()
        status['template_sha256']=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
        eos=[tokenizer.convert_tokens_to_ids(s) for s in ('<|endoftext|>','<|im_end|>')]
        if eos!=[248044,248046]:raise ValueError('Unexpected native EOG token identities')
        status['effective_eos_token_ids']=eos
        status['source_generation_eos']=model.generation_config.eos_token_id
        save()
        for case in cases:
            for thinking in (False,True):
                text=tokenizer.apply_chat_template(case['messages'],tokenize=False,
                    add_generation_prompt=True,enable_thinking=thinking)
                expected=case['rendered_on' if thinking else 'rendered_off']
                if text!=expected:raise ValueError('Native prompt differs from original GGUF input')
                inputs=tokenizer(text,return_tensors='pt',add_special_tokens=False).to('cuda')
                set_seed(3407)
                torch.cuda.synchronize();start=time.monotonic()
                with torch.inference_mode():
                    sequence=model.generate(**inputs,**settings,eos_token_id=eos,
                        pad_token_id=tokenizer.pad_token_id or eos[1],use_cache=True)
                torch.cuda.synchronize();elapsed=time.monotonic()-start
                generated=sequence[0,inputs['input_ids'].shape[-1]:].tolist()
                raw=tokenizer.decode(generated,skip_special_tokens=False)
                reason,answer='',raw
                if thinking:
                    if '</think>' in raw:reason,answer=raw.split('</think>',1)
                    else:reason,answer=raw,''
                for delimiter in ('<|im_end|>','<|endoftext|>'):answer=answer.replace(delimiter,'')
                finish='eos' if generated and generated[-1] in eos else ('length' if len(generated)>=4096 else 'time')
                row=dict(id=case['id'],thinking=thinking,condition='occam1' if args.adapter else 'base',
                    rendered_prompt=text,input_ids=inputs['input_ids'][0].tolist(),raw_completion=raw,
                    output_ids=generated,reasoning=reason.strip(),answer=answer.strip(),
                    finish_reason=finish,generated_tokens=len(generated),elapsed_s=elapsed)
                rows.append(row)
                (args.output/'outputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
                status.update(items=len(rows),outputs_sha256=sha(args.output/'outputs.jsonl'),
                    peak_vram_bytes=torch.cuda.max_memory_allocated())
                save()
                print(json.dumps(dict(id=case['id'],thinking=thinking,finish=finish,tokens=len(generated),
                    seconds=elapsed,answer=answer.strip()),ensure_ascii=False),flush=True)
        status['complete']=len(rows)==len(cases)*2
    except BaseException as error:
        status['error']=type(error).__name__+': '+str(error)
        raise
    finally:save()


if __name__=='__main__':main()
