"""Publish five fresh anonymous cases, preserving all earlier Argilla reviews."""
import argparse
import json
from pathlib import Path
import uuid
from active_tdd_data import rows
from prepare_tdd_demo import save,digest
from publish_tdd_threeway_argilla import credential,api_get

LABELS=('W','X','Y','Z')


def fields(item):
    if set(item['candidates'])!=set(LABELS):raise ValueError('Expected four anonymous candidates')
    result={'requirement':item['requirement']}
    for label in LABELS:
        code=item['candidates'][label]
        if '<think>' in code or '</think>' in code:raise ValueError('Thinking trace reached reviewer')
        result['candidate_'+label.lower()]=code if code.startswith('[No complete') else '```python\n'+code+'\n```'
    return result


def publish(args):
    import argilla as rg
    key=credential(args.credential_env);client=rg.Argilla(api_url=args.url,api_key=key)
    items=rows(args.packet_dir/'primary-tests.jsonl')
    if len(items)!=5:raise ValueError('Expected five primary cases')
    schema=rg.Settings(guidelines=(
        'Compare W/X/Y/Z against the supplied requirements, with ties and all-unusable allowed. '
        'Retain=correct and useful; repair=useful parts with defects; reject=unsuitable; uncertain=insufficient evidence. '
        'Prioritize correctness, meaningful requirement coverage, real-SUT testing and justified controls/mocks. '
        'Thinking, identities and automatic runtime/static scores are hidden. Do not infer quality from length. '
        'No 1-5 assertion score or exhaustive per-assertion annotation is required. '
        'These are prospectively clarified development contracts after earlier failures, not fresh holdout tasks. '
        'Record AI assistance and prior exposure in your evidence. Never consult PRIVATE mappings. '
        'Submit each case to save the review. Existing earlier review datasets are preserved.'),
        fields=[rg.TextField(name='requirement',title='Requirement and frozen interface',use_markdown=False)]+
               [rg.TextField(name='candidate_'+v.lower(),title='Candidate '+v,use_markdown=True) for v in LABELS],
        questions=[rg.RankingQuestion(name='ranking',title='Rank W / X / Y / Z; ties allowed',values=list(LABELS),required=True)]+
                  [rg.LabelQuestion(name='assessment_'+v.lower(),title='Would you keep '+v+'?',
                    labels=['retain','repair','reject','uncertain'],required=True) for v in LABELS]+
                  [rg.TextQuestion(name='evidence',title='Code evidence, missing requirements, defects; AI assistance/prior exposure',required=True)])
    dataset_name='tdd-thinking-lr-primary-20261107-v01'
    dataset=client.datasets(name=dataset_name,workspace=args.workspace)
    if dataset is None:dataset=rg.Dataset(name=dataset_name,workspace=args.workspace,settings=schema,client=client).create()
    current=api_get(args.url,key,f'datasets/{dataset.id}/records?limit=100&include=responses')
    existing={str(r.get('external_id') or r['id']):r for r in current['items']}
    source_hash=digest(args.packet_dir/'primary-tests.jsonl');expected={};pending=[];index=[]
    for item in items:
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,dataset_name+':'+source_hash+':'+item['case_id']))
        payload=fields(item);expected[rid]=payload;index.append(dict(record_id=rid,case_id=item['case_id']))
        if rid in existing:
            if existing[rid]['fields']!=payload:raise ValueError('Existing fields differ')
        else:pending.append(rg.Record(id=rid,fields=payload))
    if set(existing)-set(expected):raise ValueError('Unexpected existing records; use a new version')
    if pending:dataset.records.log(pending)
    actual=api_get(args.url,key,f'datasets/{dataset.id}/records?limit=100&include=responses')
    if actual['total']!=5:raise ValueError('Unexpected final record count')
    for row in actual['items']:
        if row['fields']!=expected[str(row.get('external_id') or row['id'])]:raise ValueError('Display roundtrip differs')
        if row.get('suggestions'):raise ValueError('Machine suggestions must not enter blind review')
    receipt=dict(dataset_id=str(dataset.id),name=dataset_name,records=5,index=index,source_sha256=source_hash,
        url=args.url+f'/dataset/{dataset.id}/annotation-mode',model_identities_uploaded=False,
        reasoning_uploaded=False,automatic_scores_uploaded=False,
        submitted=sum(any(r['status']=='submitted' for r in row.get('responses',[])) for row in actual['items']))
    args.receipt.parent.mkdir(parents=True,exist_ok=True);save(args.receipt,receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['packet-dir','receipt','credential-env']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--url',default='http://127.0.0.1:7900');p.add_argument('--workspace',default='tdd-blind-comparison')
    publish(p.parse_args())
