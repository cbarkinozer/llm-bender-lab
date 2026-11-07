"""Import anonymous comparisons into local Argilla; preserve existing reviews."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import urllib.request
import uuid
from active_tdd_data import EXP,rows,read_json
from prepare_tdd_demo import digest,save


def credential(path):
    values={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);values[k.strip()]=v.strip().strip('\"\'')
    return values['ARGILLA_API_KEY']


def api_get(url,key,path):
    request=urllib.request.Request(url.rstrip('/')+'/api/v1/'+path,headers={'X-Argilla-Api-Key':key})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)


def payload(item,primary):
    if set(item['candidates'])!={'X','Y','Z'}:raise ValueError('Expected anonymous X/Y/Z only')
    fields={'requirement':item['requirement']}
    for label in ('X','Y','Z'):
        text=item['candidates'][label]
        if '</think>' in text or '<think>' in text:raise ValueError('Reasoning trace reached review fields')
        fields['candidate_'+label.lower()]='```python\n'+text+'\n```' if primary and not text.startswith('[No complete') else text
    return fields


def settings(rg,primary):
    questions=[rg.RankingQuestion(name='ranking',title='Rank X / Y / Z — ties are allowed',
        description='1 = best. Equal ranks and all-unusable ties are valid. Judge correctness before style.',values=['X','Y','Z'],required=True)]
    for label in ('X','Y','Z'):
        questions.append(rg.LabelQuestion(name='assessment_'+label.lower(),title=('Would you keep '+label+'?' if primary else 'Requirement handling — '+label),
            labels=['retain','repair','reject','uncertain'] if primary else ['sound','partial','incorrect','uncertain'],required=True))
        if primary:
            questions.append(rg.RatingQuestion(name='assertion_strength_'+label.lower(),title='Assertion strength — '+label,
                description='Optional:1 weak/trivial,5 discriminating and requirement-justified.',values=[1,2,3,4,5],required=False))
    questions.append(rg.TextQuestion(name='evidence',title='Evidence: incorrect expectations, missing behavior, assumptions or smells',required=True))
    return rg.Settings(guidelines=(
        'Blind development comparison: X/Y/Z identities are randomized separately for each case. '
        'Read the supplied requirement and judge each candidate independently before ranking. '
        'Do not reward brevity or length alone. Ties, all-reject and uncertainty are valid. '
        'Retain means correct and useful; repair means useful parts with defects; reject means unsuitable. '
        'Check assertion justification, positive/negative controls, API assumptions, permitted mocks, '
        'missing behavior and test smells. Flag ambiguous contracts rather than inventing requirements. '
        'Reasoning traces, model labels and automatic execution scores are hidden during initial review. '
        'Complete Python code is shown even when filename formatting or test naming is wrong; '
        'strict format/runtime results are accounted separately. No reference implementation is supplied. '
        'Use evidence from the code; do not search for model identities or consult PRIVATE mapping files. '
        'Primary test tasks and supporting planning/clarification probes are separate capabilities. '
        'Click Submit to save each review. No suggested or prefilled human judgments are imported.'),
        fields=[rg.TextField(name='requirement',title='Requirement and explicit interface',use_markdown=False)]+
               [rg.TextField(name='candidate_'+label.lower(),title='Candidate '+label,use_markdown=True) for label in ('X','Y','Z')],
        questions=questions)


def publish(args,key):
    import argilla as rg
    client=rg.Argilla(api_url=args.url,api_key=key)
    workspace=client.workspaces(name=args.workspace)
    if workspace is None:workspace=rg.Workspace(name=args.workspace,client=client).create()
    receipt=dict(api_url=args.url,workspace=args.workspace,blinded=True,model_identities_uploaded=False,
                 reasoning_uploaded=False,automatic_scores_uploaded=False,datasets={})
    for kind,filename,primary in [('primary','primary-tests.jsonl',True),('supporting','supporting-probes.jsonl',False)]:
        source=args.packet_dir/filename;items=rows(source);sha=digest(source)
        name='tdd-threeway-'+kind+'-20261107-v01'
        dataset=client.datasets(name=name,workspace=args.workspace)
        if dataset is None:dataset=rg.Dataset(name=name,workspace=args.workspace,settings=settings(rg,primary),client=client).create()
        existing=api_get(args.url,key,f'datasets/{dataset.id}/records?limit=100&include=responses')
        by_id={str(r.get('external_id') or r['id']):r for r in existing['items']}
        records=[];index=[]
        for item in items:
            rid=str(uuid.uuid5(uuid.NAMESPACE_URL,'tdd-threeway:'+kind+':'+sha+':'+item['case_id']))
            fields=payload(item,primary);index.append(dict(record_id=rid,case_id=item['case_id']))
            if rid in by_id:
                if by_id[rid]['fields']!=fields:raise ValueError('Existing review content differs; use a new dataset version')
            else:records.append(rg.Record(id=rid,fields=fields))
        if records:dataset.records.log(records)
        actual=api_get(args.url,key,f'datasets/{dataset.id}/records?limit=100&include=responses')
        expected={r['record_id']:payload(item,primary) for r,item in zip(index,items)}
        if actual['total']!=len(items):raise ValueError('Unexpected review row count')
        for record in actual['items']:
            rid=str(record.get('external_id') or record['id'])
            if record['fields']!=expected[rid]:raise ValueError('Argilla display roundtrip changed content')
            if record.get('suggestions'):raise ValueError('Unexpected suggestions in blind review')
        receipt['datasets'][kind]=dict(id=str(dataset.id),name=name,records=len(items),source_sha256=sha,index=index,
            url=args.url.rstrip('/')+f'/dataset/{dataset.id}/annotation-mode',
            saved_responses=sum(len(r.get('responses',[])) for r in actual['items']))
    save(args.receipt,receipt);print(json.dumps(receipt,indent=2))


def export(args,key):
    receipt=read_json(args.receipt)
    if args.output is None:raise ValueError('Export requires a new output directory')
    if args.output.exists():raise ValueError('Preserve earlier annotation exports')
    args.output.mkdir(parents=True)
    counts={}
    for kind,entry in receipt['datasets'].items():
        snapshot=api_get(args.url,key,f'datasets/{entry["id"]}/records?limit=100&include=responses')
        save(args.output/(kind+'-snapshot.json'),snapshot)
        counts[kind]=dict(records=snapshot['total'],submitted=sum(any(r['status']=='submitted' for r in item.get('responses',[])) for item in snapshot['items']))
    save(args.output/'manifest.json',dict(exported_at=datetime.now(timezone.utc).isoformat(),datasets=counts,
         receipt_sha256=digest(args.receipt),model_identities_unblinded=False))
    print(json.dumps(counts))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['publish','export'])
    p.add_argument('--credential-env',type=Path,required=True);p.add_argument('--url',default='http://127.0.0.1:7900')
    p.add_argument('--workspace',default='tdd-blind-comparison')
    p.add_argument('--packet-dir',type=Path,default=Path(r'C:\Users\barkin\Documents\llm-bender-artifacts\tdd-gpu-20261107\blind-three-way-v02\for-reviewer'))
    p.add_argument('--receipt',type=Path,default=EXP/'gpu-results-20261107/argilla-review-v01/receipt.json')
    p.add_argument('--output',type=Path)
    a=p.parse_args();key=credential(a.credential_env)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    if a.action=='publish':publish(a,key)
    else:export(a,key)
