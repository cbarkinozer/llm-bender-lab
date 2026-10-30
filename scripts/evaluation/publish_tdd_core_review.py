"""Publish the assistant-reviewed, table-free app briefs and runnable core suites."""
import hashlib
import json
from pathlib import Path
import uuid
import argilla as rg

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'
BUNDLE=DOMAIN/'exp-001-local-thinking-10/app-core-v02'


def main():
    tasks=[json.loads(line) for line in (BUNDLE/'briefs.jsonl').read_text().splitlines()]
    report=json.loads((BUNDLE/'token-and-execution-report.json').read_text())
    runs={r['repo']:r for r in report['reports']}
    assert len(tasks)==len(runs)==9
    assert all(r['returncode']==0 for r in runs.values())
    source_hash=hashlib.sha256((BUNDLE/'briefs.jsonl').read_bytes()).hexdigest()
    receipt=BUNDLE/'review-receipt.json'
    if receipt.exists() and json.loads(receipt.read_text())['source_sha256']!=source_hash:
        raise ValueError('Published revision changed; create a new dataset revision.')
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    name='tdd-app-core-v02-results'
    dataset=client.datasets(name=name,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        settings=rg.Settings(guidelines='Assistant-reviewed demo artifacts. Owner review is optional and no human approval has been fabricated. Wide tables have been replaced by stacked requirement sections. Each candidate suite has passed execution, but uncovered requirements are listed honestly; these are not yet nine complete certified app acceptance suites or approved SFT targets. Unit/integration evidence, subjective/live checks, and gaps are separate. Source implementations are not model input. Roles remain unassigned; do not train on an app and claim held-out improvement on the same request/tests.',fields=[rg.TextField(name=n,title=t,use_markdown=m) for n,t,m in [('request','Natural whole-app request',True),('review','Assistant scope review and requirement checks — no table',True),('tests','Runnable compact test files and fixtures',False),('execution','Execution and Qwen token counts',True)]],questions=[rg.LabelQuestion(name='feedback',title='Feedback, only if you choose to submit a review',labels=['looks-good','needs-change','uncertain'],required=True),rg.TextQuestion(name='notes',title='Optional notes or corrections',required=False)])
        dataset=rg.Dataset(name=name,workspace=env['ARGILLA_WORKSPACE'],settings=settings,client=client);dataset.create()
    existing={str(record.id) for record in dataset.records(with_responses=False,with_suggestions=False)}
    records=[]
    for task in tasks:
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+task['id']))
        if rid in existing:continue
        run=runs[task['repo']];folder=BUNDLE/task['id']
        evidence=f"**Suite passed.**\n\nTest source: {run['test_source_tokens']:,} Qwen tokens.\n\nComplete file-output payload: {run['output_payload_tokens']:,} Qwen tokens, including fixtures and configuration.\n\nThese counts exclude request, public-interface clarification, teacher reasoning and native chat framing.\n\n"+Path(run['log']).read_text()[-1800:]
        records.append(rg.Record(id=rid,fields=dict(request=task['user_request'],review=(folder/'review.md').read_text(),tests=(folder/'test-output.md').read_text(),execution=evidence)))
    if records:dataset.records.log(records)
    assert sum(1 for _ in dataset.records(with_responses=False,with_suggestions=False))==9
    result=dict(dataset=name,dataset_id=str(dataset.id),url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode',source_sha256=source_hash,records=9,human_ratings_submitted=False)
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
