"""Build/validate authored external tasks. Trusted host fixtures only; no model calls."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from external_task_definitions import TASKS

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'
BUNDLE = EXP / 'external-batch-v02'
SYSTEM = ('Write one complete Python pytest file for the agreed development task before implementation. '
          'Use only the supplied interfaces and requirements. Include deterministic offline fixtures, '
          'successful controls and meaningful boundary/failure assertions. Give concise rationale separately, '
          'then exactly File: <target path> followed by one fenced python file. Do not implement the application.')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')


def jsave(path, value):
    save(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def sources():
    audit = json.loads((EXP / 'external-app-audit.json').read_text(encoding='utf-8'))
    return {s['repository'].split('/')[-1]: s for s in audit['sources']}


def build(repair_task=None):
    existing = {}
    if BUNDLE.exists() and not repair_task:
        raise ValueError('Existing batch: preserve it; use validate for execution.')
    if repair_task:
        existing = {r['task_id']:r for r in map(json.loads, (BUNDLE / 'records.jsonl').read_text(encoding='utf-8').splitlines())}
        if existing[repair_task]['validation']['status'] != 'failed':
            raise ValueError('Repair only an explicitly selected failed draft')
        jsave(BUNDLE / 'repairs' / (repair_task + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')) / 'record-before.json', existing[repair_task])
    lookup = sources()
    rows = []
    for task in TASKS:
        app = task['application']
        source = lookup[app]
        proposal = next(t for t in source['candidate_tasks'] if t['id'] == app + '-' + task['suffix'])
        role = {'train-proposed': 'train', 'development-proposed': 'development', 'holdout-proposed': 'holdout'}[source['proposed_role']]
        target = 'tests/test_' + task['suffix'].replace('-', '_') + '.py'
        app_tasks = [dict(id=t['suffix'], module=t['module'], target_file='tests/test_' + t['suffix'].replace('-', '_') + '.py')
                     for t in TASKS if t['application'] == app]
        prompt = ('APPLICATION\n' + {'litecli': 'Build a SQLite terminal client with query execution, SQL-aware completion and special commands.',
                  'tldr-python-client': 'Build a terminal reference-page client with translated pages, a local cache and offline fallback.',
                  'posting': 'Build a terminal HTTP client with saved requests, URL parameters and editable session variables.',
                  'ddgr': 'Build a terminal search client with safe result URLs, pagination and structured result output.'}[app]
                  + '\n\nAGREED TASK PLAN\n' + json.dumps(app_tasks, indent=2)
                  + '\n\nCURRENT TASK\n' + task['suffix'] + '\nTarget file: ' + target
                  + '\nImplementation module: ' + task['module']
                  + '\n\nINTERFACE AND ACCEPTANCE CONTRACT\n' + task['contract']
                  + '\n\nCONTEXT\nPython 3.13 and pytest. Import the named module through its normal import path. '
                  'No implementation or existing tests are supplied. All fixtures belong in this test file. '
                  'Dependencies are supplied by the environment. Use temporary storage and mock external I/O. '
                  'The task plan lists independent behavioral slices, not completed implementation steps.')
        tree = ast.parse(task['tests'])
        test_names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
        assert test_names and len(test_names) == len(set(test_names))
        row = dict(record_id=app + '-' + task['suffix'] + '-external-v02', task_id=app + '-' + task['suffix'],
                   record_type='task-test', source_group=source['repository'], candidate_split=role,
                   training_eligible=False, target_file=target,
                   messages=[dict(role='system', content=SYSTEM), dict(role='user', content=prompt),
                             dict(role='assistant', reasoning_content=task['rationale'],
                                  content='File: ' + target + '\n```python\n' + task['tests'] + '```\n')],
                   artifact=dict(path=target, content=task['tests']), test_functions=test_names,
                   source=dict(repository=source['repository'], revision=source['revision'],
                               source_file=proposal['source_file'], source_sha256=proposal['source_sha256'],
                               license=source['license'], license_files=source['license_files'],
                               provenance='New assistant-authored requirements, rationale and tests from source behavior; no upstream test bodies copied.'),
                   validation=dict(status='pending', semantic_review='pending'), tokens=None)
        folder = BUNDLE / 'tasks' / row['task_id']
        if existing and row['task_id'] != repair_task:
            prior = existing[row['task_id']]
            assert prior['messages'] == row['messages'] and prior['artifact'] == row['artifact'], 'Unselected row changed'
            rows.append(prior)
            continue
        save(folder / target, task['tests'])
        save(folder / 'prompt.txt', prompt + '\n')
        save(folder / 'rationale.txt', task['rationale'] + '\n')
        jsave(folder / 'faults.json', task['faults'])
        rows.append(row)
    save(BUNDLE / 'records.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    # Preserve the complete license notices beside derived material.
    for app, source in lookup.items():
        for notice in source['license_files']:
            p = Path(source['local_source']) / notice['path']
            assert digest(p) == notice['sha256']
            save(BUNDLE / 'attribution' / app / Path(notice['path']).name, p.read_text(encoding='utf-8'))
    jsave(BUNDLE / 'manifest.json', dict(status='draft', count=len(rows), split_counts={'train': 12, 'development': 5, 'holdout': 3},
          source_roles_frozen=False, training_enabled=False, builder_sha256=digest(Path(__file__)),
          definitions_sha256=digest(Path(__file__).with_name('external_task_definitions.py')),
          provenance='Trusted authored demo data; no model inference or training performed.',
          isolation='Host subprocesses with credential-filtered environment and bounded runtime; not an OS network sandbox.',
          adapters={'litecli': 'Minimal distribution metadata supplies a version string required by __init__; application source is unchanged.',
                    'posting': 'Empty package initializer avoids unrelated UI imports; files.py, save_request.py, urls.py and session_variables.py are unchanged.',
                    'ddgr': 'Unchanged extensionless main script copied as ddgr.py for a stable import path.'}))


PLUGIN = '''import json,random,importlib,pytest
from pathlib import Path
ORDER=[]
REPORTS=[]
def pytest_sessionstart(session):
    config=json.loads(Path('condition.json').read_text(encoding='utf-8'))
    if config['mutation']:
        m=importlib.import_module(config['module'])
        exec(config['mutation'],{'m':m})
def pytest_collection_modifyitems(items):
    config=json.loads(Path('condition.json').read_text(encoding='utf-8'))
    if config['seed'] is not None: random.Random(config['seed']).shuffle(items)
    ORDER.extend(item.nodeid for item in items)
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    report.explicit_assertion=bool(call.excinfo and call.excinfo.errisinstance((AssertionError,pytest.fail.Exception)))
def pytest_runtest_logreport(report):
    REPORTS.append(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,
                       assertion=(report.failed and report.when=='call' and report.explicit_assertion)))
def pytest_sessionfinish(session,exitstatus):
    Path('execution.json').write_text(json.dumps(dict(order=ORDER,reports=REPORTS,exitstatus=exitstatus)),encoding='utf-8')
'''


def prepare_reference(dest, app, source):
    root = Path(source['local_source'])
    for item in source['files']:
        if not item['test']:
            assert digest(root / item['path']) == item['sha256'], 'Changed source: ' + item['path']
    if app == 'litecli':
        shutil.copytree(root / 'litecli', dest / 'litecli')
        save(dest / 'litecli-0.0.0.dist-info/METADATA', 'Metadata-Version: 2.1\nName: litecli\nVersion: 0.0.0\n')
    elif app == 'tldr-python-client':
        shutil.copyfile(root / 'tldr.py', dest / 'tldr.py')
    elif app == 'posting':
        (dest / 'posting').mkdir()
        save(dest / 'posting/__init__.py', '# Reference-only adapter: skip unrelated terminal UI initialization.\n')
        for name in ('urls.py', 'files.py', 'save_request.py', 'session_variables.py'):
            shutil.copyfile(root / 'src/posting' / name, dest / 'posting' / name)
    elif app == 'ddgr':
        shutil.copyfile(root / 'ddgr', dest / 'ddgr.py')
    else:
        raise ValueError(app)


def validate_one(pair):
    task, row = pair
    source = sources()[task['application']]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = BUNDLE / 'evidence' / stamp / row['task_id']
    runs = []
    conditions = [('reference', None, None)] + [('order-' + str(seed), seed, None) for seed in (17, 43, 91)] + [(name, None, fault) for name, fault in task['faults']]
    for name, seed, fault in conditions:
        target = evidence / name
        target.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='external-task-') as temporary:
            work = Path(temporary)
            prepare_reference(work, task['application'], source)
            save(work / row['target_file'], row['artifact']['content'])
            save(work / 'batch_probe.py', PLUGIN)
            jsave(work / 'condition.json', dict(module=task['module'], mutation=fault, seed=seed))
            env = {k:v for k,v in os.environ.items() if not any(word in k.upper() for word in ('TOKEN','SECRET','PASSWORD','API_KEY','CREDENTIAL'))}
            env.update(PYTHONUTF8='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=str(work), TLDR_NETWORK_ENABLED='0')
            for key in ('LANG', 'LANGUAGE', 'TLDR_LANGUAGE', 'TLDR_CERT', 'TLDR_ALLOW_INSECURE'):
                env.pop(key, None)
            try:
                result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'batch_probe', row['target_file']],
                                        cwd=work, env=env, capture_output=True, text=True, encoding='utf-8', timeout=45)
                save(target / 'pytest.log', result.stdout + result.stderr)
                execution = json.loads((work / 'execution.json').read_text(encoding='utf-8')) if (work / 'execution.json').exists() else {}
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                execution, returncode = {}, 124
                save(target / 'pytest.log', 'Runtime limit exceeded: 45 seconds\n')
            jsave(target / 'execution.json', execution)
            jsave(target / 'condition.json', dict(module=task['module'], mutation=fault, seed=seed))
            reports = execution.get('reports', [])
            assertions = sum(bool(r['assertion']) for r in reports)
            cases = len(execution.get('order', []))
            passed = sum(r['when'] == 'call' and r['outcome'] == 'passed' for r in reports)
            invalid = any(r['outcome'] == 'failed' and r['when'] != 'call' for r in reports)
            killed = bool(fault and returncode == 1 and assertions > 0 and not invalid)
            ok = killed if fault else returncode == 0 and cases > 0 and passed == cases
            runs.append(dict(condition=name, seed=seed, returncode=returncode, cases=cases, passed_cases=passed,
                             assertion_failures=assertions, killed=killed if fault else None, ok=ok,
                             evidence=target.relative_to(ROOT).as_posix()))
    row['validation'] = dict(status='passed' if all(r['ok'] for r in runs) else 'failed',
                             semantic_review='pending; execution is not semantic approval', runs=runs,
                             reference_cases=runs[0]['cases'], artifact_sha256=sha256(row['artifact']['content'].encode()).hexdigest())
    print(row['task_id'], row['validation']['status'], flush=True)
    return row


def validate(workers, selected=None):
    rows = [json.loads(line) for line in (BUNDLE / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    pairs = [(task,row) for task,row in zip(TASKS,rows) if selected is None or row['task_id']==selected]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        updated = {r['task_id']:r for r in pool.map(validate_one, pairs)}
    rows = [updated.get(row['task_id'],row) for row in rows]
    save(BUNDLE / 'records.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    summary = dict(rows=len(rows), passed=sum(r['validation']['status'] == 'passed' for r in rows),
                   reference_cases=sum(r['validation'].get('reference_cases',0) for r in rows),
                   faults_detected=sum(run['killed'] is True for r in rows for run in r['validation'].get('runs',[])))
    jsave(BUNDLE / 'validation-report.json', summary)
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, encoding='utf-8', check=True)
    save(BUNDLE / 'environment.txt', sys.version + '\n' + freeze.stdout)
    print(json.dumps(summary))


def export(tokenizer_path):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True, trust_remote_code=False)
    rows = [json.loads(line) for line in (BUNDLE / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in rows:
        result = tokenizer.apply_chat_template(row['messages'], tokenize=True)
        ids = result['input_ids'] if isinstance(result, dict) or hasattr(result, 'keys') else result
        row['tokens'] = dict(full_sequence=len(ids), rationale=len(tokenizer.encode(row['messages'][-1]['reasoning_content'], add_special_tokens=False)),
                             final_answer=len(tokenizer.encode(row['messages'][-1]['content'], add_special_tokens=False)), limit=8192, within_limit=len(ids)<=8192)
        assert row['tokens']['within_limit'], row['task_id']
    save(BUNDLE / 'records.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    parts = []
    for row in rows:
        parts.append(row['record_id'] + '\nSplit: ' + row['candidate_split'] + '\n\n' + row['messages'][1]['content']
                     + '\n\nRATIONALE\n' + row['messages'][-1]['reasoning_content'] + '\n\n' + row['messages'][-1]['content'])
    save(BUNDLE / 'share/twenty-external-task-examples.txt', '\n----\n'.join(parts))
    jsave(BUNDLE / 'token-summary.json', {role: dict(rows=sum(r['candidate_split']==role for r in rows),
          full_sequence_tokens=sum(r['tokens']['full_sequence'] for r in rows if r['candidate_split']==role),
          final_answer_tokens=sum(r['tokens']['final_answer'] for r in rows if r['candidate_split']==role))
          for role in ('train','development','holdout')})
    jsave(BUNDLE / 'integrity.json', {p.relative_to(BUNDLE).as_posix():digest(p) for p in sorted(BUNDLE.rglob('*')) if p.is_file() and p.name!='integrity.json'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['build','validate','export'])
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--tokenizer')
    parser.add_argument('--task')
    args = parser.parse_args()
    if args.command == 'build': build(args.task)
    elif args.command == 'validate': validate(args.workers, args.task)
    else: export(args.tokenizer)
