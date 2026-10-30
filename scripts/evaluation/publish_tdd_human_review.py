"""Nine manual approval records, with explicit alignment and quality checks."""
from hashlib import sha256
import json
from pathlib import Path
import uuid
import argilla as rg

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'
BUNDLE=DOMAIN/'exp-001-local-thinking-10/app-core-v02'
SMELLS=['Assertion Roulette','Eager Test','Mystery Guest','Magic Number Test','Obscure Test','Lack of Cohesion','Conditional Test Logic','External Dependency','Unverified Action','Trivial Assertion','Duplicated Setup']
GUIDELINES='''Manually review all nine app candidates. No answers are prefilled. This is evidence-assisted human review: assistant findings and execution results are visible, not an independent blinded paper annotation.

For each app:
1. Compare the natural request with the documented source app and declared MVP scope.
2. Read the exact model input. Anything available only in source code, test helpers or the reviewer map is NOT automatically information the model receives.
3. Check whether imports, callable names, schemas, outputs, errors, defaults and tolerances needed by the tests are specified in the request or a visible interface agreement. Current public boundaries are proposals, not owner-approved agreements. Mark missing context when needed.
4. Check coverage against every important testable requirement, including boundaries, failures and state preservation. Record manual/browser/model-quality checks separately; passing a narrow subset does not cover the whole app.
5. Check each expectation for correctness and useful fault discrimination, not merely equality syntax. Oracle strength and correctness are independent. TRIVIAL: SUT-independent/static truth. WEAK: coarse truthiness/nullity/type. STRONG: a specific value, content, range, exception, state or interaction contract. UNKNOWN: insufficient evidence. A wrong equality can be STRONG and incorrect. Tensor/DataFrame comparison helpers can be strong numeric oracles. Appropriate null checks need not be removed merely to make every assertion syntactically strong.
6. Review smells contextually. Multiple coherent assertions are not automatically Assertion Roulette; isolated temporary files are not automatically Mystery Guest; necessary boundary values are not automatically Magic Number Test. Cite locations and concrete harm.
7. Submit approve only if the current declared scope is relevant, the input is sufficient to derive the tests, important requirements are covered, expectations are correct, assertions are useful and there are no actionable smells. Otherwise choose revise/reject/uncertain and explain. Known uncovered requirements remain visible. Do not silently shrink the scope to obtain approval.

Approval here concerns the current request/interface/test candidate. It does not certify an 8K final SFT record: reasoning and full native-template length are not yet available. These source-informed examples are not a held-out evaluation if used for training. No training starts or split is assigned by submitting a response.'''


