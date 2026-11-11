"""Upload completed evaluation metrics and output artifacts to W&B."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results-dir',type=Path,required=True)
    p.add_argument('--name',required=True)
    a=p.parse_args()
    import wandb
    manifest=json.loads((a.results_dir/'cetvel/manifest.json').read_text())
    assert manifest['status']=='completed' and manifest['count']==500
    scores=json.loads((a.results_dir/'cetvel/scores.json').read_text())
    text=json.loads((a.results_dir/'text/text-scores.json').read_text())
    grammar=json.loads((a.results_dir/'turblimp/scores.json').read_text())
    run=wandb.init(project='lfm3-turkish-post-training',name=a.name,
        group='lfm3-1.7b-turkish-wikipedia-cpt-v01',job_type='eval',
        config=manifest,dir=str(a.results_dir))
    def flatten(prefix,obj):
        for key,value in obj.items():
            if isinstance(value,dict):
                flatten(prefix+'/'+key,value)
            elif isinstance(value,(int,float)):
                run.summary[prefix+'/'+key]=value
    flatten('cetvel',scores)
    flatten('text',{k:{n:v for n,v in obj.items() if n!='documents'} for k,obj in text['results'].items()})
    flatten('turblimp',grammar)
    artifact=wandb.Artifact(a.name,type='evaluation')
    evidence={}
    for folder in ('cetvel','text','turblimp'):
        for file in sorted((a.results_dir/folder).glob('*')):
            if file.is_file():
                relative=file.relative_to(a.results_dir).as_posix()
                artifact.add_file(str(file),name=relative)
                evidence[relative]=hashlib.sha256(file.read_bytes()).hexdigest()
    run.log_artifact(artifact).wait()
    (a.results_dir/'wandb-run.json').write_text(json.dumps(dict(id=run.id,url=run.url,files=evidence),indent=2)+'\n')
    print(run.url,flush=True)
    run.finish()


if __name__=='__main__':
    main()
