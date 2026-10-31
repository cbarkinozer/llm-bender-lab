"""Allowlist model-visible fields. Implementation/audit columns never become training text."""
from hashlib import sha256
import json
from pathlib import Path
import argparse
from active_tdd_data import active_paths, inside

ROOT=Path(__file__).resolve().parents[2]
EXP=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'


def project_record(row):
    if row['candidate_split']!='train':
        raise ValueError('Only training-family records may enter the training preview')
    messages=[]
    for message in row['messages']:
        if message['role'] not in ('system','user','assistant'):
            raise ValueError('Unexpected message role')
        projected={'role':message['role'],'content':message['content']}
        if message['role']=='assistant' and 'reasoning_content' in message:
            projected['reasoning_content']=message['reasoning_content']
        messages.append(projected)
    if [m['role'] for m in messages]!=['system','user','assistant']:
        raise ValueError('Expected a single intent-to-target conversation')
    return {'messages':messages}


def main(output=None,planning=None,reliability=None):
    paths=active_paths()
    out=inside(output) if output else paths['preview']
    if out.exists(): raise ValueError('Preserve existing preview; use a new revision')
    out.mkdir()
    selections=[('tests',paths['tests']),
                ('planning',inside(planning+'/records.jsonl') if planning else paths['planning']),
                ('reliability',inside(reliability+'/records.jsonl') if reliability else paths['reliability'])]
    index=[];hashes={}
    for name,path in selections:
        rows=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
        selected=[row for row in rows if row['candidate_split']=='train']
        projected=[project_record(row) for row in selected]
        output=out/(name+'-train-preview.jsonl')
        output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in projected),encoding='utf-8',newline='\n')
        hashes[name]=sha256(output.read_bytes()).hexdigest()
        for number,row in enumerate(selected,1):
            index.append(dict(preview_file=output.name,line=number,record_id=row['record_id'],source_group=row['source_group'],
                              input_records=str(path.relative_to(ROOT)),input_sha256=sha256(path.read_bytes()).hexdigest()))
    (out/'audit-index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'manifest.json').write_text(json.dumps(dict(status='projection preview only; not approved training data',training_enabled=False,
        counts={name:sum(r['preview_file']==name+'-train-preview.jsonl' for r in index) for name,_ in selections},
        user_policy='User intent, clarification, planning, file tasks and requirement-based pytest targets only. Repository implementation source is excluded from model input and targets. Source columns may remain audit-only.',
        allowed_fields={'record':['messages'],'message':['role','content'],'assistant_optional':['reasoning_content']},
        excluded_columns='All other fields, including source code, reference implementations, mutation probes, validation logs and scoring references.',
        test_code_policy='Generated pytest targets and necessary synthetic code snippets/test fixtures are task content, not repository implementation solutions.',
        semantic_limit='The allowlist prevents accidental source-column leakage. It cannot prove implementation text was not embedded inside content; review model-visible messages before enabling training.',
        loss_label_audit='pending',implementation_source_in_messages_review='pending',output_sha256=hashes,
        builder_sha256=sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Intent-only previews:',len(index),'train-family records; source/audit columns excluded; training disabled.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output');parser.add_argument('--planning');parser.add_argument('--reliability')
    args=parser.parse_args();main(args.output,args.planning,args.reliability)
