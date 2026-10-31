"""Audit the active intent-only projection and save actual unshifted SFT arrays."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import gzip
from hashlib import sha256,sha1
import importlib.metadata
import json
from pathlib import Path
import sys
import urllib.request

from active_tdd_data import EXP,active_paths,read_json,rows,inside
from native_tdd_labels import encode_conversation,pad_examples,model_fields,IGNORE

REVISION='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
PIN_URL='https://huggingface.co/api/models/Qwen/Qwen3.5-4B/revision/'+REVISION+'?blobs=true'


def digest(path):return sha256(path.read_bytes()).hexdigest()
def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
def jsave(path,value):save(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def verify_tokenizer(path):
    remote=json.load(urllib.request.urlopen(PIN_URL,timeout=30))
    if remote['sha']!=REVISION:raise ValueError('Wrong remote revision')
    checked=[]
    for name in ('tokenizer.json','tokenizer_config.json','chat_template.jinja','config.json'):
        entry=next(s for s in remote['siblings'] if s['rfilename']==name);data=(path/name).read_bytes()
        if 'lfs' in entry:
            kind='sha256';actual=sha256(data).hexdigest();expected=entry['lfs']['sha256']
        else:
            kind='git-blob-sha1';actual=sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();expected=entry['blobId']
        if actual!=expected:raise ValueError('Pinned tokenizer asset mismatch: '+name)
        checked.append(dict(file=name,kind=kind,expected=expected,actual=actual,local_sha256=sha256(data).hexdigest(),bytes=len(data),matched=True))
    return dict(source=PIN_URL,revision=REVISION,checked_at=datetime.now(timezone.utc).isoformat(),files=checked)


def main(args):
    paths=active_paths();out=inside(args.output)
    if out.exists():raise ValueError('Preserve the existing audit; choose a new output revision')
    tokenizer_path=Path(args.tokenizer)
    pin=verify_tokenizer(tokenizer_path)
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True,trust_remote_code=False)
    if tokenizer.chat_template!=(tokenizer_path/'chat_template.jinja').read_text(encoding='utf-8'):
        raise ValueError('Loaded template differs from verified template file')
    index=read_json(paths['preview']/'audit-index.json');active={r['record_id']:r for p in (paths['tests'],paths['planning'],paths['reliability']) for r in rows(p)}
    actual_preview={}
    for filename in {entry['preview_file'] for entry in index}:
        if Path(filename).name!=filename:raise ValueError('Unexpected preview path')
        actual_preview[filename]=rows(paths['preview']/filename)
    if len(index)!=sum(len(r) for r in actual_preview.values()):raise ValueError('Preview index cardinality mismatch')
    seen=set();audits=[];arrays=[];samples=[];track_counts=Counter();totals=Counter();inputs={}
    for entry in index:
        position=(entry['preview_file'],entry['line'])
        if position in seen:raise ValueError('Duplicate preview index entry')
        seen.add(position)
        row=actual_preview[entry['preview_file']][entry['line']-1];source=active[entry['record_id']]
        if set(row)!={'messages'} or source['candidate_split']!='train' or source['messages']!=row['messages']:
            raise ValueError('Projection mismatch, audit-column leak or heldout row')
        encoded=encode_conversation(tokenizer,row['messages'],args.max_length)
        ids=encoded['input_ids'];labels=encoded['labels'];supervised=sum(label!=IGNORE for label in labels)
        rendered=encoded['rendered'];decoded=tokenizer.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if decoded!=rendered:raise ValueError('Native render round-trip changed')
        supervised_text=tokenizer.decode([id for id,label in zip(ids,labels) if label!=IGNORE],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        expected_body=rendered.split('<|im_start|>assistant\n',1)[1].removesuffix('\n')
        if supervised_text!=expected_body:raise ValueError('Supervised text differs from the complete native assistant body')
        for side in ('left','right'):
            for pad_id in (tokenizer.pad_token_id,tokenizer.eos_token_id):
                padded=pad_examples([encoded],pad_id,side,len(ids)+7)[0]
                if sum(label!=IGNORE for label in padded['labels'])!=supervised:raise ValueError('Padding changed loss count')
                if sum(label==tokenizer.eos_token_id for label in padded['labels'])!=1:raise ValueError('Assistant EOS lost or padding EOS contributes loss')
        track=entry['preview_file'].split('-train-preview')[0];track_counts[track]+=1
        region_counts={name:len(positions) for name,positions in encoded['region_positions'].items()}
        audit=dict(record_id=entry['record_id'],track=track,sequence_tokens=len(ids),supervised_tokens=supervised,
                   ignored_tokens=len(ids)-supervised,reasoning_present=encoded['reasoning_present'],region_token_memberships=region_counts,
                   region_positions=encoded['region_positions'],checks=dict(native_ids_match=True,round_trip=True,prompt_masked=True,
                     reasoning_supervised=encoded['reasoning_present'],answer_supervised=True,assistant_eos_supervised=True,
                     trailing_newline_masked=True,padding_both_sides=True,pad_equal_eos_safe=True,truncated=False),
                   arrays_sha256=sha256(json.dumps(model_fields(encoded),sort_keys=True).encode()).hexdigest())
        audits.append(audit);arrays.append(dict(record_id=entry['record_id'],**model_fields(encoded)))
        totals.update(sequences=1,input_tokens=len(ids),supervised_tokens=supervised,ignored_tokens=len(ids)-supervised,
                      with_reasoning=int(encoded['reasoning_present']),without_reasoning=int(not encoded['reasoning_present']))
        if track not in {s['track'] for s in samples}:
            boundary=next(i for i,label in enumerate(labels) if label!=IGNORE)
            window=list(range(max(0,boundary-5),min(len(ids),boundary+12)))+encoded['region_positions']['end_of_turn']+encoded['region_positions']['tail']
            samples.append(dict(record_id=entry['record_id'],track=track,supervised_text=supervised_text,
                                boundary_tokens=[dict(position=i,id=ids[i],token=tokenizer.convert_ids_to_tokens(ids[i]),label=labels[i],regions=encoded['token_regions'][i]) for i in window]))
    if dict(track_counts)!={'tests':50,'planning':13,'reliability':15}:raise ValueError('Unexpected active dataset counts')
    out.mkdir()
    jsave(out/'tokenizer-pin-verification.json',pin)
    save(out/'per-record.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in audits))
    jsave(out/'boundary-examples.json',samples)
    # Only intent-projection tokens and labels are stored, no implementation/reference columns.
    payload=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in arrays).encode('utf-8')
    (out/'encoded-labels.jsonl.gz').write_bytes(gzip.compress(payload,mtime=0))
    for path in [paths['index'],paths['planning'],paths['reliability'],paths['tests'],paths['preview']/'audit-index.json']+list(paths['preview'].glob('*-train-preview.jsonl')):
        inputs[path.relative_to(EXP).as_posix()]=digest(path)
    report=dict(status='passed for this preprocessing implementation and these active inputs',counts=dict(totals),tracks=dict(track_counts),
                max_sequence_tokens=max(a['sequence_tokens'] for a in audits),max_length=args.max_length,truncation_count=0,
                tokenizer_revision_verified=True,tokenizer_path=str(tokenizer_path),eos_token=tokenizer.eos_token,eos_token_id=tokenizer.eos_token_id,
                pad_token=tokenizer.pad_token,pad_token_id=tokenizer.pad_token_id,ignore_index=IGNORE,
                policy=dict(scope='single system/user/assistant plain-text conversations only',thinking_enabled=True,
                            supervised='Entire native assistant body: think markup, supplied rationale if any, answer and native assistant im_end EOS.',
                            masked='All system/user tokens, assistant role header, trailing post-EOS newline, and padding.',
                            label_shift='Unshifted labels; causal model loss performs next-token shift. Do not shift these again in a collator.',
                            reasoning_absent='Preserve the native empty think block; do not invent rationale. 28 examples teach immediate closure.',
                            padding='Dynamic batch padding; position-based masks, both sides tested including pad==EOS.',
                            packing='Disabled; no cross-example attention or label packing is audited.',
                            truncation='Forbidden; overflow fails instead of removing targets or EOS.',
                            mask_method='Verified native rendering plus fast-tokenizer character offsets; fail on mixed-loss token boundary. No template generation-tag mask assumed.',
                            region_counts='Membership counts can overlap at BPE boundaries; do not sum them as disjoint loss counts.'),
                trainer_label_parity_verified=False,training_enabled=False,
                limitation='No trainer is configured. This audit establishes a reusable preprocessor and its actual label arrays, not that an arbitrary future trainer preserves them. Compare trainer batches before a run.',
                input_sha256=inputs,code_sha256={name:digest(Path(__file__).with_name(name)) for name in ['native_tdd_labels.py','audit_native_tdd_labels.py']},
                environment=dict(python=sys.version,transformers=importlib.metadata.version('transformers'),tokenizers=importlib.metadata.version('tokenizers')))
    jsave(out/'report.json',report)
    jsave(out/'integrity.json',{p.relative_to(out).as_posix():digest(p) for p in out.iterdir() if p.is_file() and p.name!='integrity.json'})
    print(json.dumps({k:report[k] for k in ['status','counts','tracks','max_sequence_tokens','trainer_label_parity_verified']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--tokenizer',required=True);parser.add_argument('--output',default='native-label-audit-v01');parser.add_argument('--max-length',type=int,default=8192)
    main(parser.parse_args())
