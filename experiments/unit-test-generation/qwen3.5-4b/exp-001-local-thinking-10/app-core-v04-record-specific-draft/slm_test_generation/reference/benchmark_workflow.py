"""Offline suite orchestration with explicit trusted-local and isolated executors."""
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from oracle_analysis import instrument_oracles, gate_outcomes


def _pytest_report(run_dir, timeout_seconds, env):
    started=time.monotonic()
    try:
        result=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','test_generated.py'],
            cwd=run_dir,env=env,capture_output=True,text=True,timeout=timeout_seconds)
        outcome='passed' if result.returncode==0 else 'collection_error' if result.returncode in (2,4,5) else 'runtime_failure'
        return dict(outcome=outcome,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,
                    pytest_seconds=time.monotonic()-started)
    except subprocess.TimeoutExpired:
        return dict(outcome='timeout',returncode=None,stdout='',stderr='',pytest_seconds=time.monotonic()-started)


class LocalPytestExecutor:
    """Execute explicitly trusted fixture code only. This is not a sandbox."""
    def __call__(self, run_dir, timeout_seconds):
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                 ORACLE_EXECUTION_FILE=str(run_dir/'events.jsonl'))
        env.pop('PYTEST_ADDOPTS',None)
        env.pop('PYTEST_PLUGINS',None)
        return dict(_pytest_report(run_dir,timeout_seconds,env),backend='local-subprocess')


SUPERVISOR = '''import json, os, subprocess, sys, time
started=time.monotonic()
try:
    result=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','test_generated.py'],
        capture_output=True,text=True,timeout=float(os.environ['SUITE_TIMEOUT']))
    outcome='passed' if result.returncode==0 else 'collection_error' if result.returncode in (2,4,5) else 'runtime_failure'
    report={'outcome':outcome,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
except subprocess.TimeoutExpired:
    report={'outcome':'timeout','returncode':None,'stdout':'','stderr':''}
report['pytest_seconds']=time.monotonic()-started
report['python_version']=sys.version.split()[0]
import pytest
report['pytest_version']=pytest.__version__
open('execution.json','w').write(json.dumps(report))
'''


class DockerExecutor:
    def __init__(self, image=None, infrastructure_grace_seconds=15):
        self.image=image or os.environ.get('PYTEST_RUNNER_IMAGE','llm-bender-pytest:integration-v01')
        self.infrastructure_grace_seconds=infrastructure_grace_seconds
    def __call__(self, run_dir, timeout_seconds):
        (run_dir/'supervisor.py').write_text(SUPERVISOR)
        name='suite-'+uuid.uuid4().hex
        command=['docker','run','--rm','--name',name,'--network','none','--read-only',
                 '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64',
                 '--memory','256m','--cpus','1','--tmpfs','/tmp:rw,nosuid,size=32m',
                 '-v',f'{run_dir.resolve()}:/work:rw','-w','/work',
                 '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                 '-e','ORACLE_EXECUTION_FILE=/work/events.jsonl','-e',f'SUITE_TIMEOUT={timeout_seconds}',
                 '--entrypoint','python',self.image,'supervisor.py']
        started=time.monotonic()
        try:
            result=subprocess.run(command,capture_output=True,text=True,
                                  timeout=timeout_seconds+self.infrastructure_grace_seconds)
            if result.returncode:raise RuntimeError('Container runner failed: '+result.stderr)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
            raise RuntimeError('Container infrastructure timeout')
        report=json.loads((run_dir/'execution.json').read_text())
        report.update(backend='docker',executor_seconds=time.monotonic()-started,
                      configured_image=self.image,command=command,
                      timeout_scope='pytest startup, collection and execution; excludes container startup')
        return report


def run_task(task, *, root, sut_source, timeout_seconds, executor=None):
    if timeout_seconds <= 0:raise ValueError('Positive timeout required')
    identifier=task['id']
    if not identifier or Path(identifier).name!=identifier or identifier in ('.','..'):raise ValueError('Invalid task ID')
    run=Path(root)/identifier;run.mkdir(parents=True,exist_ok=False)
    source=task['source'];(run/'generation.txt').write_text(source)
    try:instrumented,sites=instrument_oracles(source,sut_names=task['sut_names'])
    except SyntaxError:instrumented,sites=source,[]
    (run/'test_generated.py').write_text(instrumented)
    (run/'solution.py').write_text(sut_source)
    (run/'conftest.py').write_text('from solution import sut\ndef pytest_collection_modifyitems(items):\n    for item in items: item.module.sut=sut\n')
    execute=executor if executor is not None else DockerExecutor()
    report=execute(run,timeout_seconds)
    path=run/'events.jsonl'
    reached={json.loads(line)['oracle_id'] for line in path.read_text().splitlines()} if path.exists() else set()
    gates=gate_outcomes(report['outcome']=='passed',sites,reached)
    result=dict(report,task_id=identifier,context=task['context'],dependency=task['dependency'],
                useful_success=gates['executed_nontrivial_gate'],reached_oracles=sorted(reached))
    logging.getLogger(__name__).info('execution backend=%s outcome=%s pytest_seconds=%s budget_seconds=%s',
        result['backend'],result['outcome'],result.get('pytest_seconds'),timeout_seconds)
    (run/'result.json').write_text(json.dumps(result,indent=2))
    return result


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
