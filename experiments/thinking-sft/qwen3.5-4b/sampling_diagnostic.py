"""Bounded Qwen-recommended sampling check on three observed looping cases.

Six attempts total, same three original prompts for base and Occam. This is an
outcome-selected infrastructure diagnostic, not a new benchmark score.
"""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error

from pipeline import read_rows,write_rows,write_json,sha
from occam_matrix import get_json,output_parts,validate_artifacts

IDS=('me-049','me-079','me-090')
SETTINGS=dict(n_predict=4096,temperature=1.0,top_p=.95,top_k=20,min_p=0.0,
              presence_penalty=1.5,repeat_penalty=1.0,repeat_last_n=8192,
              seed=3407,cache_prompt=False,stream=False,return_tokens=True,t_max_predict_ms=300000)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','base','occam','tokenizer','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--port',type=int,default=18186)
    p.add_argument('--repeat-penalty',type=float,default=1.0)
    p.add_argument('--presence-penalty',type=float,default=1.5)
    p.add_argument('--ids',nargs='+',choices=IDS,default=list(IDS))
    args=p.parse_args()
    if not 1.0<=args.repeat_penalty<=1.2:
        raise ValueError('This bounded diagnostic supports modest repetition penalties from1.0 to1.2')
    if not 0<=args.presence_penalty<=1.5:
        raise ValueError('Presence penalty must be between0 and1.5 for this diagnostic')
    if len(set(args.ids))!=len(args.ids):raise ValueError('Duplicate diagnostic IDs')
    settings=dict(SETTINGS,repeat_penalty=args.repeat_penalty,presence_penalty=args.presence_penalty)
    expected=2*len(args.ids)
    original=json.loads((args.original/'matrix-manifest.json').read_text())
    if not original['complete'] or original['outputs_sha256']!=sha(args.original/'outputs.jsonl'):
        raise ValueError('Original matrix incomplete/changed')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True,trust_remote_code=False)
    artifacts=validate_artifacts(args.base,args.occam,tokenizer)
    if artifacts!=original['provenance']['artifacts']:raise ValueError('Artifact mismatch')
    source=read_rows(args.original/'outputs.jsonl')
    args.output.mkdir(parents=True,exist_ok=False)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',args.port))==0:raise ValueError('Dedicated port occupied')
    status=dict(complete=False,items=0,error=None,settings=settings,context=20480,
        ids=args.ids,expected=expected,artifacts=artifacts,original_outputs_sha256=original['outputs_sha256'],
        script_sha256=sha(Path(__file__)),source='https://huggingface.co/Qwen/Qwen3.5-4B#quickstart',
        limitation='Three outcome-selected looping cases, one seeded sample per model; no accuracy or general sampler superiority claim.')
    write_json(args.output/'manifest.json',status)
    rows=[]
    try:
        for name,model in (('base',args.base),('occam1',args.occam)):
            with (args.output/f'{name}-server.log').open('w') as log:
                process=subprocess.Popen(['llama-server','--model',str(model),'--alias',f'occam2-sampling-{name}',
                    '--host','127.0.0.1','--port',str(args.port),'--ctx-size','20480',
                    '--parallel','1','--jinja','--n-gpu-layers','99'],stdout=log,stderr=subprocess.STDOUT)
                try:
                    deadline=time.monotonic()+120
                    while True:
                        if process.poll() is not None:raise RuntimeError('Server exited')
                        try:
                            if get_json(f'http://127.0.0.1:{args.port}/health')['status']=='ok':break
                        except (RuntimeError,urllib.error.URLError,TimeoutError):pass
                        if time.monotonic()>deadline:raise TimeoutError('Model loading timed out')
                        time.sleep(.25)
                    props=get_json(f'http://127.0.0.1:{args.port}/props')
                    if Path(props['model_path']).resolve()!=model.resolve():raise ValueError('Wrong model')
                    write_json(args.output/f'{name}-server-props.json',props)
                    for identity in args.ids:
                        old=next(r for r in source if r['id']==identity and r['condition']==f'{name}-thinking-true')
                        request=dict(prompt=old['request']['prompt'],**settings)
                        start=time.monotonic()
                        response=get_json(f'http://127.0.0.1:{args.port}/completion',request,timeout=360)
                        if response.get('truncated'):raise ValueError('Input truncated')
                        effective=response['generation_settings']
                        if any(abs(effective[key]-settings[key])>1e-5
                               for key in ('temperature','repeat_penalty','presence_penalty')):
                            raise ValueError('Effective server sampler settings differ from the request')
                        reasoning,answer=output_parts(response['content'],True)
                        rows.append(dict(id=identity,condition=f'{name}-sampled-thinking',request=request,
                            response=response,reasoning=reasoning,answer=answer,elapsed_s=time.monotonic()-start,
                            original_prompt_sha256=old['prompt_sha256']))
                        write_rows(args.output/'outputs.jsonl',rows)
                        status.update(items=len(rows),outputs_sha256=sha(args.output/'outputs.jsonl'))
                        write_json(args.output/'manifest.json',status)
                        print(f'{len(rows)}/{expected} {name} {identity}: {response["stop_type"]}, {response["tokens_predicted"]} tokens, final={bool(answer)}',flush=True)
                finally:
                    process.terminate()
                    try:process.wait(timeout=20)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
        status['complete']=len(rows)==expected
    except BaseException as error:
        status['error']=type(error).__name__+': '+str(error)
        raise
    finally:write_json(args.output/'manifest.json',status)


if __name__=='__main__':main()
