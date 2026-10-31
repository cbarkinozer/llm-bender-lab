"""Posting development suites: correct-reference and fault checks in Docker only."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from active_tdd_data import EXP, rows, read_json
from prepare_tdd_demo import save, digest
from review_tdd_demo_outputs import extract_test
from external_task_definitions import TASKS

PLUGIN='''import json,importlib,pytest
from pathlib import Path
REPORTS=[]
ORDER=[]
def pytest_sessionstart(session):
    condition=json.loads(Path('/workspace/condition.json').read_text())
    if condition['mutation']:
        m=importlib.import_module(condition['module'])
        exec(condition['mutation'],{'m':m})
def pytest_collection_modifyitems(items):
    ORDER.extend(i.nodeid for i in items)
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    result=yield
    report=result.get_result()
    report.explicit_assertion=bool(call.excinfo and call.excinfo.errisinstance((AssertionError,pytest.fail.Exception)))
def pytest_runtest_logreport(report):
    REPORTS.append(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,
                        assertion=bool(getattr(report,'explicit_assertion',False))))
def pytest_sessionfinish(session,exitstatus):
    print('\\nTDD_EXECUTION_JSON='+json.dumps(dict(order=ORDER,reports=REPORTS,exitstatus=int(exitstatus))))
'''


def classify(reference, mutant=None):
    reports=reference.get('reports',[]);order=reference.get('order',[])
    passed=[r for r in reports if r['when']=='call' and r['outcome']=='passed']
    valid=reference.get('returncode')==0 and bool(order) and len(passed)==len(order) and not any(r['outcome'] in ('failed','skipped') for r in reports)
    if mutant is None:return valid
    checks=mutant.get('reports',[])
    return bool(valid and mutant.get('returncode')==1 and mutant.get('order')==order
                and any(r['when']=='call' and r['outcome']=='failed' and r.get('assertion') for r in checks)
                and not any(r['outcome']=='failed' and (r['when']!='call' or not r.get('assertion')) for r in checks)
                and not any(r['outcome']=='skipped' for r in checks))


def execute(work, image, log_path):
    name='tdd-demo-'+uuid.uuid4().hex
    cmd=['docker','run','--name',name,'--rm','--network','none','--read-only','--cap-drop','ALL',
         '--security-opt','no-new-privileges','--pids-limit','64','--memory','512m','--cpus','1',
         '--user','65534:65534','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
         '--mount',f'type=bind,src={work.resolve()},dst=/workspace,readonly','--workdir','/workspace',
         '--env','PYTHONPATH=/workspace','--env','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','--env','PYTHONDONTWRITEBYTECODE=1',
         image,'python','-m','pytest','-q','-p','controlled_probe','-p','no:cacheprovider','--basetemp=/tmp/pytest',
         '--override-ini','addopts=','test_generated.py']
    try:
        with log_path.open('wb') as stream:
            result=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=30)
        # Preserve the full log on disk; refuse credit when output exceeds analysis cap.
        if log_path.stat().st_size>262144:return dict(returncode=result.returncode,error='excessive_output',command=cmd)
        text=log_path.read_text(encoding='utf-8',errors='replace')
        markers=[line.split('TDD_EXECUTION_JSON=',1)[1] for line in text.splitlines() if line.startswith('TDD_EXECUTION_JSON=')]
        if len(markers)!=1:return dict(returncode=result.returncode,error='missing_or_ambiguous_execution_report',command=cmd)
        evidence=json.loads(markers[0]);evidence.update(returncode=result.returncode,command=cmd)
        return evidence
    except subprocess.TimeoutExpired:
        return dict(returncode=None,error='timeout',command=cmd)
    finally:
        subprocess.run(['docker','rm','--force',name],capture_output=True,timeout=15)


def grade(outputs, output, image):
    if output.exists():raise ValueError('Preserve prior execution')
    image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
    if not image_id.startswith('sha256:'):raise ValueError('Require resolved Docker image identity')
    output.mkdir(parents=True)
    expected={r['record_id'] for r in rows(EXP/'demo-preflight-v02/development-requests.jsonl') if r['capability']=='task-to-tests'}
    selected=[r for r in rows(outputs) if r['record_id'] in expected]
    if len(selected)!=5 or {r['record_id'] for r in selected}!=expected:raise ValueError('Expected exactly five development test outputs')
    tasks={f"posting-{t['suffix']}-external-v02":t for t in TASKS if t['application']=='posting'}
    grades=[]
    with tempfile.TemporaryDirectory(prefix='tdd-protected-') as temporary:
        root=Path(temporary)
        # Resolve self-contained source package; no dependence on original machine paths.
        with zipfile.ZipFile(EXP/'portable-share/intent-tdd-v03.zip') as z:z.extractall(root/'package')
        package=root/'package/intent-tdd-v03'
        source=next(s for s in read_json(package/'audit/sources.json') if s['source_group']=='darrenburns/posting')
        original=package/source['directory']/'src/posting'
        package_manifest=read_json(package/'manifest.json')['sha256']
        for name in ('urls.py','files.py','save_request.py','session_variables.py'):
            p=original/name
            if digest(p)!=package_manifest[p.relative_to(package).as_posix()]:raise ValueError('Pinned source package corrupted')
        for row in selected:
            task=tasks[row['record_id']];parsed=extract_test(row);folder=output/row['record_id'];folder.mkdir()
            if parsed['code'] is None:
                grades.append(dict(record_id=row['record_id'],status=parsed['status'],reference_pass=False,kills=0,faults=len(task['faults'])));continue
            conditions=[]
            for label,mutation in [('reference',None)]+task['faults']:
                work=root/'work'
                if work.exists():shutil.rmtree(work)
                (work/'posting').mkdir(parents=True)
                (work/'posting/__init__.py').write_text('# Reference-only UI initialization adapter\n',encoding='utf-8')
                for name in ('urls.py','files.py','save_request.py','session_variables.py'):shutil.copyfile(original/name,work/'posting'/name)
                (work/'test_generated.py').write_text(parsed['code'],encoding='utf-8')
                (work/'controlled_probe.py').write_text(PLUGIN,encoding='utf-8')
                save(work/'condition.json',dict(module=task['module'],mutation=mutation))
                result=execute(work,image_id,folder/(label+'.log'));save(folder/(label+'.json'),result)
                conditions.append(result)
            reference=conditions[0]
            killed=[classify(reference,r) for r in conditions[1:]]
            grades.append(dict(record_id=row['record_id'],status='executed',reference_pass=classify(reference),
                               kills=sum(killed),faults=len(killed),fault_results=dict(zip([n for n,_ in task['faults']],killed))))
    save(output/'summary.json',dict(image_id=image_id,outputs_sha256=digest(outputs),records=grades,
         tasks=5,reference_passes=sum(r['reference_pass'] for r in grades),
         useful_tasks=sum(r['reference_pass'] and r['kills']>0 for r in grades),
         kills=sum(r['kills'] for r in grades),faults=sum(r['faults'] for r in grades),
         limitations='Curated faults are incomplete and correlated, not a universal quality metric. Containers bound resources/network but are not a proof against malicious test/report manipulation. Semantic anti-cheating review remains necessary. Counts are descriptive for one development family.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--outputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--image',required=True);a=p.parse_args();grade(a.outputs,a.output,a.image)
