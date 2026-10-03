"""Small raw mode/retained-training-fit probes, never the primary evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
REV='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--adapter',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output_dir.exists()
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, set_seed
    set_seed(3407)
    model,_=FastLanguageModel.from_pretrained(model_name='unsloth/Qwen3.5-4B',revision=REV,
        max_seq_length=32768,load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    if args.adapter:
        model=PeftModel.from_pretrained(model,str(args.adapter),is_trainable=False)
    FastLanguageModel.for_inference(model)
    model.eval()
    tok=AutoTokenizer.from_pretrained('unsloth/Qwen3.5-4B',revision=REV)
    import sys
    sys.path.insert(0,str(HERE.parent/'exp-009-minimal-edit'))
    from evaluate_adapter import repeated_tail
    raw=HERE.parent/'exp-009-minimal-edit/reviewed-v2'
    validation=[json.loads(s) for s in (raw/'validation-reviewed.jsonl').read_text(encoding='utf-8').splitlines()]
    train=[json.loads(s) for s in (raw/'train-reviewed.jsonl').read_text(encoding='utf-8').splitlines()]
    # Exact selected IDs fixed in source before these supporting outputs are seen.
    cases=[(r,thinking,'mode-preservation') for r in validation if r['id'] in ('me-070','me-079') for thinking in (False,True)]
    if args.adapter:
        cases.extend((r,False,'retained-training-fit') for r in train if r['id'] in ('me-041','me-051'))
        assert len(cases)==6
    args.output_dir.mkdir(parents=True)
    eos=model.generation_config.eos_token_id
    eos=[eos] if isinstance(eos,int) else eos
    with (args.output_dir/'raw-probes.jsonl').open('x',encoding='utf-8') as file:
        for row,thinking,purpose in cases:
            ids=tok.apply_chat_template(row['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=thinking)
            start=time.monotonic()
            class Guard(StoppingCriteria):
                reason=None
                def __call__(self,input_ids,scores,**kwargs):
                    if (input_ids.shape[1]-len(ids))%16==0 and repeated_tail(input_ids[0,len(ids):].tolist()):
                        self.reason='repetition_guard'
                    if time.monotonic()-start>180:
                        self.reason='wall_time_guard'
                    return self.reason is not None
            guard=Guard()
            x=torch.tensor([ids],device=next(model.parameters()).device)
            with torch.inference_mode():
                y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,num_beams=1,
                    repetition_penalty=1.05,max_new_tokens=4096,eos_token_id=eos,pad_token_id=tok.pad_token_id,
                    forced_eos_token_id=None,use_cache=True,stopping_criteria=StoppingCriteriaList([guard]))
            output=y[0,len(ids):].tolist()
            text=tok.decode(output,skip_special_tokens=False)
            if thinking:
                marker=tok.encode('</think>',add_special_tokens=False)
                positions=[i for i in range(len(output)-len(marker)+1) if output[i:i+len(marker)]==marker]
                boundary=positions[0]+len(marker) if positions else None
                final=tok.decode(output[boundary:],skip_special_tokens=True).strip() if boundary is not None else ''
                reasoning_tokens=boundary if boundary is not None else len(output)
            else:
                boundary=0
                final=tok.decode(output,skip_special_tokens=True).strip()
                reasoning_tokens=0
            native=bool(output and output[-1] in eos)
            item=dict(id=row['id'],purpose=purpose,split=row['split'],thinking=thinking,messages=row['messages'],
                rendered_prompt=tok.decode(ids,skip_special_tokens=False),prompt_token_ids=ids,output_token_ids=output,
                raw_output=text,final_answer=final,desired_answer=row['desired_answer'],final_answer_emitted=bool(final),
                reasoning_tokens=reasoning_tokens,final_tokens=len(output)-reasoning_tokens,native_eos=native,
                finish_reason='native_eos' if native else guard.reason or 'length_limit',output_tokens=len(output),seconds=time.monotonic()-start)
            file.write(json.dumps(item,ensure_ascii=False)+'\n');file.flush()
            print(row['id'],purpose,thinking,len(output),item['finish_reason'],flush=True)
    manifest=dict(status='completed',count=len(cases),model_revision=REV,adapter=str(args.adapter) if args.adapter else None,
        seed=3407,backend='Unsloth/Transformers',max_new_tokens=4096,repetition_penalty=1.05,
        caveat='Supporting diagnostic only. Mode probes use two reused development items; training fit is not generalization.',
        files={'raw-probes.jsonl':hashlib.sha256((args.output_dir/'raw-probes.jsonl').read_bytes()).hexdigest()})
    (args.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':
    main()
