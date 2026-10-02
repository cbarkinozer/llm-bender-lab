"""CPU-only pinned-tokenizer preflight; no weights, inference or training."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from export_completed_reviews import normalized

HERE = Path(__file__).resolve().parent
MODEL = 'unsloth/Qwen3.5-4B'
REVISION = '3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def encode_final(tokenizer, row):
    context = row['messages']
    full = context + [{'role':'assistant', 'content':row['desired_answer']}]
    prefix = tokenizer.apply_chat_template(context, tokenize=True, add_generation_prompt=True, enable_thinking=False)
    ids = tokenizer.apply_chat_template(full, tokenize=True, add_generation_prompt=False, enable_thinking=False)
    if ids[:len(prefix)] != prefix:
        raise ValueError('Template prefix mismatch: '+row['id'])
    end_id = tokenizer.convert_tokens_to_ids('<|im_end|>')
    ends = [i for i in range(len(prefix), len(ids)) if ids[i] == end_id]
    if len(ends) != 1:
        raise ValueError('Expected one final end-of-turn: '+row['id'])
    end = ends[0]+1
    labels = [-100]*len(prefix)+ids[len(prefix):end]+[-100]*(len(ids)-end)
    assert all(x == -100 for x in labels[:len(prefix)])
    assert labels[end-1] == end_id
    assert any(x != -100 for x in labels)
    target_text = tokenizer.decode(ids[len(prefix):end-1], skip_special_tokens=False)
    # Native Qwen template trims outer whitespace; keep reviewed raw target intact.
    if target_text != row['desired_answer'].strip():
        raise ValueError('Target roundtrip differs: '+row['id'])
    return dict(input_ids=ids, labels=labels, attention_mask=[1]*len(ids)), len(prefix), end-len(prefix)

def stats(values):
    values=sorted(values)
    return {'min':min(values), 'median':values[round((len(values)-1)*.5)],
            'p90':values[round((len(values)-1)*.9)], 'p95':values[round((len(values)-1)*.95)],
            'p99':values[round((len(values)-1)*.99)], 'max':max(values), 'total':sum(values)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('Refusing to overwrite preflight')
    parent=HERE/'reviewed-v2'
    manifest=json.loads((parent/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='qa-corrections-applied'
    for name, expected in manifest['files'].items():
        assert sha(parent/name)==expected, name
    rows=[]
    for split, count in [('train',80),('validation',20)]:
        subset=[json.loads(s) for s in (parent/f'{split}-reviewed.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(subset)==count and all(r['split']==split for r in subset)
        rows.extend(subset)
    assert len({r['id'] for r in rows})==100
    train=[r for r in rows if r['split']=='train']
    val=[r for r in rows if r['split']=='validation']
    flags=[]
    for a in train:
        for b in val:
            assert a['scenario_group_id'] != b['scenario_group_id']
            assert (a['source_path'],a['source_id']) != (b['source_path'],b['source_id'])
            for ma in a['messages']:
                for mb in b['messages']:
                    ta,tb=normalized(ma['content']),normalized(mb['content'])
                    assert ta != tb, (a['id'], b['id'])
                    # Same content stripping as original audit (remove task scaffolding).
                    from build_selection import content_only
                    score=SequenceMatcher(None,content_only(ta),content_only(tb),autojunk=False).ratio()
                    if score>=.60:
                        flags.append({'train':a['id'],'validation':b['id'],'score':score})
    audit=json.loads((HERE/'data/audit-report.json').read_text(encoding='utf-8'))
    benchmarks=[]
    for path, info in audit['benchmark_inputs'].items():
        file=HERE.parent/path
        assert sha(file)==info['sha256_bytes']
        with file.open(encoding='utf-8-sig',newline='') as f:
            benchmarks.extend((path,r['id'],r['prompt_tr']) for r in csv.DictReader(f) if r.get('prompt_tr'))
    benchmark_flags=[]
    for row in rows:
        for m in row['messages']:
            for path, bid, text in benchmarks:
                score=SequenceMatcher(None,normalized(m['content']),normalized(text),autojunk=False).ratio()
                if score>=.78:
                    benchmark_flags.append({'id':row['id'],'benchmark':path,'benchmark_id':bid,'score':score})
    assert not flags, flags
    assert not benchmark_flags, benchmark_flags
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    prepared=[]
    for row in rows:
        assert row['desired_answer'].strip() and '\ufffd' not in row['desired_answer']
        assert '**' not in row['desired_answer'] and not re.search(r'^\s*#{1,6}\s',row['desired_answer'],re.M)
        item, prompt_count, target_count=encode_final(tokenizer,row)
        prepared.append(dict(id=row['id'],split=row['split'],category=row['category'],
                             prompt_tokens=prompt_count,target_tokens=target_count,**item))
    maximum=max(len(r['input_ids']) for r in prepared)
    max_length=next(n for n in [512,1024,2048,4096,8192] if n>=maximum)
    args.output_dir.mkdir(parents=True)
    def save(name,value):
        (args.output_dir/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for split in ('train','validation'):
        subset=[r for r in prepared if r['split']==split]
        (args.output_dir/f'{split}-tokenized.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in subset),encoding='utf-8',newline='\n')
    samples=[]
    for id_ in ['me-001','me-042','me-053','me-054','me-059','me-088']:
        item=next(r for r in prepared if r['id']==id_)
        samples.append(dict(id=id_,split=item['split'],input_ids=item['input_ids'],labels=item['labels'],
            full_text=tokenizer.decode(item['input_ids'],skip_special_tokens=False),
            supervised_text=tokenizer.decode([x for x in item['labels'] if x!=-100],skip_special_tokens=False)))
    save('mask-inspection.json',samples)
    save('tokenizer-template.json',dict(model=MODEL,revision=REVISION,chat_template=tokenizer.chat_template,
        template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),special_tokens_map=tokenizer.special_tokens_map))
    report=dict(status='local-preflight-passed',rows=100,splits={'train':80,'validation':20},
        split_stats={s:{'sequence':stats([len(r['input_ids']) for r in prepared if r['split']==s]),
            'target':stats([r['target_tokens'] for r in prepared if r['split']==s])} for s in ('train','validation')},
        max_seq_length=max_length,truncated_rows=0,zero_target_rows=0,all_context_tokens_masked=True,
        native_final_end_of_turn_supervised=True,cross_split_near_flags=flags,benchmark_rows_checked=len(benchmarks),
        benchmark_flags=benchmark_flags,packing=False,
        source_hashes={f'{s}-reviewed.jsonl':sha(parent/f'{s}-reviewed.jsonl') for s in ('train','validation')},
        limitation='Zero detected overlap, not proof of semantic independence. Tokenizer-only checks do not validate GPU trainer collator.',
        remaining=['GPU actual-batch label check','model trainability','smoke save/reload','tiny overfit','W&B connection'],
        files={p.name:sha(p) for p in args.output_dir.iterdir()})
    save('report.json',report)
    config=dict(experiment_id='exp-009-minimal-edit',status='prepared-not-trained',model=dict(name=MODEL,revision=REVISION,adapter=None,thinking_mode=False),
        dataset=dict(train='reviewed-v2/train-reviewed.jsonl',validation='reviewed-v2/validation-reviewed.jsonl',hashes=report['source_hashes'],train_rows=80,validation_rows=20,loss='final-assistant-only'),
        training=dict(framework='unsloth',method='bf16-lora',max_seq_length=max_length,epochs=2,learning_rate=5e-5,
            per_device_train_batch_size=1,gradient_accumulation_steps=8,effective_batch_size=8,expected_optimizer_steps=20,
            optimizer='adamw_8bit',scheduler='cosine',warmup_steps=2,weight_decay=0.0,max_grad_norm=1.0,seed=3407,
            packing=False,lora=dict(rank=16,alpha=16,dropout=0,bias='none',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']),
            save_strategy='epoch',eval_strategy='epoch',report_to='wandb'),
        inference=dict(backend='vllm',temperature=0.0,repetition_penalty=1.05,thinking_mode=False,additional_system_prompt=None,output_token_budgets=[4096,8192,16384]),
        notes=['New combined data/recipe phase, not an isolated comparison with exp008.',
            '2 epochs and 5e-5 are a conservative initial hypothesis, not a retention guarantee.',
            'Validation references only used for no-grad evaluation, never training or replay.',
            'Old exp004 trainer rejects multi-turn rows and masks all assistant turns; do not launch it unchanged.',
            'GPU runner must consume explicit labels, preserve -100 padding and verify actual batches against this preflight.',
            'Each GPU preflight uses fresh base/adapters; do not continue smoke or tiny-overfit adapter into full run.'])
    save('training-config.json',config)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