def main():
    tasks=[json.loads(line) for line in (BUNDLE/'briefs.jsonl').read_text().splitlines()]
    runs={r['repo']:r for r in json.loads((BUNDLE/'token-and-execution-report.json').read_text())['reports']}
    assert len(tasks)==len(runs)==9
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    name='tdd-nine-apps-human-review-v01'
    dataset=client.datasets(name=name,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        questions=[rg.LabelQuestion(name=n,title=t,labels=labels,required=True) for n,t,labels in [
            ('source_relevance','1. Does the request match the source app and declared scope?',['yes','partly','no','uncertain']),
            ('input_sufficiency','2. Can these tests be derived from the visible prompt and interface?',['yes','missing-interface','missing-behavior','both-missing','uncertain']),
            ('coverage','3. Are all important testable requirements covered in enough detail?',['yes','minor-gaps','major-gaps','uncertain']),
            ('expectation_correctness','4. Are the asserted expected outcomes justified and correct?',['yes','some-wrong','unjustified-assumptions','uncertain']),
            ('assertion_quality','5. Do assertions meaningfully protect behavior against bugs?',['strong-and-useful','mixed-needs-improvement','weak-or-trivial','uncertain']),
            ('smell_quality','6. Are there actionable test smells?',['none-found','minor-smells','major-smells','uncertain']),
            ('approval','7. Overall manual decision for this request/test candidate',['approve','revise','reject','uncertain']),
        ]]
        questions += [rg.MultiLabelQuestion(name='smells',title='Smell categories found (optional; explain locations below)',labels=SMELLS,required=False),rg.TextQuestion(name='missing_context',title='Missing interface details, ambiguous behavior, or unsupported assumptions',required=False),rg.TextQuestion(name='missing_tests',title='Missing requirements/tests and manual checks needed',required=False),rg.TextQuestion(name='evidence',title='Incorrect/weak assertions or smells: file, test name, reason and requested fix',required=False)]
        settings=rg.Settings(guidelines=GUIDELINES,fields=[rg.TextField(name=n,title=t,use_markdown=m) for n,t,m in [
            ('model_input','Exact proposed model input — no source implementation',True),
            ('interface','Proposed boundary versus information actually specified',True),
            ('requirements','Requirement coverage, assistant findings and known gaps',True),
            ('tests','Complete candidate test files, fixtures and configuration',False),
            ('source','Source app context and references — review evidence, NOT model input',True),
            ('execution','Execution and token evidence — NOT semantic approval',True),
        ]],questions=questions)
        dataset=rg.Dataset(name=name,workspace=env['ARGILLA_WORKSPACE'],settings=settings,client=client);dataset.create()
    existing={str(record.id) for record in dataset.records(with_responses=False,with_suggestions=False)}
    records=[];packets=[]
    for task in tasks:
        folder=BUNDLE/task['id'];run=runs[task['repo']]
        # Verify that displayed tests still match the executed snapshot.
        for file in run['files']:
            assert sha256((folder/file['path']).read_bytes()).hexdigest()==file['sha256'],file['path']
        tests=(folder/'test-output.md').read_text()
        original_input='**System instruction:**\n\n'+task['messages'][0]['content']+'\n\n**User request:**\n\n'+task['messages'][1]['content']
        interface='**Proposed public test boundary:**\n\n'+task['proposed_test_boundary']+'\n\n**Current status:** this boundary description is not a complete interface agreement. Actual imports and call signatures appear in the test files; do not assume the model knows them unless they are specified in its input.\n\n**Assistant decisions (review material; not yet added to the exact model input above):**\n\n'+'\n'.join('- '+x for x in task['assistant_decisions'])
        readme=ROOT.parent/task['repo']/'README.md'
        excerpt=readme.read_text(errors='replace')[:5000]
        source='**Local checkout:** `'+str(readme.parent)+'`\n\n**Recorded source revision:** `'+run['source_commit']+'`\n\n**Working tree had local changes when executed:** '+str(run['source_dirty'])+'\n\n**README excerpt (context only, not complete implementation verification):**\n\n'+excerpt+'\n\n**Existing test references:**\n\n'+'\n'.join('- `'+x+'`' for x in task['provenance']['candidate_tests'])+'\n\nFull source remains in the local checkout; this excerpt cannot establish implementation correctness.'
        execution=f"**Current suite passed.**\n\nFull test-file output: **{run['output_payload_tokens']:,} Qwen tokens**, including fixtures/configuration.\n\n8,192 is the intended total SFT sequence cap. This count excludes request, clarified interface, teacher reasoning and native chat framing; full fit is NOT yet verified.\n\nPassing the existing implementation does not prove correctness, adequate coverage or smell-free quality.\n\n**Run log:**\n\n"+Path(run['log']).read_text()[-1400:]
        fields=dict(model_input=original_input,interface=interface,requirements=(folder/'review.md').read_text(),tests=tests,source=source,execution=execution)
        rid=str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+task['id']))
        packet=dict(id=rid,repo=task['repo'],fields=fields)
        packets.append(packet)
        if rid not in existing:records.append(rg.Record(id=rid,fields=fields))
    packet_path=BUNDLE/'human-review-v01/packets.jsonl'
    packet_text=''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in packets)
    if packet_path.exists() and packet_path.read_text()!=packet_text:
        raise ValueError('Published review material changed; create a new revision to preserve annotations.')
    if records:dataset.records.log(records)
    count=sum(1 for _ in dataset.records(with_responses=False,with_suggestions=False))
    assert count==9,count
    out=BUNDLE/'human-review-v01';out.mkdir(exist_ok=True)
    (out/'packets.jsonl').write_text(packet_text)
    (out/'GUIDELINES.md').write_text(GUIDELINES+'\n')
    receipt=dict(dataset=name,dataset_id=str(dataset.id),records=count,url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode',required_checks=['source_relevance','input_sufficiency','coverage','expectation_correctness','assertion_quality','smell_quality','approval'],human_ratings_submitted=False,packet_sha256=sha256((out/'packets.jsonl').read_bytes()).hexdigest())
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
