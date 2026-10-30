"""Three seeded test-order runs of trusted suites; preserve snapshots and node IDs."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v03'
ART=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts')
DEPS=ART/'thinking-tdd/repo-audit-20261030/deps'
PYTHON=ART/'occam-gguf-20261026/.venv/bin/python'


def main():
    global BUNDLE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo')
    parser.add_argument('--revision',choices=['app-core-v03','app-core-v04'],default='app-core-v03')
    args=parser.parse_args()
    BUNDLE=BUNDLE.parent/args.revision
    output=ART/('thinking-tdd/'+args.revision+'-stability')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    runs=json.loads((BUNDLE/'token-and-execution-report.json').read_text())['reports']
    results=[]
    for run in runs:
        repo=run['repo']
        if args.repo and repo!=args.repo:continue
        source=ROOT.parent/repo;folder=BUNDLE/repo.lower()
        for seed in (17,43,91):
            target=output/repo/str(seed);target.mkdir(parents=True)
            (target/'order_probe.py').write_text('import json, random\nfrom pathlib import Path\ndef pytest_collection_modifyitems(items):\n    random.Random('+str(seed)+').shuffle(items)\n    Path('+repr(str(target/'order.json'))+').write_text(json.dumps([i.nodeid for i in items],indent=2))\n')
            env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,[target,folder/'reference',source,source/'src',DEPS])),
                     PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',QT_QPA_PLATFORM='offscreen',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            for key in list(env):
                if any(s in key.upper() for s in ('TOKEN','API_KEY','PASSWORD','SECRET')):env.pop(key)
            python=source/'.venv/bin/python' if repo in ('GitHub-insignia','ghost-box') else PYTHON
            command=[str(python),'-m','pytest','-q','-p','order_probe',str(folder/'tests')]
            if (folder/'pytest.ini').exists():command+=['-c',str(folder/'pytest.ini')]
            result=subprocess.run(command,cwd=source,env=env,capture_output=True,text=True,timeout=90)
            (target/'pytest.log').write_text(result.stdout+result.stderr)
            order=json.loads((target/'order.json').read_text())
            results.append(dict(repo=repo,seed=seed,returncode=result.returncode,collected=len(order),
                order=order,log=str(target/'pytest.log'),
                test_snapshot={str(p.relative_to(folder)):sha256(p.read_bytes()).hexdigest() for p in sorted((folder/'tests').rglob('*.py'))},
                reference_snapshot={str(p.relative_to(folder)):sha256(p.read_bytes()).hexdigest() for p in sorted((folder/'reference').glob('*.py'))}))
            print(repo,seed,'PASS' if result.returncode==0 else 'FAIL',len(order),'cases',flush=True)
    for repo in {r['repo'] for r in results}:
        group=[r for r in results if r['repo']==repo]
        assert len(group)==3 and len({tuple(r['order']) for r in group})==3, 'Orders did not change'
        assert all(set(r['order'])==set(group[0]['order']) for r in group), 'Collection changed'
    if args.repo:
        assert results, args.repo
        previous=json.loads(Path(json.loads((BUNDLE/'stability-receipt.json').read_text())['results']).read_text())
        results=[r for r in previous['results'] if r['repo']!=args.repo]+results
    report=dict(results=results,all_passed=all(r['returncode']==0 for r in results),
                note='Seeded stdlib shuffle plugin changes collection order; no claim of hermetic fresh dependency environments. External calls are mocked; generated fixture suites use network-disabled Docker.')
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (BUNDLE/'stability-receipt.json').write_text(json.dumps(dict(results=str(output/'results.json'),all_passed=report['all_passed']),indent=2)+'\n')
    print(output)

if __name__=='__main__':main()
