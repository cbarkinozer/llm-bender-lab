"""Execute/count the nine compact candidate suites without downloading models."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
REPOS=ROOT.parent
BUNDLE=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v02'
ARTIFACTS=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts')
AUDIT=ARTIFACTS/'thinking-tdd/repo-audit-20261030'
PYTHON=ARTIFACTS/'occam-gguf-20261026/.venv/bin/python'
TOKENIZER=ARTIFACTS/'occam-gguf-20261026/base'
NAMES=['GitHub-insignia','ghost-box','slm_test_generation','llm-bender-lab','ReflexModels','codelang-detect','repo-context','cryptocurrency-analyser','miniature-llms']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', choices=NAMES)
    parser.add_argument('--revision', choices=['app-core-v02','app-core-v03','app-core-v04','app-core-v05'], default='app-core-v02')
    args=parser.parse_args()
    bundle=BUNDLE.parent/args.revision
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(TOKENIZER/'tokenizer.json'))
    output=ARTIFACTS/('thinking-tdd/'+args.revision)/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    reports=[]
    for name in ([args.repo] if args.repo else NAMES):
        folder=bundle/name.lower();repo=REPOS/name
        files=sorted((folder/'tests').rglob('*.py'))
        if (folder/'pytest.ini').exists(): files.append(folder/'pytest.ini')
        assert files, name
        python=repo/'.venv/bin/python' if name in ['GitHub-insignia','ghost-box'] else PYTHON
        paths=[str(folder/'reference'),str(repo),str(repo/'src')]
        if name=='llm-bender-lab':paths.append(str(repo/'experiments/thinking-sft/qwen3.5-4b'))
        if name!='GitHub-insignia':paths.append(str(AUDIT/'deps'))
        env={**os.environ,'PYTHONPATH':os.pathsep.join(paths),'PYTHONDONTWRITEBYTECODE':'1','QT_QPA_PLATFORM':'offscreen','HF_HUB_OFFLINE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','TDD_TOKENIZER_PATH':str(TOKENIZER)}
        # Strip credentials; core fixtures must never require them.
        for key in list(env):
            if any(word in key.upper() for word in ('TOKEN','API_KEY','PASSWORD','SECRET')) and key!='TDD_TOKENIZER_PATH':env.pop(key)
        command=[str(python),'-m','pytest','-q',str(folder/'tests')]
        if args.revision=='app-core-v04' and name=='slm_test_generation':command+=['--log-cli-level=INFO']
        if (folder/'pytest.ini').exists():command.extend(['-c',str(folder/'pytest.ini')])
        started=time.monotonic()
        try:
            result=subprocess.run(command,cwd=repo,env=env,capture_output=True,text=True,timeout=90)
            stdout=result.stdout+result.stderr;exitcode=result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout=str(exc);exitcode=None
        (output/(name+'.log')).write_text(stdout)
        parts=[dict(path=str(p.relative_to(folder)),chars=len(p.read_text()),tokens=len(tokenizer.encode(p.read_text(),add_special_tokens=False).ids),sha256=sha256(p.read_bytes()).hexdigest()) for p in files]
        # This is the exact test-files answer payload, not a sum of repo suites.
        payload='\n\n'.join('File: '+str(p.relative_to(folder))+'\n```'+('ini' if p.suffix=='.ini' else 'python')+'\n'+p.read_text()+'```' for p in files)+'\n'
        (folder/'test-output.md').write_text(payload)
        report=dict(repo=name,returncode=exitcode,seconds=round(time.monotonic()-started,2),test_source_tokens=sum(p['tokens'] for p in parts),output_payload_tokens=len(tokenizer.encode(payload,add_special_tokens=False).ids),files=parts,log=str(output/(name+'.log')),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),reference_files=[dict(path=str(p.relative_to(folder)),sha256=sha256(p.read_bytes()).hexdigest()) for p in sorted((folder/'reference').glob('*.py'))],source_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()))
        reports.append(report)
        print(name,exitcode,report['output_payload_tokens'],stdout[-150:].strip(),flush=True)
    manifest=dict(reports=reports,tokenizer=str(TOKENIZER),tokenizer_sha256=sha256((TOKENIZER/'tokenizer.json').read_bytes()).hexdigest(),total_test_output_tokens=sum(r['output_payload_tokens'] for r in reports),note='Candidate compact tests and required fixtures, not all-requirements certification. Payload excludes request, clarification/interface, teacher reasoning and native chat framing.')
    (output/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (bundle/('execution-receipt-'+args.repo+'.json' if args.repo else 'execution-receipt.json')).write_text(json.dumps(dict(results=str(output/'results.json'),passed=all(r['returncode']==0 for r in reports)),indent=2)+'\n')
    (bundle/('execution-'+args.repo+'.json' if args.repo else 'token-and-execution-report.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print('RESULTS',output,flush=True)

if __name__=='__main__':main()
