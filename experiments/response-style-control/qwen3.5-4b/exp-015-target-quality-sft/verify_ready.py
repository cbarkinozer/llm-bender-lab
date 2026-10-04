"""Offline hash/masking/split check of already approved E/F artifacts; no GPU."""
import json
from prepare_pair import HERE,F,C,ROOT,HASHES,load,sha

def verify():
    manifest=json.loads((HERE/'data-reviewed-v1/manifest.json').read_text(encoding='utf-8'))
    audit=json.loads((HERE/'data-reviewed-v1/final-split-audit-v1.json').read_text(encoding='utf-8'))
    assert audit['status']=='automated-checks-passed-needs-semantic-signoff'
    for path,hash_ in audit['hash_inventory'].items():
        assert sha((ROOT/path).read_bytes())==hash_,path
    assert (HERE/'data-reviewed-v1/SEMANTIC-LEAKAGE-REVIEW.md').is_file()
    e=load(HERE/'data-reviewed-v1/train-reviewed.jsonl')
    f=load(F/'data-reviewed-v1/train-reviewed.jsonl')
    controls=load(HERE/'controls-reviewed-v1/questions-12.jsonl')
    assert e==f[:80] and len(e)==80 and len(f)==104 and len(controls)==12
    assert sha((HERE/'controls-reviewed-v1/questions-12.jsonl').read_bytes())==manifest['control_sha256']
    changes=load(HERE/'data-reviewed-v1/approved-candidates.jsonl')
    assert len(changes)==33 and all(r['review_decision'] in ('accept','rewrite') for r in changes+controls)
    assert all(r['evaluation_only'] and r['split']=='control' for r in controls)
    for arm,folder,rows in [('E',HERE,e),('F',F,f)]:
        config=json.loads((folder/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
        assert config['status']=='prepared-needs-gpu-gates'
        assert config['dataset']['review_required'] is False
        assert config['dataset']['train_rows']==len(rows) and config['dataset']['validation_rows']==20
        t=config['training']
        assert t['max_steps']==t['expected_optimizer_steps']==40
        assert (t['learning_rate'],t['effective_batch_size'],t['lora']['rank'],t['lora']['alpha'],t['seed'])==(1e-4,8,16,16,3407)
        assert t['warmup_steps']==2 and t['scheduler']=='cosine'
        assert t['save_steps']==t['eval_steps']==10
        assert config['model']['adapter'] is None
        assert manifest['train_hashes'][arm]==sha((folder/'data-reviewed-v1/train-reviewed.jsonl').read_bytes())
        assert config['dataset']['hashes']['train-reviewed.jsonl']==manifest['train_hashes'][arm]
        assert sha((folder/'data-reviewed-v1/validation-reviewed.jsonl').read_bytes())==HASHES['validation-reviewed.jsonl']
        report=json.loads((folder/'training-preflight-v1/report.json').read_text(encoding='utf-8'))
        assert report['status']=='local-preflight-passed'
        assert report['splits']==dict(train=len(rows),validation=20)
        assert report['truncated_rows']==report['zero_target_rows']==0
        assert report['all_context_tokens_masked'] and report['native_final_end_of_turn_supervised']
        for name,hash_ in report['files'].items():
            assert sha((folder/'training-preflight-v1'/name).read_bytes())==hash_,name
        assert json.loads((folder/'training-preflight-v1/training-config.json').read_text(encoding='utf-8'))==config
        tokenized=load(folder/'training-preflight-v1/train-tokenized.jsonl')
        assert [r['id'] for r in tokenized]==[r['id'] for r in rows]
        assert {r['id'] for r in tokenized}.isdisjoint({r['id'] for r in controls})
        for r in tokenized:
            assert all(x==-100 for x in r['labels'][:r['prompt_tokens']])
            assert len(r['input_ids'])<=1024 and r['target_tokens']>1
        assert load(folder/'training-preflight-v1/validation-tokenized.jsonl')==load(C/'training-preflight-v1/validation-tokenized.jsonl')
        assert all('\ufffd' not in r['desired_answer'] for r in rows)
    assert load(HERE/'training-preflight-v1/train-tokenized.jsonl')==load(F/'training-preflight-v1/train-tokenized.jsonl')[:80]
    assert not manifest['training_started']
    return dict(status='approved-data-CPU-checks-passed-GPU-gates-pending',train=dict(E=80,F=104),
        evaluation=32,actual_target_changes=manifest['actual_target_changes'],
        checks='hashes,40stepconfigs,E/Fcoreparity,approvedannotations,splitIDs,EOScontextmaskreports',training_started=False)

if __name__=='__main__': print(json.dumps(verify(),indent=2))
