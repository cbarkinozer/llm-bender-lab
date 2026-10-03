"""Verify recovered bytes, adapter identities and paired evaluation parity locally."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    runs=a.root/'exp013-exp014-runs'
    inventory=json.loads((runs/'backup-file-manifest.json').read_text(encoding='utf-8'))
    for name,expected in inventory.items():
        path=(a.root/name).resolve()
        assert path.is_relative_to(a.root.resolve())
        assert path.stat().st_size==expected['bytes'] and sha(path)==expected['sha256'],name
    arms={}
    for arm in ('C','D'):
        root=runs/arm
        result=json.loads((root/'sft-v1/result.json').read_text())
        assert result['status']=='completed'
        args=json.loads((root/'sft-v1/effective-training-arguments.json').read_text())
        assert args['num_train_epochs']==(4 if arm=='C' else 6) and args['learning_rate']==1e-4 and args['gradient_accumulation_steps']==8
        for step in ((30,40) if arm=='C' else (50,60)):
            cp=root/f'sft-v1/checkpoints/checkpoint-{step}'
            state=json.loads((cp/'trainer_state.json').read_text())
            assert state['global_step']==step
            for name in ('optimizer.pt','scheduler.pt','rng_state.pth','adapter_model.safetensors'):
                assert (cp/name).is_file()
        manifest=json.loads((root/'validation-v1/manifest.json').read_text())
        assert manifest['status']=='completed' and manifest['count']==20
        for name,expected in manifest['files'].items():
            assert sha(root/'validation-v1'/name)==expected
        for name,expected in manifest['adapter_hashes'].items():
            assert sha(root/'sft-v1/adapter'/name)==expected
        rows=[json.loads(line) for line in (root/'validation-v1/answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(rows)==20 and sum(row['native_eos'] for row in rows)==manifest['native_eos_count']
        arms[arm]=(manifest,{row['id']:row for row in rows})
    ma,ra=arms['C'];mb,rb=arms['D']
    for key in ('validation_sha256','generation','seed','revision','chat_template_sha256','backend','precision'):
        assert ma[key]==mb[key],key
    assert ra.keys()==rb.keys()
    for id,row in ra.items():
        assert row['messages']==rb[id]['messages'] and row['prompt_token_ids']==rb[id]['prompt_token_ids'] and row['desired_answer']==rb[id]['desired_answer']
    print(json.dumps(dict(status='verified',files=len(inventory),C_native_eos=ma['native_eos_count'],D_native_eos=mb['native_eos_count'])))

if __name__=='__main__':
    main()
