"""Publish nine draft app requests and acceptance maps; never submit owner ratings."""
import hashlib
import json
from pathlib import Path
import uuid
import argilla as rg

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'
BRIEFS=DOMAIN/'exp-001-local-thinking-10/app-briefs-v01'


def main():
    source=BRIEFS/'briefs.jsonl'
    tasks=[json.loads(line) for line in source.read_text().splitlines()]
    assert len(tasks)==9
    for task in tasks:
        assert '\n' not in task['user_request']
        assert (BRIEFS/task['id']/'request.md').read_text().strip()==task['user_request']
        for candidate in task['provenance']['candidate_tests']:
            assert (ROOT.parent/task['repo']/candidate).is_file(), candidate
        assert [r['id'] for r in task['requirements']]==[f'R{i}' for i in range(1,len(task['requirements'])+1)]
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    receipt=BRIEFS/'review-receipt.json'
    if receipt.exists() and json.loads(receipt.read_text())['source_sha256']!=digest:
        raise ValueError('Briefs changed after publication; create a new revision/dataset to preserve owner responses.')
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    name='tdd-app-core-briefs-v01'
    dataset=client.datasets(name=name,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        settings=rg.Settings(guidelines='Review whole-app requests and proposed core behavior checks, not existing generated code. The user prompt is one paragraph and does not prescribe internal functions. The acceptance map is reviewer metadata, not hidden model input; any additional behavior must be clarified before becoming a graded requirement. These are reconstructed draft MVPs, not full historical repo reproductions. Confirm scope, request clarity, meaningful oracles and non-automatable checks. Existing tests are only candidate evidence; no compact suite is yet selected or verified against all mapped requirements. Split roles are unassigned. Do not use the same app/scenario for training and held-out evaluation. Owner ratings are never filled by the assistant.',fields=[rg.TextField(name=n,title=t,use_markdown=True) for n,t in [('request','Natural user request — proposed model input'),('instructions','Shared test-generation instruction — proposed model input'),('map','Requirements and core tests — reviewer map'),('scope','Scope and unresolved decisions'),('provenance','Sources and readiness — not model input')]],questions=[rg.LabelQuestion(name='approval',title='Is this a useful whole-app request for our demo?',labels=['approve','revise','reject','uncertain'],required=True),rg.LabelQuestion(name='scope_fit',title='Does this core scope match the app you want?',labels=['right-size','too-narrow','too-broad','uncertain'],required=True),rg.LabelQuestion(name='map_quality',title='Do the proposed checks protect the important requirements?',labels=['adequate-draft','missing-core-behavior','unjustified-expectation','uncertain'],required=True),rg.TextQuestion(name='changes',title='Changes, clarification answers, or important missing behaviors',required=False)])
        dataset=rg.Dataset(name=name,workspace=env['ARGILLA_WORKSPACE'],settings=settings,client=client);dataset.create()
    existing={str(record.id) for record in dataset.records(with_responses=False,with_suggestions=False)}
    records=[]
    for task in tasks:
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,'tdd-app-core-briefs-v01/'+task['id']))
        if rid in existing:continue
        scope=task['scope_note']+'\n\n**Public test boundary (proposal):** '+task['proposed_test_boundary']+'\n\n**Needs agreement:**\n'+'\n'.join('- '+x for x in task['open_decisions'])+'\n\n**Manual/live checks:**\n'+'\n'.join('- '+x for x in task['manual_checks'])
        provenance=dict(repo=task['repo'],split=task['split'],suite=task['suite_status'],reasoning=task['teacher_reasoning_status'],provenance=task['provenance'])
        records.append(rg.Record(id=rid,fields=dict(request=task['user_request'],instructions=task['system_instruction'],map=(BRIEFS/task['id']/'acceptance-map.md').read_text(),scope=scope,provenance='```json\n'+json.dumps(provenance,indent=2,ensure_ascii=False)+'\n```')))
    if records:dataset.records.log(records)
    count=sum(1 for _ in dataset.records(with_responses=False,with_suggestions=False))
    assert count==9,count
    result=dict(dataset=name,dataset_id=str(dataset.id),records=count,url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode',source_sha256=digest,human_ratings_submitted=False)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
