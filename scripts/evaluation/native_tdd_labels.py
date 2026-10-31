"""Fail-closed Qwen3.5 text-only, single-assistant-turn SFT preprocessing.

No string-search completion mask, template changes, truncation, packing or model load.
Labels are unshifted; a causal-LM loss must perform its normal next-token shift.
"""
from copy import deepcopy

IGNORE=-100
CONTROL=('<|im_start|>','<|im_end|>','<|endoftext|>','<think>','</think>')


def encode_conversation(tokenizer,messages,max_length=8192):
    if [m['role'] for m in messages]!=['system','user','assistant']:
        raise ValueError('Only system/user/assistant single-turn conversations are supported')
    if not tokenizer.is_fast:raise ValueError('Fast tokenizer offsets are required')
    for message in messages:
        if set(message)-{'role','content','reasoning_content'}:raise ValueError('Unexpected message fields; use intent-only projection')
        for key in ('content','reasoning_content'):
            text=message.get(key,'')
            if not isinstance(text,str):raise ValueError('Only plain text is supported')
            if any(marker in text for marker in CONTROL):raise ValueError('Reserved template markup inside message content')
    assistant=messages[-1];reason=assistant.get('reasoning_content','').strip();answer=assistant['content'].strip()
    if not answer:raise ValueError('Empty assistant answer')
    options=dict(add_generation_prompt=False,enable_thinking=True)
    rendered=tokenizer.apply_chat_template(messages,tokenize=False,**options)
    prefix=tokenizer.apply_chat_template(messages[:-1],tokenize=False,**options)+'<|im_start|>assistant\n'
    pieces=[('prompt',prefix,False),('reasoning_markup','<think>\n',True),('reasoning',reason,True),
            ('reasoning_markup','\n</think>\n\n',True),('answer',answer,True),('end_of_turn','<|im_end|>',True),('tail','\n',False)]
    expected=''.join(text for _,text,_ in pieces)
    if rendered!=expected:raise ValueError('Native template changed or unsupported serialization; refuse inferred masks')
    spans=[];position=0
    for name,text,supervised in pieces:
        spans.append(dict(region=name,start=position,end=position+len(text),supervised=supervised));position+=len(text)
    tokenized=tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True,truncation=False)
    ids=list(tokenized['input_ids']);offsets=tokenized['offset_mapping']
    native=tokenizer.apply_chat_template(messages,tokenize=True,**options)
    native=list(native['input_ids']) if hasattr(native,'keys') else list(native)
    if ids!=native:raise ValueError('Rendered tokenization differs from native chat tokenization')
    if len(ids)>max_length:raise ValueError('Sequence exceeds limit; truncation is forbidden')
    masks=[];regions=[];positions={name:[] for name,_,_ in pieces}
    for i,(start,end) in enumerate(offsets):
        if start==end:raise ValueError('Unmapped token offset')
        overlapping=[s for s in spans if s['start']<s['end'] and start<s['end'] and end>s['start']]
        decisions={s['supervised'] for s in overlapping}
        if len(decisions)!=1:raise ValueError('Token straddles supervised/masked character boundary')
        masks.append(decisions.pop());names=sorted({s['region'] for s in overlapping});regions.append(names)
        for name in names:positions[name].append(i)
    encoded=dict(input_ids=ids,attention_mask=[1]*len(ids),labels=[id if yes else IGNORE for id,yes in zip(ids,masks)],
                 expected_supervise_mask=masks,token_regions=regions,region_positions=positions,
                 reasoning_present=bool(reason),rendered=rendered)
    validate_labels(encoded)
    end_positions=positions['end_of_turn']
    if len(end_positions)!=1 or ids[end_positions[0]]!=tokenizer.eos_token_id:
        raise ValueError('Expected exactly one native assistant end-of-turn EOS token')
    if not positions['answer'] or (reason and not positions['reasoning']):raise ValueError('Missing assistant text tokens')
    return encoded


def validate_labels(example):
    keys=('input_ids','attention_mask','labels','expected_supervise_mask')
    if len({len(example[k]) for k in keys})!=1:raise ValueError('Misaligned arrays')
    supervised=0
    for id,attention,label,expected in zip(*(example[k] for k in keys)):
        if attention not in (0,1):raise ValueError('Invalid attention mask')
        if not attention:
            if expected or label!=IGNORE:raise ValueError('Padding contributes loss')
        elif expected:
            if label!=id:raise ValueError('Supervised token missing or wrong label')
            supervised+=1
        elif label!=IGNORE:raise ValueError('Prompt or tail contributes loss')
    if not supervised:raise ValueError('No supervised tokens')


def pad_examples(examples,pad_token_id,side='right',length=None):
    if side not in ('left','right'):raise ValueError('Invalid padding side')
    if not examples:raise ValueError('Empty batch')
    target=length or max(len(e['input_ids']) for e in examples)
    result=[]
    for original in examples:
        validate_labels(original)
        count=target-len(original['input_ids'])
        if count<0:raise ValueError('Padding length would truncate input')
        example={k:deepcopy(original[k]) for k in ('input_ids','attention_mask','labels','expected_supervise_mask')}
        for key,value in [('input_ids',pad_token_id),('attention_mask',0),('labels',IGNORE),('expected_supervise_mask',False)]:
            pad=[value]*count;example[key]=pad+example[key] if side=='left' else example[key]+pad
        validate_labels(example);result.append(example)
    return result


def model_fields(encoded):
    """Only these arrays may be supplied to the later trainer/model."""
    validate_labels(encoded)
    return {key:encoded[key] for key in ('input_ids','attention_mask','labels')}
