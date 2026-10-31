"""Build and validate trusted task-to-test demonstrations; never launches training."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
EXPERIMENT=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'
PARENT=EXPERIMENT.parent/'exp-001-local-thinking-10/app-core-v07'
SPECFILE=EXPERIMENT/'pilot-spec.json'
BUNDLE=EXPERIMENT/'pilot-v01'
SYSTEM=('Write one complete Python pytest file for the current development task before its implementation. '
        'Use the application goal, explicit plan, interface contract and supplied context. '
        'Cover meaningful successful and failing behavior with deterministic offline fixtures. '
        'Do not implement application code or change the contract to make tests pass. '
        'Give concise rationale separately, then return exactly File: <target path> followed by one fenced python file. '
        'Respect the target path; do not generate the rest of the repository.')


def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return sha256(path.read_bytes()).hexdigest()
def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')
def save_json(path,obj):save(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def load_rows(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def save_rows(path,rows):save(path,''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))


def extract_tests(source,names,helpers=()):
    """Keep complete selected definitions/decorators and their required top-level imports."""
    tree=ast.parse(source);wanted=set(names)|set(helpers)
    definitions={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    while True:
        called={node.func.id for name in wanted if name in definitions for node in ast.walk(definitions[name]) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}
        fixtures={arg.arg for name in wanted if name in definitions for arg in definitions[name].args.args}
        dependencies={name for name in called|fixtures if name in definitions and not name.startswith('test_')}
        if dependencies<=wanted:break
        wanted|=dependencies
    selected=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in wanted]
    if len(selected)!=len(wanted) or {node.name for node in selected}!=wanted:raise ValueError('Missing or duplicate selected function')
    used={node.id for definition in selected for node in ast.walk(definition) if isinstance(node,ast.Name)}
    imports=[]
    for node in tree.body:
        if isinstance(node,ast.Import):
            aliases=[alias for alias in node.names if (alias.asname or alias.name.split('.')[0]) in used]
        elif isinstance(node,ast.ImportFrom):
            aliases=[alias for alias in node.names if (alias.asname or alias.name) in used]
        else:continue
        if aliases:
            copied=ast.Import(names=aliases) if isinstance(node,ast.Import) else ast.ImportFrom(module=node.module,names=aliases,level=node.level)
            imports.append(ast.unparse(copied))
    lines=source.splitlines()
    definitions=[]
    for node in selected:
        start=min([node.lineno]+[item.lineno for item in node.decorator_list])-1
        definitions.append('\n'.join(lines[start:node.end_lineno]))
    return '\n'.join(imports)+'\n\n\n'+'\n\n\n'.join(definitions)+'\n'


def validate_record(row):
    path=PurePosixPath(row['target_file'])
    if path.is_absolute() or '..' in path.parts or '\\' in str(path) or ':' in str(path) or not str(path).startswith('tests/') or path.suffix!='.py':
        raise ValueError('Unsafe or invalid target test path')
    if row['candidate_split']!='train' or row['source']['parent_split']!='train':
        raise ValueError('Pilot may only derive from existing training families')
    if [item['role'] for item in row['messages']]!=['system','user','assistant']:
        raise ValueError('Wrong conversation roles')
    expected='File: '+row['target_file']+'\n```python\n'+row['artifact']['content']+'```\n'
    if row['messages'][2]['content']!=expected:raise ValueError('Target/artifact mismatch')
    tests=[node.name for node in ast.parse(row['artifact']['content']).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_')]
    if not tests or tests!=row['test_functions']:raise ValueError('Test inventory mismatch')


def build(args):
    spec=read_json(SPECFILE);bundle=BUNDLE
    version=spec.get('pilot_version','v01')
    existing={}
    if (bundle/'records.jsonl').exists():
        if not args.repair_task:raise ValueError('Pilot already built; create a new revision rather than overwrite records')
        existing={row['task_id']:row for row in load_rows(bundle/'records.jsonl')}
        if args.repair_task not in existing or existing[args.repair_task]['validation']['status']!='failed':
            raise ValueError('Only an explicitly selected failed draft may be repaired')
        prior=existing[args.repair_task]
        repair=bundle/'repairs'/args.repair_task/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        save_json(repair/'record-before.json',prior);save(repair/'test-before.txt',prior['artifact']['content'])
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True,trust_remote_code=False)
    parents={row['record_id'].removesuffix('-v07'):row for row in load_rows(PARENT/'records.jsonl')}
    plans=[];records=[]
    for app in spec['applications']:
        parent=parents[app['id']]
        if parent['split']!='train':raise ValueError('Cannot turn held-out applications into training data')
        tasks=[task for task in spec['tasks'] if task['application']==app['id']]
        plan=dict(application=app['id'],goal=parent['messages'][1]['content'],tasks=[{key:task[key] for key in ['id','title','depends_on','implementation_files','target_file','acceptance']} for task in tasks]+app.get('delivery_tasks',[]),
                  unresolved=app['unresolved'],context_policy='Interfaces are agreed; implementations may not exist yet. No completion or tool execution is implied.')
        save_json(bundle/'plans'/(app['id']+'.json'),plan)
        plans.append(dict(record_id=app['id']+'-plan-'+version,record_type='planning-context',training_eligible=False,
                          source_group=parent['leakage_group'],messages=[dict(role='system',content='Plan the requested application into behavioral tasks. Make dependencies, public contracts, acceptance criteria and expected files explicit. Leave nonessential choices open.'),
                          dict(role='user',content=plan['goal']),dict(role='assistant',content=json.dumps(plan,ensure_ascii=False,indent=2))],
                          authorship='Assistant-authored plan, not a historical user interaction or a trained planner result.'))
        for task in tasks:
            folder=bundle/'tasks'/task['id'];fragments=[];provenance=[]
            for selection in task['selections']:
                source=PARENT/app['id']/selection['path']
                fragments.append(extract_tests(source.read_text(encoding='utf-8'),selection['tests'],selection.get('helpers',[])))
                provenance.append(dict(path=source.relative_to(ROOT).as_posix(),sha256=digest(source),functions=selection['tests']))
            if task.get('additional_tests'):fragments.append(task['additional_tests'])
            content='\n\n'.join(fragments).rstrip()+'\n'
            ast.parse(content)
            user=('APPLICATION REQUEST\n'+plan['goal']+'\n\nAGREED PLAN\n'+json.dumps(plan['tasks'],ensure_ascii=False,indent=2)+
                  '\n\nCURRENT TASK\n'+task['title']+'\nTarget test file: '+task['target_file']+
                  '\nExpected implementation files: '+', '.join(task['implementation_files'])+
                  '\n\nINTERFACE CONTRACT\n'+task['contract']+'\n\nACCEPTANCE CRITERIA\n'+
                  '\n'.join('- '+criterion for criterion in task['acceptance'])+
                  '\n\nAVAILABLE CONTEXT\n'+task['context']+
                  '\nNo application implementation or existing solution tests are supplied. Write the selected test file only.')
            messages=[dict(role='system',content=SYSTEM),dict(role='user',content=user),
                      dict(role='assistant',reasoning_content=task['rationale'],content='File: '+task['target_file']+'\n```python\n'+content+'```\n')]
            rendered=tokenizer.apply_chat_template(messages,tokenize=False,enable_thinking=True,add_generation_prompt=False)
            encoded=tokenizer.apply_chat_template(messages,tokenize=True,enable_thinking=True,add_generation_prompt=False)
            if hasattr(encoded,'keys'):encoded=encoded['input_ids']
            assert len(encoded)==len(tokenizer.encode(rendered,add_special_tokens=False))
            assert '<think>\n'+task['rationale'] in rendered and '</think>' in rendered
            row=dict(record_id=task['id']+'-'+version,record_type='task-to-tests',application=app['id'],task_id=task['id'],target_file=task['target_file'],
                     implementation_files=task['implementation_files'],source_group=parent['leakage_group'],candidate_split='train',
                     split_status='Existing train-family pilot used to develop format; never eligible as a new independent holdout.',
                     training_eligible=False,messages=messages,artifact=dict(path=task['target_file'],content=content),
                     test_functions=[node.name for node in ast.parse(content).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_')],
                     diversity=task['diversity'],acceptance_criteria=task['acceptance'],
                     source=dict(parent_record_id=parent['record_id'],parent_record_sha256=sha256(json.dumps(parent,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                                 parent_split=parent['split'],repository=parent['source']['repo'],revision=parent['source']['revision'],selected_test_sources=provenance,
                                 authored_additions=bool(task.get('additional_tests')),provenance='Reframed authored v07 demonstrations; not original issue reports, fresh model generations or independent source tasks.'),
                     tokens=dict(full_sequence=len(encoded),supervised_reasoning=len(tokenizer.encode(task['rationale'],add_special_tokens=False)),
                                 final_answer=len(tokenizer.encode(messages[2]['content'],add_special_tokens=False)),limit=8192,within_limit=len(encoded)<=8192,
                                 tokenizer_sha256=digest(Path(args.tokenizer)/'tokenizer.json'),chat_template_sha256=digest(Path(args.tokenizer)/'chat_template.jinja')),
                     validation=dict(status='pending',semantic_review='pending; v07 ratings do not transfer to this new task framing'))
            validate_record(row)
            if not row['tokens']['within_limit']:raise ValueError('No truncation allowed: '+row['record_id'])
            if existing and task['id']!=args.repair_task:
                prior=existing[task['id']]
                if row['messages']!=prior['messages'] or row['artifact']!=prior['artifact']:
                    raise ValueError('Repair would change a different task: '+task['id'])
                row=prior
            save(folder/task['target_file'],content)
            save(folder/'prompt.txt',SYSTEM+'\n\n'+user+'\n')
            save(folder/'rationale.txt',task['rationale']+'\n')
            records.append(row)
    save_rows(bundle/'planning-contexts.jsonl',plans);save_rows(bundle/'records.jsonl',records)
    summary=dict(records=len(records),independent_source_groups=len(plans),planning_examples=len(plans),planning_in_sft=False,
                 train_target=100,train_tasks_still_needed=max(0,100-len(records)),all_within_8192=True,
                 total_tokens=sum(row['tokens']['full_sequence'] for row in records),maximum_tokens=max(row['tokens']['full_sequence'] for row in records),
                 status='format-pilot; validation pending',training_started=False,model_baseline_started=False,
                 spec_sha256=digest(SPECFILE),records_sha256=digest(bundle/'records.jsonl'))
    save_json(bundle/'manifest.json',summary);print(json.dumps(summary,indent=2))


def validate(args):
    bundle=BUNDLE;rows=load_rows(bundle/'records.jsonl')
    if read_json(bundle/'manifest.json')['spec_sha256']!=digest(SPECFILE):
        raise ValueError('Pilot spec changed after build; create a new revision')
    spec=read_json(SPECFILE);tasks={task['id']:task for task in spec['tasks']}
    source_manifest=read_json(PARENT/'source-snapshots.json')
    for name in {row['source']['repository'] for row in rows}:
        source=Path(args.source_root)/name
        for path,expected in source_manifest[name]['python_source_files'].items():
            if digest(source/path)!=expected:raise ValueError('Pinned source changed: '+name+'/'+path)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=bundle/'evidence'/stamp;reports=[]
    def run_row(row):
        validate_record(row);task=tasks[row['task_id']];folder=bundle/'tasks'/row['task_id'];file=folder/row['target_file']
        if file.read_text(encoding='utf-8')!=row['artifact']['content']:raise ValueError('Saved artifact changed')
        references=PARENT/row['application']/'reference';source=Path(args.source_root)/row['source']['repository']
        paths=[references,source,source/'src']
        env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,paths)),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        for key in list(env):
            if any(term in key.upper() for term in ('TOKEN','API_KEY','PASSWORD','SECRET')):env.pop(key)
        env.pop('PYTEST_ADDOPTS',None)
        observed=[]
        for label,seed,mutation in [('reference',None,None)]+[('order-'+str(seed),seed,None) for seed in (17,43,91)]+[(fault['id'],None,fault['code']) for fault in task['faults']]:
            target=output/row['task_id']/label;target.mkdir(parents=True)
            capture=target/'events.json'
            plugin=('import json,random\nfrom pathlib import Path\nEVENTS={"collected":[],"calls":[],"failures":[]}\n'
                    'def pytest_configure(config):\n'+(''.join('    '+line+'\n' for line in mutation.splitlines()) if mutation else '    pass\n')+
                    'def pytest_collection_modifyitems(items):\n'+('    random.Random('+str(seed)+').shuffle(items)\n' if seed is not None else '')+
                    '    EVENTS["collected"]=[item.nodeid for item in items]\n'
                    'def pytest_runtest_logreport(report):\n'
                    '    if report.when=="call":EVENTS["calls"].append(report.nodeid)\n'
                    '    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})\n'
                    'def pytest_sessionfinish(session,exitstatus):\n    Path('+repr(str(capture))+').write_text(json.dumps(EVENTS),encoding="utf-8")\n')
            save(target/'pilot_probe.py',plugin)
            case_env=dict(env,PYTHONPATH=os.pathsep.join([str(target)]+list(map(str,paths))))
            command=[args.python,'-m','pytest','-q','-p','pilot_probe',str(file)]
            result=subprocess.run(command,cwd=folder,env=case_env,capture_output=True,text=True,encoding='utf-8',timeout=45)
            save(target/'pytest.log',result.stdout+result.stderr)
            events=read_json(capture) if capture.exists() else dict(collected=[],calls=[],failures=[])
            killed=mutation is not None and result.returncode==1 and any(failure['when']=='call' and ('AssertionError' in failure['detail'] or 'Failed:' in failure['detail']) for failure in events['failures'])
            observed.append(dict(condition=label,seed=seed,returncode=result.returncode,cases=len(events['collected']),order=events['collected'],
                                 called_cases=len(events['calls']),killed=killed if mutation is not None else None,
                                 log=(target/'pytest.log').relative_to(ROOT).as_posix(),mutation_source=(target/'pilot_probe.py').relative_to(ROOT).as_posix() if mutation else None))
            print(row['task_id'],label,('KILLED' if killed else 'FAILED') if mutation else ('PASS' if result.returncode==0 else 'FAIL'),flush=True)
        passing=[entry for entry in observed if entry['seed'] is not None]
        reference=observed[0]
        valid=reference['returncode']==0 and reference['cases']>0 and reference['called_cases']==reference['cases'] and all(entry['returncode']==0 and set(entry['order'])==set(reference['order']) for entry in passing) and all(entry['killed'] for entry in observed if entry['killed'] is not None)
        row['validation']=dict(status='passed' if valid else 'failed',reference_cases=reference['cases'],runs=observed,
                               artifact_sha256=digest(file),spec_sha256=digest(SPECFILE),
                               source_snapshot_sha256=source_manifest[row['source']['repository']]['snapshot_sha256'],
                               reference_snapshot={p.relative_to(references).as_posix():digest(p) for p in references.rglob('*.py')},
                               semantic_review='pending; executable checks are not semantic approval',
                               execution_scope='Trusted authored pytest fixtures on host with stripped credentials and bounded subprocess time. External I/O mocked; no claim of OS network isolation.')
        return dict(record_id=row['record_id'],passed=valid,reference_cases=reference['cases'],faults=sum(entry['killed'] is True for entry in observed))
    selected=[row for row in rows if args.task is None or row['task_id']==args.task]
    if not selected:raise ValueError('Unknown selected task')
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_row,selected))
    reports=[dict(record_id=row['record_id'],passed=row['validation']['status']=='passed',
                  reference_cases=row['validation'].get('reference_cases',0),
                  faults=sum(run['killed'] is True for run in row['validation'].get('runs',[]))) for row in rows]
    save_rows(bundle/'records.jsonl',rows)
    summary=dict(reports=reports,all_passed=all(row['passed'] for row in reports),reference_cases=sum(row['reference_cases'] for row in reports),
                 faults_detected=sum(row['faults'] for row in reports),training_started=False,baseline_inference_started=False)
    save_json(output/'summary.json',summary);save_json(bundle/'validation-report.json',summary)
    manifest=read_json(bundle/'manifest.json');manifest.update(status=('validated-format-pilot; semantic review and expansion pending' if summary['all_passed'] else 'validation-failed'),records_sha256=digest(bundle/'records.jsonl'))
    save_json(bundle/'manifest.json',manifest);print(json.dumps(summary,indent=2))
    if not summary['all_passed']:raise SystemExit(1)


def export(args):
    bundle=BUNDLE;rows=load_rows(bundle/'records.jsonl');blocks=[]
    for row in rows:
        validate_record(row)
        blocks.append(row['record_id']+'\n\nMODEL INPUT\n\nSYSTEM:\n'+row['messages'][0]['content']+'\n\nUSER:\n'+row['messages'][1]['content']+
                      '\n\nAUTHORED RATIONALE:\n'+row['messages'][2]['reasoning_content']+'\n\nTARGET OUTPUT:\n'+row['messages'][2]['content']+
                      '\nREVIEW-ONLY METADATA\nSource group: '+row['source_group']+'; role: train candidate, not new holdout.\nFull native tokens: '+str(row['tokens']['full_sequence'])+
                      '\nValidation: '+row['validation']['status']+'\n')
    save(bundle/('share/task-test-'+bundle.name+'.txt'),str(len(rows))+' task-level teaching candidates from '+str(len({row['source_group'] for row in rows}))+' existing training families. Planning is input context, not an SFT target. No baseline model outputs or actual planning/tool trajectories are claimed.\n\n'+'\n----\n\n'.join(blocks))
    print(bundle/('share/task-test-'+bundle.name+'.txt'))


def main():
    global SPECFILE,BUNDLE
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    build_parser=commands.add_parser('build');build_parser.add_argument('--tokenizer',required=True);build_parser.add_argument('--repair-task')
    validate_parser=commands.add_parser('validate');validate_parser.add_argument('--python',default=sys.executable);validate_parser.add_argument('--source-root',required=True);validate_parser.add_argument('--workers',type=int,choices=range(1,5),default=2);validate_parser.add_argument('--task')
    export_parser=commands.add_parser('export')
    for subparser in (build_parser,validate_parser,export_parser):
        subparser.add_argument('--spec',default='pilot-spec.json')
        subparser.add_argument('--bundle',default='pilot-v01')
    args=parser.parse_args()
    SPECFILE=EXPERIMENT/args.spec;BUNDLE=EXPERIMENT/args.bundle
    if not SPECFILE.resolve().is_relative_to(EXPERIMENT.resolve()) or not BUNDLE.resolve().is_relative_to(EXPERIMENT.resolve()):
        raise ValueError('Spec and bundle must remain inside the experiment')
    {'build':build,'validate':validate,'export':export}[args.command](args)


if __name__=='__main__':main()
