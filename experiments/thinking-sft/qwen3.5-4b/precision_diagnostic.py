"""One BF16/GGUF reference on the exact saved Q4 diagnostic request."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error

from pipeline import read_rows,write_rows,write_json,sha
from occam_matrix import get_json,output_parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--bf16',required=True,type=Path)
    p.add_argument('--receipt',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--port',default=18187,type=int)
    args=p.parse_args()
    parent=json.loads((args.source/'manifest.json').read_text())
    if not parent['complete'] or parent['outputs_sha256']!=sha(args.source/'outputs.jsonl'):
        raise ValueError('Source diagnostic incomplete/changed')
    row=next(r for r in read_rows(args.source/'outputs.jsonl')
             if r['id']=='me-079' and r['condition']=='base-sampled-thinking')
    receipt=json.loads(args.receipt.read_text())
    if sha(args.bf16)!=receipt['base_bf16_sha256']:raise ValueError('BF16 artifact hash mismatch')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',args.port))==0:raise ValueError('Dedicated port occupied')
    args.output.mkdir(parents=True,exist_ok=False)
    manifest=dict(complete=False,error=None,id=row['id'],source_outputs_sha256=sha(args.source/'outputs.jsonl'),
        bf16_sha256=receipt['base_bf16_sha256'],source_request=row['request'],
        context=20480,script_sha256=sha(Path(__file__)),
        limitation='Single selected case/seed: BF16-vs-Q4 diagnostic only, no benchmark or causal certainty.')
    write_json(args.output/'manifest.json',manifest)
    with (args.output/'server.log').open('w') as log:
        process=subprocess.Popen(['llama-server','--model',str(args.bf16),'--alias','occam2-bf16-diagnostic',
            '--host','127.0.0.1','--port',str(args.port),'--ctx-size','20480','--parallel','1',
            '--jinja','--n-gpu-layers','99'],stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+180
            while True:
                if process.poll() is not None:raise RuntimeError('BF16 server exited')
                try:
                    if get_json(f'http://127.0.0.1:{args.port}/health')['status']=='ok':break
                except (RuntimeError,urllib.error.URLError,TimeoutError):pass
                if time.monotonic()>deadline:raise TimeoutError('BF16 model loading timed out')
                time.sleep(.25)
            props=get_json(f'http://127.0.0.1:{args.port}/props')
            if Path(props['model_path']).resolve()!=args.bf16.resolve():raise ValueError('Wrong model')
            write_json(args.output/'server-props.json',props)
            start=time.monotonic()
            response=get_json(f'http://127.0.0.1:{args.port}/completion',row['request'],timeout=420)
            if response.get('truncated'):raise ValueError('Input truncated')
            reasoning,answer=output_parts(response['content'],True)
            result=dict(id=row['id'],condition='base-bf16-sampled-thinking',request=row['request'],
                response=response,reasoning=reasoning,answer=answer,elapsed_s=time.monotonic()-start)
            write_rows(args.output/'outputs.jsonl',[result])
            manifest.update(complete=True,outputs_sha256=sha(args.output/'outputs.jsonl'))
            print(json.dumps(dict(finish=response['stop_type'],tokens=response['tokens_predicted'],
                                  answer=answer),ensure_ascii=False),flush=True)
        except BaseException as error:
            manifest['error']=type(error).__name__+': '+str(error)
            raise
        finally:
            process.terminate()
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            write_json(args.output/'manifest.json',manifest)


if __name__=='__main__':main()
