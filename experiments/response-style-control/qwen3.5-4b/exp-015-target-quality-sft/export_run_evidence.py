"""Copy small canonical run evidence to Git; weights and blind mapping stay external."""
import argparse
import json
from pathlib import Path
import shutil
from archive_pair import sha

HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(); p.add_argument('--results-root',type=Path,required=True); a=p.parse_args()
    root=a.results_root
    assert json.loads((root/'post-recovery-verification.json').read_text())['status'].startswith('recovered-training-and-inference-verified')
    destination=HERE/'gpu-results-v1'
    assert not destination.exists(),'Refusing overwrite'
    destination.mkdir()
    names=['status.json','status-before-resume.json','pipeline.log','pipeline-resumed.log','cpu-readiness.log',
        'tracking-auth.json','hardware.txt','runtime-python.txt','backup-file-manifest.json',
        'post-recovery-verification.json','output-diagnostics.json','argilla-link.json']
    names+=[f'{model}-evaluation-v1/{name}' for model in ('base','C','E','F') for name in ('manifest.json','answers.jsonl','chat_template.jinja')]
    for arm in ('E','F'):
        names+=[f'{arm}/{name}' for name in ('gpu-gates.json','wandb-run.json','wandb-history.json','wandb-summary.json',
            'exposure-summary.json','representation-check.log','sft.log','evaluation.log')]
        names+=[f'{arm}/sft-v1/{name}' for name in ('source-config.json','effective-training-arguments.json','environment.json',
            'invocation.json','mask-check.json','result.json','training-exposure.jsonl')]
        for step in (30,40):
            names.append(f'{arm}/sft-v1/checkpoints/checkpoint-{step}/trainer_state.json')
        for mode in ('representation-check','smoke','tiny-overfit','smoke-reload'):
            folder=root/arm/mode
            if folder.exists():
                for file in folder.glob('*.json'):
                    names.append(str(file.relative_to(root)).replace('\\','/'))
                if (root/arm/(mode+'.log')).exists(): names.append(f'{arm}/{mode}.log')
    inventory={}
    for name in dict.fromkeys(names):
        file=root/name
        assert file.is_file(),file
        assert file.suffix in ('.json','.jsonl','.log','.txt','.jinja')
        target=destination/name; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,target)
        assert sha(target)==sha(file)
        inventory[name]=dict(sha256=sha(target),bytes=target.stat().st_size)
    (destination/'export-manifest.json').write_text(json.dumps(dict(source=str(root),files=inventory,
        excluded='All adapter weights/optimizer/scheduler/RNG binaries, archives, W&B binary logs and blind item mapping remain in verified external recovery'),indent=2)+'\n')
    print(json.dumps(dict(exported=len(inventory),destination=str(destination))))

if __name__=='__main__':
    main()
