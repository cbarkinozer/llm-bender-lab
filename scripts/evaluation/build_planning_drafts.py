"""Transform agreed task inventories into separate, unapproved planning drafts."""
import json
from pathlib import Path
from hashlib import sha256
import sys

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'
sys.path.insert(0, str(Path(__file__).parent))
from external_task_definitions import TASKS


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def main():
    output = EXP / 'planning-pilot-v02'
    if output.exists():
        raise ValueError('Preserve existing planning drafts; create a new revision')
    existing = load_rows(EXP / 'pilot-v02/records.jsonl')
    external = load_rows(EXP / 'external-batch-v02/records.jsonl')
    proposals = []
    for path in sorted((EXP / 'pilot-v02/plans').glob('*.json')):
        plan = json.loads(path.read_text(encoding='utf-8'))
        app = plan['application']
        matching = [r for r in existing if r['task_id'] in {t['id'] for t in plan['tasks']}]
        tasks = []
        for task in plan['tasks']:
            row = next((r for r in matching if r['task_id'] == task['id']), None)
            contract = row['messages'][1]['content'].split('INTERFACE CONTRACT\n', 1)[1].split('\n\nACCEPTANCE CRITERIA', 1)[0] if row else None
            tasks.append(dict(id=task['id'], purpose=task['title'], depends_on=task['depends_on'],
                              implementation_files=task['implementation_files'], test_file=task['target_file'],
                              interface_contract=contract, acceptance_criteria=task['acceptance'],
                              verification='offline pytest reference and fault checks' if row else 'delivery/integration verification; specify runnable contract first',
                              child_prompt=('Write ' + task['target_file'] + ' for: ' + task['title'] + '\n'
                                            + (contract or 'Clarify integration interfaces before implementing automated tests.')
                                            + '\nAcceptance:\n' + '\n'.join('- ' + c for c in task['acceptance'])),
                              status='planned; no execution claimed'))
        proposals.append(dict(id=app+'-app-plan', family=matching[0]['source_group'], split='train',
                              request=plan['goal'], tasks=tasks, open_questions=plan['unresolved'],
                              source_artifacts=[str(path.relative_to(ROOT))]))
    for app in dict.fromkeys(t['application'] for t in TASKS):
        matched = [r for r in external if r['source']['repository'].split('/')[-1] == app]
        goal = matched[0]['messages'][1]['content'].split('APPLICATION\n')[1].split('\n\nAGREED TASK PLAN')[0]
        tasks = []
        for task, row in [(t, next(r for r in matched if r['task_id'] == app+'-'+t['suffix'])) for t in TASKS if t['application']==app]:
            tasks.append(dict(id=row['task_id'], purpose=task['suffix'].replace('-', ' '), depends_on=[],
                              implementation_files=[row['source']['source_file']], test_file=row['target_file'],
                              interface_contract=task['contract'], acceptance_criteria=[task['contract']],
                              verification='offline pytest reference, targeted faults and order stability',
                              child_prompt='Write '+row['target_file']+' using '+task['module']+'.\n'+task['contract']
                                           +'\nDefine all fixtures locally; mock I/O; include positive and negative controls.',
                              status='planned; no execution claimed'))
        request = (goal + ' For this milestone plan only these backend behaviors: '
                   + '; '.join(t['purpose'] for t in tasks) + '. Keep full terminal UI and packaging as follow-up work. '
                   'Make the file-level test tasks self-contained and identify unresolved choices.')
        proposals.append(dict(id=app+'-backend-plan', family=matched[0]['source_group'], split=matched[0]['candidate_split'],
                              request=request, tasks=tasks, open_questions=['Terminal UI, installation and full end-to-end integration are follow-up scope.'],
                              source_artifacts=['external-batch-v02/records.jsonl']))
    # Four scoped requests share source groups with their parent; they are not independent repos.
    variants = [('litecli-backend-plan', 'sql-core', ['sql-table-identifiers','sql-destructive-detection','sqlite-query-execution']),
                ('tldr-python-client-backend-plan', 'offline-cache', ['cache-path-selection','cache-freshness','cache-network-routing']),
                ('repo-context-app-plan', 'snapshot-core', ['snapshot-file-tree','snapshot-dependencies','snapshot-text-decoding']),
                ('ghost-box-app-plan', 'first-memory-milestone', None)]
    for parent_id, suffix, selectors in variants:
        parent = next(p for p in proposals if p['id']==parent_id)
        tasks = [t for t in parent['tasks'] if selectors is None or any(t['id'].endswith(s) for s in selectors)]
        if selectors is None:
            tasks = tasks[:3]
        ids = {t['id'] for t in tasks}
        tasks = [dict(t, depends_on=[d for d in t['depends_on'] if d in ids]) for t in tasks]
        proposals.append(dict(id=parent_id+'-'+suffix, family=parent['family'], split=parent['split'], tasks=tasks,
                              request='Plan a focused first milestone for this application: '+parent['request']
                                      +' Limit this milestone to: '+'; '.join(t['purpose'] for t in tasks)
                                      +'. List the rest as deferred scope. Give self-contained test tasks before implementation tasks.',
                              open_questions=['Broader parent application scope is deferred; these tasks do not complete the whole app.'],
                              source_artifacts=parent['source_artifacts'], variant_of=parent_id))
    rows = []
    dispatched = []
    for proposal in proposals:
        ids = {t['id'] for t in proposal['tasks']}
        assert len(ids)==len(proposal['tasks'])
        done = set()
        for _ in range(len(ids)+1):
            done |= {t['id'] for t in proposal['tasks'] if set(t['depends_on']) <= done}
        assert done==ids, 'Unresolved dependency or cycle'
        shared_contracts = {}
        compact_tasks = []
        for task in proposal['tasks']:
            compact = dict(task)
            contract = compact.pop('interface_contract')
            if contract:
                ref = 'contract-' + sha256(contract.encode()).hexdigest()[:12]
                shared_contracts[ref] = contract
                compact['required_contract'] = ref
                compact['child_prompt'] = compact['child_prompt'].replace(contract, 'Use the required contract attached by the orchestrator.')
            else:
                compact['required_contract'] = None
            compact_tasks.append(compact)
            dispatched.append(dict(plan_id=proposal['id'], source_group=proposal['family'], split=proposal['split'],
                                   task_id=task['id'], prompt=task['child_prompt'], training_eligible=False,
                                   purpose='Materialized child input for sufficiency review; not a separate SFT target.'))
        result = dict(intent=proposal['request'], shared_contracts=shared_contracts,
                      dispatch_policy='Attach the full shared_contracts[required_contract] text to each child prompt before dispatch. '
                      'The child receives its own prompt and contract, not just a reference ID.',
                      task_order_policy='Tasks are test specifications first, then implementations. '
                      'Dependencies must be satisfied before a dependent task. Tasks editing a shared file execute sequentially; '
                      'independent files may run concurrently after shared interfaces are agreed.',
                      tasks=compact_tasks, open_questions_and_deferred_scope=proposal['open_questions'],
                      delivery_gate='Run reference checks, fault probes and integration checks before claiming the application is complete.')
        rows.append(dict(record_id=proposal['id']+'-planning-v02', record_type='app-to-task-plan',
                         source_group=proposal['family'], candidate_split=proposal['split'], training_eligible=False,
                         variant_of=proposal.get('variant_of'), source_artifacts=proposal['source_artifacts'],
                         authorship='Assistant-authored transformation of agreed task inventories; no independent planner model execution.',
                         messages=[dict(role='system', content='Turn the application request into an explicit test-first development plan. '
                                        'Return JSON with intent, task ordering, file ownership, public interfaces, acceptance criteria, '
                                        'self-contained child prompts and unresolved/deferred scope. Do not claim code has run.'),
                                   dict(role='user',content=proposal['request']),
                                   dict(role='assistant', content=json.dumps(result,ensure_ascii=False,indent=2))],
                         validation=dict(structural_checks='passed: unique IDs, dependency closure and acyclicity',
                                         requirement_coverage='pending', child_prompt_sufficiency='pending',
                                         independent_planner_quality='not measured', native_label_audit='pending')))
    output.mkdir()
    (output/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8',newline='\n')
    (output/'materialized-child-inputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in dispatched),encoding='utf-8',newline='\n')
    share='\n----\n'.join(r['record_id']+'\nSplit: '+r['candidate_split']+'\n\nREQUEST\n'+r['messages'][1]['content']+'\n\nPLAN\n'+r['messages'][2]['content'] for r in rows)
    (output/'fifteen-planning-drafts.txt').write_text(share+'\n',encoding='utf-8',newline='\n')
    (output/'manifest.json').write_text(json.dumps(dict(rows=len(rows),unique_source_families=len({r['source_group'] for r in rows}),
        split_counts={role:sum(r['candidate_split']==role for r in rows) for role in ('train','development','holdout')},
        status='separate unapproved planning drafts; excluded from test-only dataset',
        builder_sha256=sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Created',len(rows),'planning drafts; none training eligible.')


if __name__=='__main__':
    main()
