"""Publish versioned TDD review displays without altering model text or annotations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import uuid
import argilla as rg
from tdd_review_prechecks import META_DEFECT, render_test_field

ROOT=Path(__file__).resolve().parents[2]
DOMAIN=ROOT/'experiments/unit-test-generation/qwen3.5-4b'
BUNDLE=DOMAIN/'exp-001-local-thinking-10/app-core-v03'
NAME='tdd-nine-apps-human-review-v02'
GUIDELINES='''Review framing B: natural request + visible preparation constraints -> decisions, proposed interface, requirement map, complete pytest files, manual checks, always in that order. Concise rationale is separately reviewable. API names may be proposed in the TARGET; they need not appear in the INPUT. Assistant choices are never historical owner clarifications. Nonessential undecided choices must remain visible.

This is evidence-assisted demo annotation, not blinded scientific review. New backend reference modules do not certify original app UI/CLI wiring. Manual/live integration is pending and explicitly listed. The paper repo and GitHub-insignia are held out from training; review approval cannot change their split.

Option anchors:
Q1 Source relevance: yes = behavior matches source/reference and declared target scope; too-broad = request asks beyond suite/reference; too-narrow = tests require extra behavior absent from request and declared proposals; mismatch = different application behavior; uncertain = source evidence unavailable.
Q2 Interface sufficiency: yes = imports, signatures, schemas and decisions are declared in input OR target agreement; minor-gaps = one or two missing details require guessing; no = undeclared APIs/behavior required; uncertain = cannot inspect evidence. An import inventory alone does not prove method/schema sufficiency.
Q3 Coverage: yes = every important requirement has its core tests or appropriate manual checks; partial-but-disclosed = limitations are explicit and acceptable for this demo; no = a testable requirement is silently missing; uncertain = evidence missing. Do not hide absent backend tests by relabeling them subjective. Live/controller wiring may be checked manually but remains unverified.
Q4a Correctness: all-correct = expected outcomes are correct; some-wrong = at least one wrong expectation; cannot-verify = needed evidence missing.
Q4b Justification: yes = expectations follow from request and explicitly proposed choices; unexplained = values or decisions rely on unstated facts; uncertain = evidence missing. Framing B permits justified design proposals, not pretending names came from the user.
Q5 Assertions: strong = meaningful behavior checks and a killed TARGETED variant for every core requirement; mixed = some coarse oracles or surviving probes; weak = mostly trivial or no useful kills; uncertain = evidence missing. Consult requirement-targeted fault evidence, not equality syntax alone. Kill coverage is not exhaustive bug coverage. A null check is appropriate for a null contract; a documented raises contract can be a strong exception oracle.
Q6 Smells: none = no actionable issue; cosmetic = naming/style only, no fix needed; actionable = harmful coupling, misleading tests, hidden bugs or another concrete teaching defect; uncertain = evidence missing. Related assertions are not automatically poor diagnosis; loops/fixtures/tmp_path do not automatically create smells. Explain concrete harm.
Q8 Rationale: yes = concise, follows the request/declared choices and justifies values; too-long = unnecessary narration; reference-leak = relies on undeclared reference internals; unjustified-values = missing/wrong explanation; uncertain = evidence missing.

Q7 decision rule:
APPROVE only when Q1=yes, Q2=yes, Q3=yes or partial-but-disclosed, Q4a=all-correct, Q4b=yes, Q5=strong or mixed WITH targeted kills for every automated core requirement, Q6=none or cosmetic, Q8=yes, no blocking issues, reference tests pass, three different seeded order runs pass and full sequence <=8192 tokens.
REVISE for fixable violations of that rule. REJECT for mismatch or an unusable/contradictory request requiring rewrite. UNCERTAIN only for missing evidence: name exactly what would resolve it in Blocking issues. An explicit API is necessary but does not excuse an unnecessary private helper dependency.

“Review/meta text leaked into input or target” means dataset construction, revision-history or grading commentary appears in model messages. Legitimate application provenance fields and explicitly chosen public API names are not automatic violations. Preservation requirements need failure-state probes as well as success checks.

Fixed defect categories supplement the lab's contextual smell taxonomy; they do not redefine the paper taxonomy. None of the categories is an automatic verdict without a concrete reason.

Free-text formats (one item per line; enter none in Blocking issues when empty):
Missing interface: name or decision -> where used -> proposed declaration.
Missing coverage: R-id -> missing case -> add test | add manual check | explicitly revise scope.
Assertion/smell evidence: file::test -> fixed category -> reason -> requested fix.
Blocking issues: only approval blockers, or the exact missing evidence for uncertain.
Reviewer confidence: high = inspected enough evidence to apply anchors; low = unresolved uncertainty remains.

Calibration examples (illustrations, not actual submitted ratings):
APPROVE: request requires an integer sum, target declares totals.add(a,b), tests check add(2,3)==5 and add(-2,3)==1, targeted off-by-one variant is killed, stable/ref/token checks pass, rationale explains 5 and 1, no manual gap. All applicable answers yes/all-correct/strong/none; Blocking issues=none.
REVISE: request asks for complete processing but tests only a classifier and import an undeclared internal module; a skipped-assertion case is claimed yet absent. Q1=too-broad,Q2=no,Q3=no,Q4a=cannot-verify,Q4b=unexplained,Q5=mixed,Q6=actionable,Q7=revise. Blocking issues name undeclared API, missing processing tests and false coverage claim. This illustrates the old defect, not a rating of the corrected record.

No ratings are prefilled or submitted automatically. Two records will receive a separate AI reviewer audit; it is not independent human agreement. Once two human reviews exist, report their Q7 agreement with numerator/denominator rather than inventing a rate now. Approval is training-target review, not a training command or proof of broad generalization.'''
SMELLS=['Undeclared interface','Tautological assertion','Weak or missing oracle','White-box coupling','Duplicate or redundant case','Poor failure diagnosis','Hidden test logic','Non-determinism','Unexplained expected value','Misleading test name','Unjustified skip, xfail or catch',META_DEFECT]


def main():
    global BUNDLE,NAME
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',choices=['app-core-v03','app-core-v04','app-core-v05'],default='app-core-v03')
    parser.add_argument('--repair-display',action='store_true',help='Repair HTML escaping in place, preserving fields and annotations; save a before snapshot.')
    args=parser.parse_args()
    BUNDLE=BUNDLE.parent/args.revision
    version=args.revision.rsplit('-',1)[-1]
    review_version={'v03':'v02','v04':'v03','v05':'v04'}[version]
    NAME='tdd-nine-apps-human-review-'+review_version
    rows=[json.loads(l) for l in (BUNDLE/'records.jsonl').read_text().splitlines()]
    report=json.loads((BUNDLE/'validation-report.json').read_text())
    assert len(rows)==9 and report['all_reference_pass'] and report['all_within_8192']
    assert report['records_sha256']==sha256((BUNDLE/'records.jsonl').read_bytes()).hexdigest()
    packets=[]
    for row in rows:
        folder=BUNDLE/row['record_id'].removesuffix('-'+version)
        for file in row['validation']['test_files']+row['source']['new_reference_files']:
            assert sha256((folder/file['path']).read_bytes()).hexdigest()==file['sha256'],file['path']
        assert row['validation']['three_order_runs_pass'] and row['validation']['all_core_requirements_have_killed_variant']
        assert row['validation']['faults'] and all(f['killed'] for f in row['validation']['faults'])
        current={str(p.relative_to(folder)):sha256(p.read_bytes()).hexdigest() for p in sorted((folder/'tests').rglob('*.py'))}
        for fault in row['validation']['faults']:assert fault['test_snapshot']==current, 'Fault evidence belongs to a different suite'
        for stable in row['validation']['stability']:
            assert stable['test_snapshot']==current, 'Stability evidence belongs to a different suite'
            for path,digest in stable['reference_snapshot'].items():assert sha256((folder/path).read_bytes()).hexdigest()==digest
        coverage='\n\n'.join(r['id']+': '+r['text']+'\n'+ '\n'.join('- `'+t+'`' for t in r['test_ids'])+('\nManual/live: '+', '.join(r['manual_ids']) if r['manual_ids'] else '') for r in row['requirements'])
        if version in ('v04','v05'):assert row['validation']['model_text_scan']['unresolved']==0
        if version=='v05':
            assert row['validation']['test_numbering_consistent']
            assert all(check['detected'] for check in row['validation']['preservation_checks'])
        source=row['source']
        evidence=f"**Reference suite passed. Full native sequence: {row['tokens']['full_sequence']:,} / 8,192 tokens.**\n\nIncludes system, request, declared constraints, proposed interface, concise rationale, maps, all test files/config and manual checks. No truncation.\n\n**Targeted faults:**\n\n"+'\n'.join('- '+f['fault']+': detected; '+str(len(f['failing_tests']))+' failing test case(s)' for f in row['validation']['faults'])
        evidence+='\n\n**Killed variants by targeted core requirement:**\n\n'+'\n'.join('- '+rid+': '+', '.join(names) for rid,names in row['validation']['fault_coverage_by_core_requirement'].items())
        if row['validation'].get('preservation_checks'):
            evidence+='\n\n**Preservation checks:**\n\n'+'\n'.join('- '+c['requirement_id']+': '+c['contract']+' Detected: '+', '.join(c['faults']) for c in row['validation']['preservation_checks'])
        evidence+='\n\n**Stability:** three different seeded collection orders passed: '+', '.join(str(r['seed']) for r in row['validation']['stability'])+'.\n\nThese are targeted probes, not a comprehensive mutation score.\n\n**Actual pytest log:**\n\n```text\n'+Path(row['validation']['execution_log']).read_text()[-1600:]+'\n```'
        provenance=f"**Source app:** `{source['repo']}` at `{source['revision']}`; dirty checkout at execution: {source['dirty']}.\n\n{source['origin']}\n\n**Proposed split:** {row['split']}; leakage group `{row['leakage_group']}`. Paper overlap: {row['paper_benchmark_overlap']}.\n\n{source['reference_note']}\n\n**New reference files (verification only):**\n\n"+'\n'.join('- `'+str(folder/f['path'])+'` — SHA256 '+f['sha256'] for f in source['new_reference_files'])
        if version=='v04':provenance+='\n\nFormat-only revision: test executable AST and application implementation are unchanged from v03; only model-facing prose and test module descriptions were cleaned. Record-specific executor work is archived separately.'
        if version=='v05':provenance+='\n\nCode is HTML-escaped for this display only. Raw training messages remain unchanged by presentation escaping. Numbered tests match the requirement map; preservation probes include failed-refresh and stale-state cases.'
        provenance+='\n\nOriginal app source remains at `'+str(ROOT.parent/source['repo'])+'`. No original app files were changed for this revision. No human approval or SFT result exists. Exact record and provenance: `'+str(folder/'record.json')+'`.'
        fields=dict(model_input='**System:**\n\n'+row['messages'][0]['content']+'\n\n**User:**\n\n'+row['messages'][1]['content'],
            reasoning=row['teacher_reasoning'],interface=row['decisions']+'\n\n'+row['interface']['text'],
            requirement_map=coverage,tests=render_test_field((folder/'test-output.md').read_text()),
            manual='\n\n'.join(m['id']+': '+m['text'] for m in row['manual_checks']),
            evidence=evidence,provenance=provenance)
        packets.append(dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/'+row['record_id'])),record_id=row['record_id'],fields=fields))
    out=BUNDLE/('human-review-'+review_version)/'presentation-v02';out.mkdir(parents=True,exist_ok=True)
    text=''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in packets)
    packet_path=out/'packets.jsonl'
    if packet_path.exists() and packet_path.read_text()!=text:raise ValueError('Published packet changed; create a new revision. Existing annotations are preserved.')
    env=dict(line.split('=',1) for line in (DOMAIN/'review/.env').read_text().splitlines() if line and not line.startswith('#'))
    client=rg.Argilla(api_url='http://127.0.0.1:7900',api_key=env['ARGILLA_API_KEY'])
    dataset=client.datasets(name=NAME,workspace=env['ARGILLA_WORKSPACE'])
    if dataset is None:
        questions=[rg.LabelQuestion(name=name,title=title,labels=labels,required=True) for name,title,labels in [
            ('source_relevance','Q1. Request/source relevance and scope',['yes','too-broad','too-narrow','mismatch','uncertain']),
            ('interface_quality','Q2. Derivable from input and target agreement (framing B)?',['yes','minor-gaps','no','uncertain']),
            ('coverage','Q3. Important requirements covered adequately?',['yes','partial-but-disclosed','no','uncertain']),
            ('expectation_correctness','Q4a. Are expected outcomes correct?',['all-correct','some-wrong','cannot-verify']),
            ('expectation_justification','Q4b. Are values and choices justified explicitly?',['yes','unexplained','uncertain']),
            ('assertion_quality','Q5. Meaningful fault discrimination? See per-requirement evidence.',['strong','mixed','weak','uncertain']),
            ('smell_quality','Q6. Actionable test smells?',['none','cosmetic','actionable','uncertain']),
            ('approval','Q7. Overall decision — apply guideline rule',['approve','revise','reject','uncertain']),
            ('reasoning_quality','Q8. Concise rationale grounded in request and declared choices?',['yes','too-long','reference-leak','unjustified-values','uncertain']),
            ('confidence','Reviewer confidence',['high','low'])]]
        questions += [rg.MultiLabelQuestion(name='smells',title='Fixed defect categories (optional; explain concrete harm)',labels=SMELLS,required=False),
            rg.TextQuestion(name='missing_interface',title='Missing interface: name/decision -> where used -> declaration',required=False),
            rg.TextQuestion(name='missing_coverage',title='Missing coverage: R-id -> case -> test/manual/scope fix',required=False),
            rg.TextQuestion(name='assertion_evidence',title='file::test -> category -> reason -> fix',required=False),
            rg.TextQuestion(name='blocking_issues',title='Approval blockers only; enter none if empty. For uncertain, name missing evidence.',required=True)]
        fields=[rg.TextField(name=n,title=t,use_markdown=markdown) for n,t,markdown in [
            ('model_input','Exact model input — source is not included',True),
            ('reasoning','Target concise rationale — separately reviewable thinking content',True),
            ('interface','Target decisions and proposed interface — not historical user answers',True),
            ('requirement_map','Target requirement-to-test map — semantic coverage still needs review',True),
            ('tests','Target complete test files and configuration',False),
            ('manual','Target manual/live checks — pending',True),
            ('evidence','Review-only validation and full token count',True),
            ('provenance','Review-only provenance, split and NEW reference-code disclosure',True)]]
        dataset=rg.Dataset(name=NAME,workspace=env['ARGILLA_WORKSPACE'],settings=rg.Settings(guidelines=GUIDELINES,fields=fields,questions=questions),client=client)
        dataset.create()
    live=list(dataset.records(with_responses=True,with_suggestions=True))
    existing={str(r.id) for r in live}
    annotations_before={str(r.id):r.responses.to_dict() for r in live}
    backup=out/'server-before.jsonl'
    if args.repair_display and not backup.exists():
        backup.write_text(''.join(json.dumps(r.to_dict(),ensure_ascii=False,default=str)+'\n' for r in live))
    smells=dataset.settings.questions['smells']
    category_available=META_DEFECT in smells.labels
    # Published option counts cannot change; older views are repaired in place,
    # and a new dataset carries the extended category list.
    expected={p['id']:p for p in packets}
    repaired=[]
    for record in live:
        packet=expected[str(record.id)]
        wanted=packet['fields']['tests']
        if record.fields['tests']==wanted:continue
        raw=(BUNDLE/packet['record_id'].removesuffix('-'+version)/'test-output.md').read_text()
        if not args.repair_display:raise ValueError('Existing code needs presentation repair; rerun with --repair-display.')
        if record.fields['tests']!=raw:raise ValueError('Unexpected server code differs from both raw and escaped source; refusing to overwrite.')
        fields=dict(record.fields);fields['tests']=wanted
        response=client.api.records.http_client.patch('/api/v1/records/'+str(record._model.id),json={'fields':fields})
        response.raise_for_status()
        repaired.append(str(record.id))
    verified=list(dataset.records(with_responses=True,with_suggestions=True))
    assert annotations_before=={str(r.id):r.responses.to_dict() for r in verified}, 'Annotation values changed during display repair'
    assert all(r.fields['tests']==expected[str(r.id)]['fields']['tests'] for r in verified)

    pending=[rg.Record(id=p['id'],fields=p['fields']) for p in packets if p['id'] not in existing]
    if pending:dataset.records.log(pending)
    assert sum(1 for _ in dataset.records(with_responses=False,with_suggestions=False))==9
    packet_path.write_text(text);(out/'GUIDELINES.md').write_text(GUIDELINES+'\n')
    receipt=dict(dataset=NAME,dataset_id=str(dataset.id),records=9,
                 url=f'http://127.0.0.1:7900/dataset/{dataset.id}/annotation-mode',
                 human_ratings_submitted=False,display_only=args.repair_display,code_fields_html_escaped=True,meta_defect_category_available=category_available,annotations_preserved=True,repaired_records=repaired,packet_sha256=sha256(packet_path.read_bytes()).hexdigest())
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
