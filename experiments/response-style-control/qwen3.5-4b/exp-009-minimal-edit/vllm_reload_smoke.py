"""Fast-engine generation check for merged smoke adapter, never used as benchmark."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError('Refusing overwrite')
    from vllm import LLM, SamplingParams
    llm=LLM(model=args.model,dtype='bfloat16',max_model_len=4096,gpu_memory_utilization=.85,
        max_num_seqs=1,enforce_eager=True,enable_prefix_caching=False,
        limit_mm_per_prompt={'image':0,'video':0},generation_config='vllm',seed=3407)
    tokenizer=llm.get_tokenizer()
    end=tokenizer.convert_tokens_to_ids('<|im_end|>')
    messages=[{'role':'user','content':'Yalnızca şu sözcüğü yaz: tamam'}]
    prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    output=llm.generate([prompt],SamplingParams(temperature=0,max_tokens=1024,repetition_penalty=1.05,stop_token_ids=[end]))[0].outputs[0]
    natural=output.finish_reason=='stop' and (output.stop_reason==end or (output.token_ids and output.token_ids[-1]==end))
    report=dict(status='passed' if natural and output.text.strip() else 'failed',finish_reason=output.finish_reason,
        stop_reason=output.stop_reason,native_stop=natural,text=output.text,token_ids=list(output.token_ids),backend='vllm',scope='reload smoke only, not benchmark')
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if report['status']!='passed':
        raise RuntimeError('Reload smoke did not stop naturally')
    print(json.dumps({k:v for k,v in report.items() if k!='token_ids'},ensure_ascii=False))

if __name__=='__main__':
    main()
