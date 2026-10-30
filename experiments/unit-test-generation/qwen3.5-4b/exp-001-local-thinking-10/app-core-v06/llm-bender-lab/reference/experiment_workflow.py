"""New reference orchestrator for the proposed app contract; no backend imports."""
from copy import deepcopy
import json
from pathlib import Path

def run_experiment(root, name, config, rows, *, trainer, evaluator):
    if Path(name).name!=name or name in ('.','..'): raise ValueError('Simple run ID required')
    prompts=set(); train=[]; heldout=[]
    for row in rows:
        messages=row.get('messages',[])
        if len(messages)!=2 or [m.get('role') for m in messages]!=['user','assistant']:
            raise ValueError('Malformed conversation')
        if any(not m.get('content','').strip() for m in messages): raise ValueError('Empty content')
        prompt=' '.join(messages[0]['content'].split()).casefold()
        if prompt in prompts: raise ValueError('Duplicate/overlapping prompt')
        prompts.add(prompt)
        if row['split']=='train': train.append(deepcopy(row))
        elif row['split']=='test': heldout.append(deepcopy(row))
        else: raise ValueError('Unknown split')
    if not train or not heldout: raise ValueError('Both splits required')
    run=Path(root)/name; run.mkdir(parents=True,exist_ok=False)
    secrets=[str(v) for k,v in config.items() if any(s in k.lower() for s in ('secret','token','password','api_key'))]
    resolved={k:deepcopy(v) for k,v in config.items() if not any(s in k.lower() for s in ('secret','token','password','api_key'))}
    def write(name, obj): (run/name).write_text(json.dumps(obj,indent=2))
    write('resolved.json',resolved); write('status.json',{'status':'running'})
    try:
        adapter=Path(trainer(run,deepcopy(resolved),deepcopy(train)))
        if not adapter.is_file() or adapter.parent!=run: raise ValueError('Missing run-local adapter')
        before=evaluator(resolved['model_revision'],deepcopy(heldout),deepcopy(resolved['generation']))
        after=evaluator(str(adapter),deepcopy(heldout),deepcopy(resolved['generation']))
        comparison={k:{'before':before.get(k),'after':after.get(k),'delta':
            None if before.get(k) is None or after.get(k) is None else after[k]-before[k]}
            for k in sorted(before.keys()|after.keys())}
        result={'status':'completed','comparison':comparison}
        write('status.json',result)
        (run/'summary.md').write_text('Before/after comparison\n'+json.dumps(comparison,indent=2))
        (run/'run.log').write_text('Training and matched evaluation completed\n')
        return result
    except Exception as exc:
        error=str(exc)
        for secret in secrets:
            if secret: error=error.replace(secret,'[redacted]')
        result={'status':'failed','error':error}; write('status.json',result)
        (run/'run.log').write_text(error+'\n'); return result
