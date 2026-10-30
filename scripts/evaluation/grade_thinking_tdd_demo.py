"""Grade saved demo suites only in resource-limited, network-disabled Docker."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VERIFIER=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/verifier'
IMAGE='llm-bender-pytest:integration-v01'

def execute(directory):
    command=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--pids-limit','64','--memory','512m','--cpus','1',
             '--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--mount',f'type=bind,src={directory},dst=/workspace,readonly',
             '--workdir','/workspace',IMAGE,'python','-m','pytest','-q','-p','no:cacheprovider',
             '--override-ini','addopts=','test_generated.py']
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        return dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
    except subprocess.TimeoutExpired:
        return dict(returncode=None,error='timeout')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run',type=Path);args=parser.parse_args()
    grades=[]
    for task in json.loads((args.run/'manifest.json').read_text())['task_ids']:
        item=args.run/task
        if not (item/'summary.json').exists(): continue
        destination=item/'grade.json'
        if destination.exists(): grades.append(json.loads(destination.read_text()));continue
        with tempfile.TemporaryDirectory(prefix='bender-tdd-grade-') as tmp:
            folder=Path(tmp)
            for name in ['references.py','faults.py']: shutil.copyfile(VERIFIER/name,folder/name)
            shutil.copyfile(item/'generated_tests.py',folder/'test_generated.py')
            (folder/'solution.py').write_text('from references import *\n')
            reference=execute(folder)
            (folder/'solution.py').write_text('from references import *\nfrom faults import CASES\nfor task, name, faulty, args, expected in CASES:\n    if task == '+repr(task)+':\n        globals()[name] = faulty\n')
            fault=execute(folder)
        # Pytest exit 1 means test failure; collection/runtime infrastructure errors
        # and no-tests exit codes never count as a detected fault.
        grade=dict(task_id=task,reference_pass=reference['returncode']==0,
                   fault_detected=reference['returncode']==0 and fault['returncode']==1,
                   reference=reference,fault=fault,
                   note='One diagnostic mutant, not comprehensive coverage. Semantic review still required.')
        destination.write_text(json.dumps(grade,indent=2)+'\n');grades.append(grade)
        print(task,grade['reference_pass'],grade['fault_detected'],flush=True)
    (args.run/'grades.json').write_text(json.dumps(grades,indent=2)+'\n')

if __name__=='__main__':main()
