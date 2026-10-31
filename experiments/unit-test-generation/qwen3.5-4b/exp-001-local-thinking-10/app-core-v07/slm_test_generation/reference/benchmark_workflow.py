"""New fixture reference runner: actual pytest in bounded network-disabled Docker.

Not the paper orchestrator. It only consumes supplied generations and never
imports inference or writes to the source benchmark checkout.
"""
import json
import os
from pathlib import Path
import subprocess
import uuid
from oracle_analysis import instrument_oracles, gate_outcomes

IMAGE = 'llm-bender-pytest:integration-v01'
SUPERVISOR = '''import json, os, subprocess, sys
try:
    result=subprocess.run([sys.executable,'-m','pytest','-q','test_generated.py'],
        capture_output=True,text=True,timeout=float(os.environ['SUITE_TIMEOUT']))
    outcome='passed' if result.returncode==0 else 'collection_error' if result.returncode in (2,4,5) else 'runtime_failure'
    report={'outcome':outcome,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
except subprocess.TimeoutExpired:
    report={'outcome':'timeout','returncode':None,'stdout':'','stderr':''}
open('execution.json','w').write(json.dumps(report))
'''


def run_task(task, *, root, sut_source, timeout_seconds, executor=None):
    if timeout_seconds <= 0: raise ValueError('Positive timeout required')
    identifier=task['id']
    if Path(identifier).name != identifier or identifier in ('.','..'): raise ValueError('Invalid task ID')
    run=Path(root)/identifier; run.mkdir(parents=True,exist_ok=False)
    source=task['source']
    (run/'generation.txt').write_text(source)
    # Collection errors are deliberately preserved as executable pytest input.
    try:
        instrumented,sites=instrument_oracles(source,sut_names=task['sut_names'])
    except SyntaxError:
        instrumented,sites=source,[]
    (run/'test_generated.py').write_text(instrumented)
    (run/'solution.py').write_text(sut_source)
    (run/'conftest.py').write_text('from solution import sut\ndef pytest_collection_modifyitems(items):\n    for item in items: item.module.sut=sut\n')
    (run/'supervisor.py').write_text(SUPERVISOR)
    if executor is not None:
        executor(run, timeout_seconds)
    else:
        name='tdd-fixture-'+uuid.uuid4().hex
        command=['docker','run','--rm','--name',name,'--network','none','--read-only',
                 '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64',
                 '--memory','256m','--cpus','1','--tmpfs','/tmp:rw,nosuid,size=32m',
                 '-v',f'{run.resolve()}:/work:rw','-w','/work',
                 '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                 '-e','ORACLE_EXECUTION_FILE=/work/events.jsonl','-e',f'SUITE_TIMEOUT={timeout_seconds}',
                 '--entrypoint','python',IMAGE,'supervisor.py']
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=timeout_seconds+15)
            if result.returncode: raise RuntimeError('Container runner failed: '+result.stderr)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
            raise RuntimeError('Container infrastructure timeout')
    report=json.loads((run/'execution.json').read_text())
    path=run/'events.jsonl'
    reached={json.loads(line)['oracle_id'] for line in path.read_text().splitlines()} if path.exists() else set()
    gates=gate_outcomes(report['outcome']=='passed',sites,reached)
    return dict(report,task_id=identifier,context=task['context'],dependency=task['dependency'],
                useful_success=gates['executed_nontrivial_gate'],reached_oracles=sorted(reached))


def summarize(*, eligible_ids, observations):
    eligible=set(eligible_ids)
    if len(eligible)!=len(eligible_ids): raise ValueError('Duplicate eligible ID')
    by_id={row['task_id']:row for row in observations}
    if len(by_id)!=len(observations) or not by_id.keys()<=eligible: raise ValueError('Unknown/duplicate task')
    successes=sum(row['useful_success'] is True for row in observations)
    return dict(eligible=len(eligible),observed=len(by_id),missing=len(eligible)-len(by_id),
                successful=successes,success_rate=successes/len(eligible) if eligible else None)


def mutation_summary(*, eligible, valid, killed):
    if not 0<=killed<=valid<=eligible: raise ValueError('Invalid mutation counts')
    return dict(unconditional=killed/eligible if eligible else None,
                conditional=killed/valid if valid else None,eligible=eligible,valid=valid,killed=killed)


def save_manifest(path, manifest):
    Path(path).write_text(json.dumps(manifest,indent=2))


def load_manifest(path):
    return json.loads(Path(path).read_text())
