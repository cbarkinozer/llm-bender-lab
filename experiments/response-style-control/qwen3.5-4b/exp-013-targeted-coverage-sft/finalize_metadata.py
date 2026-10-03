"""Post-SFT evidence, not a retroactive passed pre-training reload gate."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('/workspace/exp013-exp014-runs')


def main():
    assert json.loads((ROOT/'status.json').read_text())['status']=='completed'
    summary={}
    for arm in ('C','D'):
        base=ROOT/arm
        manifest=json.loads((base/'validation-v1/manifest.json').read_text())
        assert manifest['status']=='completed' and manifest['count']==20
        for name,expected in manifest['adapter_hashes'].items():
            assert hashlib.sha256((base/'sft-v1/adapter'/name).read_bytes()).hexdigest()==expected
        tracking=json.loads((base/'wandb-summary.json').read_text())
        assert tracking['state']=='finished'
        evidence=dict(status='post-SFT-saved-adapter-reload-verified',primary_output_count=20,
            evidence='Completed inference manifest and adapter hash verification',
            pre_SFT_reload_waived=True,pre_SFT_reload_claimed_passed=False,
            native_eos_count=manifest['native_eos_count'])
        (base/'post-sft-adapter-reload.json').write_text(json.dumps(evidence,indent=2)+'\n')
        rows=[json.loads(line) for line in (base/'validation-v1/answers.jsonl').read_text().splitlines()]
        tokens=sorted(r['output_tokens'] for r in rows)
        summary[arm]=dict(training=json.loads((base/'sft-v1/result.json').read_text())['metrics'],
            native_eos_count=manifest['native_eos_count'],outputs=20,
            stops={reason:sum(r['finish_reason']==reason for r in rows) for reason in {r['finish_reason'] for r in rows}},
            output_tokens=dict(total=sum(tokens),median=(tokens[9]+tokens[10])/2,max=max(tokens)),
            wandb=json.loads((base/'wandb-run.json').read_text()),wandb_state=tracking['state'])
    (ROOT/'run-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    commands=[['uname','-a'],['cat','/etc/os-release'],['lscpu'],['df','-h','/workspace'],
              ['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv']]
    with (ROOT/'platform-metadata.txt').open('w') as file:
        for command in commands:
            file.write('Command: '+' '.join(command)+'\n')
            subprocess.run(command,stdout=file,stderr=subprocess.STDOUT,check=True)
    print(json.dumps(summary))


if __name__=='__main__':
    main()
