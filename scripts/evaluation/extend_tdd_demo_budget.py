"""Freeze larger inference allowance from measured prompts; training stays identical."""
import argparse
import math
from pathlib import Path
import shutil
from active_tdd_data import EXP,read_json,rows
from prepare_tdd_demo import digest,save


def main(tokenizer_path):
    from transformers import AutoTokenizer
    src=EXP/'demo-preflight-v02';out=EXP/'demo-preflight-v03'
    if out.exists():raise ValueError('Preserve existing budget revision')
    pin=read_json(EXP/'native-label-audit-v01/tokenizer-pin-verification.json')
    for entry in pin['files']:
        if digest(Path(tokenizer_path)/entry['file'])!=entry['local_sha256']:raise ValueError('Tokenizer differs from pinned audit')
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True,trust_remote_code=False)
    sizes=[]
    for row in rows(src/'development-requests.jsonl'):
        prompt=tokenizer.apply_chat_template(row['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=True)
        sizes.append(dict(record_id=row['record_id'],prompt_tokens=len(tokenizer.encode(prompt,add_special_tokens=False))))
    output_tokens=8192;largest=max(r['prompt_tokens'] for r in sizes)
    context=math.ceil((largest+output_tokens)/1024)*1024
    out.mkdir()
    for name in ('train-encoded.jsonl','development-encoded.jsonl','development-requests.jsonl','development-targets.jsonl',
                 'executor-reference-controls.jsonl','baseline-review-template.json'):
        shutil.copyfile(src/name,out/name)
    recipe=read_json(src/'recipe.json');recipe['inference'].update(max_tokens=output_tokens,max_model_len=context)
    recipe['evaluation']['budget_rationale']=f'Study launchers use8192 output/16384 total context. Current development prompts require at most{largest} tokens; use{output_tokens} shared output and{context} total context. Training3072 unchanged. This is a ceiling, not forced generation length.'
    save(out/'recipe.json',recipe)
    save(out/'prompt-budget.json',dict(prompts=sizes,max_prompt_tokens=largest,max_new_tokens=output_tokens,
         minimum_total_context=largest+output_tokens,rounded_total_context=context,rounding_multiple=1024,
         scope='Current nine development requests only; runtime independently checks each prompt. Holdout unmeasured/unopened.'))
    manifest=read_json(src/'manifest.json');manifest['status']='local budget preparation verified; GPU/Docker gates pending'
    manifest['supersedes']='demo-preflight-v02 generation budget only; training data and labels unchanged'
    manifest['files']={p.name:digest(p) for p in out.iterdir()};save(out/'manifest.json',manifest)
    print('Output budget:',output_tokens,'max prompt:',largest,'total context:',context)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tokenizer',required=True);main(p.parse_args().tokenizer)
