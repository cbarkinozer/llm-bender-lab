"""Deferred record-specific executor probe; excluded from active format work."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v04-record-specific-draft'
ART=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts/thinking-tdd')


def main():
    sys.path[:0]=[str(BUNDLE/'slm_test_generation/reference'),str(ROOT.parent/'slm_test_generation')]
    from benchmark_workflow import run_task
    output=ART/'app-core-v04-executor-probe'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    cases=[('success','def test_value():\n    assert sut() == 42','passed',True),
           ('skipped','import pytest\n@pytest.mark.skip(reason="fixture")\ndef test_skip():\n    assert sut() == 42','passed',False),
           ('empty','','collection_error',False),
           ('timeout','def test_forever():\n    while True: pass','timeout',False)]
    reports=[]
    for name,source,outcome,useful in cases:
        # No executor injection here: exercise the actual default Docker path.
        result=run_task(dict(id=name,source=source,sut_names=['sut'],context='B',dependency='L1'),
                        root=output,sut_source='def sut(): return 42',timeout_seconds=2)
        assert result['backend']=='docker' and result['outcome']==outcome and result['useful_success'] is useful
        assert '--network' in result['command'] and result['command'][result['command'].index('--network')+1]=='none'
        reports.append(result)
        print(name,result['backend'],result['outcome'],f"pytest={result['pytest_seconds']:.3f}s outer={result['executor_seconds']:.3f}s",flush=True)
    image=reports[0]['configured_image']
    image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
    report=dict(results=reports,image_id=image_id,all_passed=True,
        reference_snapshot={str(p.relative_to(BUNDLE)):sha256(p.read_bytes()).hexdigest() for p in sorted((BUNDLE/'slm_test_generation/reference').glob('*.py'))},
        note='New demo runtime, not the historical Python3.10 benchmark harness. Timing is measured, not promised. Unit fixtures use an explicit local executor; these probes use default Docker.')
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (BUNDLE/'executor-probe-receipt.json').write_text(json.dumps(dict(results=str(output/'results.json'),all_passed=True),indent=2)+'\n')
    print(output)

if __name__=='__main__':main()
