"""Higher-budget diagnostics for truncated original-matrix thinking attempts.

Preserves the original matrix; retries only token-limited thinking attempts.
Budgets:8192 then16384 for still-token-limited items, no correctness-based retries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error

from pipeline import sha, write_json, write_rows, read_rows
from occam_matrix import validate_artifacts, get_json, output_parts

BUDGETS=(8192,16384)


def selected_attempts(rows):
    return [r for r in rows if r['thinking'] and r['response']['stop_type']=='limit']


def still_token_limited(row):
    return (row['response']['stop_type']=='limit' and
            row['response']['tokens_predicted'] >= row['request']['n_predict'])


def request_for(original,budget):
    if not original['thinking']:
        raise ValueError('Recovery is thinking-on only')
    request=dict(original['request'])
    # Preserve penalties/sampling/seed and exact rendered prompt. Keep the
    # original8192-token repetition window: only resource limits change.
    request.update(n_predict=budget,t_max_predict_ms=600000 if budget==8192 else 1200000)
    return request


def summary(original_rows,recovered,complete):
    final={(r['condition'],r['id']):r for r in original_rows}
    for row in recovered:
        final[row['condition'],row['id']]=row
    result=dict(recovery_complete=complete,attempts=len(recovered),
        original_selected=len(selected_attempts(original_rows)),conditions={},
        interpretation='Adaptive budget recovery on previously truncated items, not a uniform8192/16384-budget benchmark or accuracy score.')
    for condition in ('base-thinking-true','occam1-thinking-true'):
        rows=[r for r in final.values() if r['condition']==condition]
        result['conditions'][condition]={cohort:dict(items=len(items),
            natural_eos=sum(r['response']['stop_type']=='eos' for r in items),
            still_limited=sum(r['response']['stop_type']=='limit' for r in items),
            empty_final=sum(not r['answer'].strip() for r in items),
            limited_ids=[r['id'] for r in items if r['response']['stop_type']=='limit'])
            for cohort in ('original20','controls12')
            for items in [[r for r in rows if r['cohort']==cohort]]}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',required=True,type=Path)
    p.add_argument('--base',required=True,type=Path)
    p.add_argument('--occam',required=True,type=Path)
    p.add_argument('--tokenizer',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--port',default=18184,type=int)
    p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    manifest=json.loads((args.original/'matrix-manifest.json').read_text())
    if not manifest['complete'] or manifest['completed']!=128:
        raise ValueError('Original matrix must be complete')
    if sha(args.original/'outputs.jsonl')!=manifest['outputs_sha256']:
        raise ValueError('Original outputs changed')
    original_rows=read_rows(args.original/'outputs.jsonl')
    selected=selected_attempts(original_rows)
    if len({(r['condition'],r['id']) for r in selected})!=len(selected):
        raise ValueError('Duplicate original attempts')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True,trust_remote_code=False)
    artifacts=validate_artifacts(args.base,args.occam,tokenizer)
    if artifacts!=manifest['provenance']['artifacts']:
        raise ValueError('Recovery must use the exact original artifacts/template')
    provenance=dict(original_manifest_sha256=sha(args.original/'matrix-manifest.json'),
        original_outputs_sha256=manifest['outputs_sha256'],artifacts=artifacts,
        budgets=BUDGETS,contexts=[b+4096 for b in BUDGETS],
        script_sha256=sha(Path(__file__)),shared_script_sha256=sha(Path(__file__).with_name('occam_matrix.py')),
        selected=[dict(condition=r['condition'],id=r['id']) for r in selected],
        policy='Only token/time-limited thinking attempts selected. Escalate only still-token-limited items. Never retry wrong completed answers.',
        runtime='\n'.join(line for line in subprocess.check_output(['llama-server','--version'],stderr=subprocess.STDOUT,text=True).splitlines()
                          if line.startswith(('version:','built with'))))
    # JSON normalizes tuples to arrays; compare the normalized structure on resume.
    provenance=json.loads(json.dumps(provenance))
    path=args.output/'recovery-manifest.json'
    if path.exists():
        previous=json.loads(path.read_text())
        if not args.resume or previous['provenance']!=provenance or previous['complete']:
            raise ValueError('Explicit identical-code resume required; completed recovery is immutable')
    elif args.output.exists():
        raise ValueError('Choose a fresh output directory')
    args.output.mkdir(parents=True,exist_ok=args.resume)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',args.port))==0:
            raise ValueError('Dedicated port occupied')
    recovered=read_rows(args.output/'outputs.jsonl') if (args.output/'outputs.jsonl').exists() else []
    completed={(r['condition'],r['id'],r['request']['n_predict']) for r in recovered}
    if len(completed)!=len(recovered):
        raise ValueError('Duplicate recovery attempts')
    status=dict(complete=False,provenance=provenance,completed=len(recovered),error=None)
    write_json(path,status)
    try:
        for budget in BUDGETS:
            latest={(r['condition'],r['id']):r for r in selected}
            for row in recovered:
                latest[row['condition'],row['id']]=row
            for name,model_path in (('base',args.base),('occam1',args.occam)):
                condition=f'{name}-thinking-true'
                pending=[r for key,r in latest.items() if key[0]==condition
                    and (r['condition'],r['id'],budget) not in completed and still_token_limited(r)]
                if not pending:
                    continue
                context=budget+4096
                with (args.output/f'{name}-{budget}-server.log').open('a') as log:
                    process=subprocess.Popen(['llama-server','--model',str(model_path),'--alias',f'occam2-recovery-{name}',
                        '--host','127.0.0.1','--port',str(args.port),'--ctx-size',str(context),
                        '--parallel','1','--jinja','--n-gpu-layers','99'],stdout=log,stderr=subprocess.STDOUT)
                    try:
                        deadline=time.monotonic()+120
                        while True:
                            if process.poll() is not None:
                                raise RuntimeError('Dedicated server exited during startup')
                            try:
                                if get_json(f'http://127.0.0.1:{args.port}/health')['status']=='ok':break
                            except (RuntimeError,urllib.error.URLError,TimeoutError):pass
                            if time.monotonic()>deadline:raise TimeoutError('Model loading timed out')
                            time.sleep(.25)
                        props=get_json(f'http://127.0.0.1:{args.port}/props')
                        if Path(props['model_path']).resolve()!=model_path.resolve():
                            raise ValueError('Wrong served model')
                        write_json(args.output/f'{name}-{budget}-server-props.json',props)
                        for previous in pending:
                            original=next(r for r in selected if (r['condition'],r['id'])==(condition,previous['id']))
                            request=request_for(original,budget)
                            rendered=request['prompt']
                            if hashlib.sha256(rendered.encode()).hexdigest()!=original['prompt_sha256']:
                                raise ValueError('Original prompt changed')
                            if len(tokenizer.encode(rendered,add_special_tokens=False))+budget>context:
                                raise ValueError('Prompt and output allowance exceed context')
                            start=time.monotonic()
                            response=get_json(f'http://127.0.0.1:{args.port}/completion',request,
                                timeout=request['t_max_predict_ms']/1000+120)
                            if response.get('truncated'):raise ValueError('Input was truncated')
                            reasoning,answer=output_parts(response['content'],True)
                            row={k:original[k] for k in ('id','condition','category','cohort','thinking','prompt_sha256','rendered_prompt')}
                            row.update(request=request,response=response,reasoning=reasoning,answer=answer,
                                context=context,elapsed_s=time.monotonic()-start,original_budget=4096,
                                original_finish=original['response']['stop_type'],
                                attempt_kind='higher-budget recovery diagnostic')
                            recovered.append(row);completed.add((condition,row['id'],budget))
                            write_rows(args.output/'outputs.jsonl',recovered)
                            status.update(completed=len(recovered),outputs_sha256=sha(args.output/'outputs.jsonl'))
                            write_json(path,status)
                            write_json(args.output/'recovery-summary.json',summary(original_rows,recovered,False))
                            print(f'{condition} {row["id"]} budget={budget}: {response["stop_type"]}, {response["tokens_predicted"]} tokens, final={bool(answer)}',flush=True)
                    finally:
                        process.terminate()
                        try:process.wait(timeout=20)
                        except subprocess.TimeoutExpired:process.kill();process.wait()
        status['complete']=True
    except BaseException as error:
        status['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        write_json(path,status)
        result=summary(original_rows,recovered,status['complete'])
        write_json(args.output/'recovery-summary.json',result)
        print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
