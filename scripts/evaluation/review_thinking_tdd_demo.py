"""Append completed baseline outputs to a dedicated Argilla review dataset."""
import argparse
import json
from pathlib import Path
import argilla as rg

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);args=p.parse_args()
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    name='thinking-tdd-demo-10-v01'
    dataset=client.datasets(name=name,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        settings=rg.Settings(guidelines='Quick learning demo. First check whether the requirement is clear and internally consistent. Then inspect whether each generated assertion follows the contract. Do not reward length. Execution evidence is diagnostic, not ground truth; flag possible reference/grader mistakes. No edits are applied to original generations.',
            fields=[rg.TextField(name=n,title=t,use_markdown=True) for n,t in [('contract','Requirement and API'),('thinking','Original model reasoning'),('tests','Original generated tests'),('execution','Diagnostic execution evidence')]],
            questions=[rg.LabelQuestion(name='contract_valid',title='Is the requirement clear and valid?',labels=['yes','needs-clarification','incorrect'],required=True),rg.LabelQuestion(name='suite_quality',title='Are these useful, correct tests?',labels=['retain','repair','reject','uncertain'],required=True),rg.TextQuestion(name='notes',title='Incorrect expectations, missing behaviors, or grading concerns',required=False)])
        dataset=rg.Dataset(name=name,workspace=env['ARGILLA_WORKSPACE'],settings=settings,client=client);dataset.create()
    existing={str(r.id) for r in dataset.records(with_responses=False,with_suggestions=False)}
    for task in [json.loads(x) for x in (args.run/'requirements.jsonl').read_text().splitlines()]:
        item=args.run/task['id']
        if not (item/'grade.json').exists(): continue
        import uuid
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,str(args.run)+task['id']))
        if rid in existing:continue
        grade=json.loads((item/'grade.json').read_text())
        fields=dict(contract=f"**{task['id']}**\n\n`from solution import {task['signature'].split('(')[0]}`\n\n`{task['signature']}`\n\n{task['requirements']}",thinking=(item/'thinking.txt').read_text() or '(No reasoning captured)',tests='```python\n'+(item/'generated_tests.py').read_text()+'\n```',execution='```json\n'+json.dumps(grade,indent=2)+'\n```')
        dataset.records.log([rg.Record(id=rid,fields=fields)])
    url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode'
    (args.run/'review-receipt.json').write_text(json.dumps(dict(url=url,dataset=name),indent=2)+'\n');print(url)

if __name__=='__main__':main()
