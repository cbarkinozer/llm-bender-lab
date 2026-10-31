"""Prepare rationale-supervised/masked arms; preserve identical teacher-forced inputs."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
from active_tdd_data import EXP,active_paths,rows,read_json
from native_tdd_labels import encode_conversation,model_fields
from export_intent_only_preview import project_record
from prepare_tdd_demo import digest,save,lines


def arm_fields(encoded,arm):
    result=deepcopy(model_fields(encoded))
    if arm not in ('A','B'):raise ValueError('Unknown arm')
    if arm=='B':
        for position in encoded['region_positions']['reasoning']:
            if set(encoded['token_regions'][position])-{'reasoning','reasoning_markup'}:
                raise ValueError('Rationale masking would touch protected answer/prompt/EOS')
            result['labels'][position]=-100
    return result


def inference_identity(preflight,config):
    shared=dict(model=config['model'],inference=config['inference'],requests_sha256=digest(preflight/'development-requests.jsonl'))
    return sha256(json.dumps(shared,sort_keys=True).encode()).hexdigest()


def main(tokenizer_path):
    from transformers import AutoTokenizer
    src=EXP/'demo-preflight-v03';out=EXP/'paired-preflight-v01'
    if out.exists():raise ValueError('Preserve previous pair')
    for entry in read_json(EXP/'native-label-audit-v01/tokenizer-pin-verification.json')['files']:
        if digest(Path(tokenizer_path)/entry['file'])!=entry['local_sha256']:raise ValueError('Wrong tokenizer pin')
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True,trust_remote_code=False)
    original=rows(src/'train-encoded.jsonl')
    source=[r for r in rows(active_paths()['tests']) if r['candidate_split']=='train']
    arrays={'A':[],'B':[]};audit=[]
    assert len(source)==len(original)==50
    for row,saved in zip(source,original):
        encoded=encode_conversation(tokenizer,project_record(row)['messages'],max_length=3072)
        a=arm_fields(encoded,'A');b=arm_fields(encoded,'B')
        assert a=={k:saved[k] for k in a} and saved['record_id']==row['record_id']
        changed=[i for i,(x,y) in enumerate(zip(a['labels'],b['labels'])) if x!=y]
        assert changed==encoded['region_positions']['reasoning']
        for arm,values in (('A',a),('B',b)):arrays[arm].append(dict(record_id=row['record_id'],**values))
        audit.append(dict(record_id=row['record_id'],masked_rationale_tokens=len(changed),
                          mixed_rationale_markup_tokens=sum(len(encoded['token_regions'][i])>1 for i in changed),
                          A_supervised=sum(x!=-100 for x in a['labels']),B_supervised=sum(x!=-100 for x in b['labels']),
                          input_ids_unchanged=a['input_ids']==b['input_ids'],answer_eos_unchanged=True))
    out.mkdir()
    for arm in ('A','B'):
        dest=out/arm;dest.mkdir()
        for name in read_json(src/'manifest.json')['files']:
            if name not in ('recipe.json','train-encoded.jsonl'):shutil.copyfile(src/name,dest/name)
        lines(dest/'train-encoded.jsonl',arrays[arm])
        recipe=read_json(src/'recipe.json');recipe['inference']['repetition_penalty']=1.15
        recipe['arm']=arm;recipe['training']['loss_policy']='rationale-supervised' if arm=='A' else 'rationale-text-masked'
        recipe['training']['loss_normalization']='Summed causal CE divided by actual nonignored shifted-label count across each accumulation group; custom loss, no double shift'
        recipe['supervised_tokens_per_epoch']=sum(r[arm+'_supervised'] for r in audit)
        recipe['evaluation']['ablation']='Direct rationale supervision holding teacher-forced inputs/exposure equal; supervised-token exposure differs'
        save(dest/'recipe.json',recipe)
        manifest=read_json(src/'manifest.json');manifest['status']='paired arrays audited locally; actual GPU loss/runtime gates pending'
        manifest['files']={p.name:digest(p) for p in dest.iterdir()};save(dest/'manifest.json',manifest)
    lines(out/'mask-audit.jsonl',audit)
    save(out/'summary.json',dict(arms=['A','B'],rows=50,input_tokens_per_epoch=91858,
         supervised_tokens_per_epoch={arm:sum(r[arm+'_supervised'] for r in audit) for arm in ('A','B')},
         masked_rationale_tokens=sum(r['masked_rationale_tokens'] for r in audit),
         mixed_rationale_markup_tokens=sum(r['mixed_rationale_markup_tokens'] for r in audit),
         shared_inference_identity=inference_identity(out/'A',read_json(out/'A/recipe.json')),
         limitation='B still conditions on rationale input; this is not rationale-free training. GPU normalization/masking tests remain required.'))
    print((out/'summary.json').read_text(encoding='utf-8'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tokenizer',required=True);main(p.parse_args().tokenizer)
