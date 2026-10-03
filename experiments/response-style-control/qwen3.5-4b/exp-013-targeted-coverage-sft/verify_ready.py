"""Verify frozen C/D artifacts locally; never claim GPU gates passed."""
import copy
import json
from prepare_next_pair import HERE, D, PARENT, original, assemble, load_rows, sha, save, encoded, jsonl
from export_review import approved_targets, apply_postreview_qa


def main():
    folder = HERE/'data-reviewed-v1'
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='human-reviewed-local-preflight-passed'
    for name,digest in manifest['files'].items():
        assert sha((folder/name).read_bytes())==digest, name
    snapshot=json.loads((folder/'argilla-snapshot.json').read_text(encoding='utf-8'))
    before=approved_targets(snapshot['items'], load_rows(HERE/'data-draft-v2/candidates-12.jsonl'))
    assert before==load_rows(folder/'reviewed-candidates-before-qa.jsonl')
    approval=json.loads((folder/'postreview-qa-approval.json').read_text(encoding='utf-8'))
    assert approval['snapshot_sha256']==sha(encoded(snapshot))
    after,changes=apply_postreview_qa(before,approval)
    assert after==load_rows(folder/'approved-candidates-12.jsonl')
    assert changes==json.loads((folder/'qa-changes.json').read_text(encoding='utf-8'))
    train,val=assemble(after)
    assert train==load_rows(folder/'train-reviewed.jsonl')
    assert val==load_rows(folder/'validation-reviewed.jsonl')
    original()
    c=json.loads((HERE/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
    d=json.loads((D/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
    assert c['dataset']==d['dataset'] and c['model']==d['model'] and c['inference']==d['inference']
    ct,dt=copy.deepcopy(c['training']),copy.deepcopy(d['training'])
    assert (ct.pop('epochs'),dt.pop('epochs'))==(4,6)
    assert (ct.pop('expected_optimizer_steps'),dt.pop('expected_optimizer_steps'))==(40,60)
    assert ct==dt and c['model']['adapter'] is None
    assert c['dataset']['hashes']['train-reviewed.jsonl']==sha(jsonl(train))
    for base in (HERE,D):
        pre=base/'training-preflight-v1'
        report=json.loads((pre/'report.json').read_text(encoding='utf-8'))
        assert report['status']=='local-preflight-passed' and report['truncated_rows']==0
        assert report['all_context_tokens_masked'] and report['native_final_end_of_turn_supervised']
        for name,digest in report['files'].items():
            assert sha((pre/name).read_bytes())==digest,name
        assert json.loads((pre/'training-config.json').read_text(encoding='utf-8'))== (c if base==HERE else d)
    for split in ('train','validation'):
        name=split+'-tokenized.jsonl'
        assert (HERE/'training-preflight-v1'/name).read_bytes()==(D/'training-preflight-v1'/name).read_bytes()
    tokenized=load_rows(HERE/'training-preflight-v1/train-tokenized.jsonl')
    parent={r['id']:r for r in load_rows(PARENT/'training-preflight-v1/train-tokenized.jsonl')}
    for row in tokenized:
        if row['id'].startswith('me-'): assert row==parent[row['id']]
    assert (HERE/'training-preflight-v1/validation-tokenized.jsonl').read_bytes()==(PARENT/'training-preflight-v1/validation-tokenized.jsonl').read_bytes()
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(c['model']['name'],revision=c['model']['revision'])
    inspection=[dict(id=r['id'],full_text=tokenizer.decode(r['input_ids'],skip_special_tokens=False),
        supervised_text=tokenizer.decode([x for x in r['labels'] if x!=-100],skip_special_tokens=False),
        input_ids=r['input_ids'],labels=r['labels']) for r in tokenized if r['id'].startswith('tc-')]
    for row in after:
        rendered=next(r for r in inspection if r['id']==row['id'])
        assert rendered['supervised_text']==row['desired_answer'].strip()+'<|im_end|>'
    save(HERE/'approved-mask-inspection-v1.json',encoded(inspection))
    report=json.loads((HERE/'training-preflight-v1/report.json').read_text(encoding='utf-8'))
    tokens=report['split_stats']['train']['target']['total']
    leak=json.loads((folder/'leakage-report.json').read_text(encoding='utf-8'))
    assert leak['status']=='no-detected-overlap' and not leak['exact_matches'] and not leak['near_flags']
    readiness=dict(status='reviewed-and-CPU-verified-awaiting-GPU',training_started=False,
        shared_train_rows=80,unchanged_validation_rows=20,retained_original_rows=68,
        reviewed_new_rows=12,argilla_decisions=manifest['decisions'],postreview_qa_rows=2,
        native_EOS_supervised=True,context_masked=True,truncated_rows=0,
        shared_train_sha256=sha(jsonl(train)),validation_sha256=sha((folder/'validation-reviewed.jsonl').read_bytes()),
        target_tokens_per_epoch=tokens,target_token_change_vs_A_percent=round(100*(tokens-5384)/5384,2),
        planned_steps=dict(C=40,D=60),planned_epochs=dict(C=4,D=6),
        approved_mask_inspection_sha256=sha((HERE/'approved-mask-inspection-v1.json').read_bytes()),
        source_configs={base.name:sha((base/'config-reviewed-v1.yaml').read_bytes()) for base in (HERE,D)},
        no_detected_leakage=True,limitation='Lexical/provenance checks cannot prove universal semantic independence.',
        GPU_gates_passed=False,remaining=['GPU endpoint/access','Pinned environment and actual-batch checks',
            'Smoke/reload/tiny-overfit checks or explicit scoped waiver','W&B authentication',
            'Independent C/D SFT, inference, verified recovery, human comparison'])
    save(HERE/'pair-readiness-report-v1.json',encoded(readiness))
    print(json.dumps(readiness,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
