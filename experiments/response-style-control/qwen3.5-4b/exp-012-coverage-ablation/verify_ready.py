"""Verify frozen paired CPU artifacts; never contacts a GPU or launches training."""
import json
from prepare_pair import A,HERE,original,load_rows,sha,encoded,save,SOURCE_HASHES

def main():
    train,validation=original()
    root=HERE/'data-reviewed-v1'
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name,expected in manifest['files'].items():
        assert sha((root/name).read_bytes())==expected,name
    reviewed=load_rows(root/'train-reviewed.jsonl')
    retained=[r for r in reviewed if r['id'].startswith('me-')]
    new=[r for r in reviewed if r['id'].startswith('bc-')]
    assert len(reviewed)==80 and len(retained)==56 and len(new)==24
    assert all(r in train for r in retained)
    draft={r['id']:r for r in load_rows(HERE/'data-draft-v1/candidates-24.jsonl')}
    assert all(r['desired_answer']==draft[r['id']]['desired_answer'] and
               r['messages']==draft[r['id']]['messages'] and
               r['review_decision']=='accept' and
               r['review_provenance']=='user-conversation-approval' and
               r['review_response_id'] is None for r in new)
    snapshot=json.loads((root/'argilla-snapshot.json').read_text(encoding='utf-8'))
    assert len(snapshot['items'])==24 and all(not r['responses'] for r in snapshot['items'])
    assert sha((root/'validation-reviewed.jsonl').read_bytes())==SOURCE_HASHES['validation-reviewed.jsonl']
    configs=[]; reports=[]
    for experiment in (A,HERE):
        preflight=experiment/'training-preflight-v1'
        config=json.loads((preflight/'training-config.json').read_text(encoding='utf-8'))
        report=json.loads((preflight/'report.json').read_text(encoding='utf-8'))
        assert report['status']=='local-preflight-passed'
        assert config['training']['epochs']==4 and config['training']['expected_optimizer_steps']==40
        assert not config['dataset']['review_required']
        for name,expected in report['files'].items():
            assert sha((preflight/name).read_bytes())==expected,name
        configs.append(config); reports.append(report)
    assert configs[0]['training']==configs[1]['training']
    assert configs[0]['model']==configs[1]['model']
    assert configs[0]['inference']==configs[1]['inference']
    assert configs[1]['dataset']['hashes']['train-reviewed.jsonl']==sha((root/'train-reviewed.jsonl').read_bytes())
    assert json.loads((HERE/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))==configs[1]
    assert load_rows(A/'training-preflight-v1/validation-tokenized.jsonl')==load_rows(HERE/'training-preflight-v1/validation-tokenized.jsonl')
    result=dict(status='both-CPU-ready-GPU-gates-needed',A_train_rows=80,B_train_rows=80,
        retained_original_rows=56,approved_new_rows=24,approval_source=manifest['approval_source'],
        validation_unchanged=True,training_configs_equal=True,training_started=False,
        target_tokens_per_epoch={config['experiment_id']:report['split_stats']['train']['target']['total']
                                for config,report in zip(configs,reports)},
        configuration_hashes={config['experiment_id']:sha((exp/'training-preflight-v1/training-config.json').read_bytes())
                              for config,exp in zip(configs,(A,HERE))})
    save(HERE/'pair-readiness-report.json',encoded(result))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
