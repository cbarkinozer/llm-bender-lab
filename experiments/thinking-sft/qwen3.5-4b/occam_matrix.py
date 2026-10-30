"""Matched local Q4 matrix on original Occam20 + separate12 controls.

All model calls use original messages only, never references/review criteria.
Historical BF16 outputs remain a separate evidence series.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error
import urllib.request

from pipeline import ROOT, sha, write_json, write_rows, read_rows

REPO = ROOT.parents[2]
OLD = REPO / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft'
SOURCES = ('data-reviewed-v1/validation-reviewed.jsonl', 'controls-reviewed-v1/questions-12.jsonl')
SOURCE_HASHES = ('43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429',
                 '21f46cef4d1e80dbde9ea5db69ea83b409efc67ae6c17260a411938b35dabd05')
SETTINGS = dict(n_predict=4096, temperature=0.0, top_k=0, top_p=1.0, min_p=0.0,
                repeat_penalty=1.05, repeat_last_n=8192, seed=3407,
                cache_prompt=False, stream=False, return_tokens=True, t_max_predict_ms=180000)


def benchmark():
    result, keys = [], []
    for name, digest, size, cohort in zip(SOURCES, SOURCE_HASHES, (20, 12), ('original20', 'controls12')):
        path = OLD / name
        if sha(path) != digest:
            raise ValueError(f'Original benchmark changed: {name}')
        rows = read_rows(path)
        if len(rows) != size:
            raise ValueError('Historical cohort size changed')
        for row in rows:
            identity = {k: row.get(k) for k in ('id', 'category')}
            result.append(identity | dict(cohort=cohort, messages=row['messages']))
            keys.append(identity | dict(cohort=cohort, reference=row['desired_answer'],
                                         evaluation_criteria=row.get('evaluation_criteria', '')))
    if len({r['id'] for r in result}) != 32:
        raise ValueError('Duplicate benchmark IDs')
    return result, keys


def gguf_signature(path):
    from gguf import GGUFReader
    reader = GGUFReader(path)
    if reader.fields['qwen35.block_count'].contents() != 32:
        raise ValueError('Expected32 main decoder blocks')
    return dict(tensors={t.name: dict(shape=t.shape.tolist(), type=int(t.tensor_type)) for t in reader.tensors},
                template=reader.fields['tokenizer.chat_template'].contents(),
                vocabulary=reader.fields['tokenizer.ggml.tokens'].contents(),
                token_types=reader.fields['tokenizer.ggml.token_type'].contents(),
                file_type=reader.fields['general.file_type'].contents())


def validate_artifacts(base, occam, tokenizer):
    signatures = [gguf_signature(path) for path in (base, occam)]
    for key in ('tensors', 'template', 'vocabulary', 'token_types', 'file_type'):
        if signatures[0][key] != signatures[1][key]:
            raise ValueError(f'Base/Occam GGUF {key} mismatch')
    if signatures[0]['template'] != tokenizer.chat_template:
        raise ValueError('GGUF/native source template mismatch')
    return dict(base_sha256=sha(base), occam_sha256=sha(occam),
        tensors=len(signatures[0]['tensors']),
        tensor_types=dict(collections.Counter(str(t['type']) for t in signatures[0]['tensors'].values())),
        template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest())


def get_json(url, data=None, timeout=10):
    request = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body=error.read().decode(errors='replace')
        raise RuntimeError(f'Local inference HTTP {error.code}: {body}') from error


def rendered_input(tokenizer, messages, thinking):
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                          enable_thinking=thinking)


def output_parts(raw, thinking):
    if thinking:
        if '</think>' not in raw:
            return raw, ''
        reasoning, answer = raw.split('</think>', 1)
        return reasoning.removeprefix('<think>').strip(), answer.strip()
    return '', raw.strip()


def summarize(work, manifest):
    rows = read_rows(work/'outputs.jsonl') if (work/'outputs.jsonl').exists() else []
    result = dict(run_complete=manifest['complete'], expected=128, saved=len(rows), conditions={})
    for model in ('base', 'occam1'):
        for thinking in (False, True):
            label = f'{model}-thinking-{str(thinking).lower()}'
            selected = [r for r in rows if r['condition'] == label]
            result['conditions'][label] = {cohort:dict(items=len(items),
                natural_eos=sum(r['response']['stop_type'] == 'eos' for r in items),
                empty_final=sum(not r['answer'].strip() for r in items),
                total_output_tokens=sum(r['response']['tokens_predicted'] for r in items),
                seconds=sum(r['elapsed_s'] for r in items))
                for cohort in ('original20', 'controls12')
                for items in [[r for r in selected if r['cohort'] == cohort]]}
    result['accuracy'] = 'Not scored; semantic human review required. Runtime completion is not correctness.'
    write_json(work/'mechanical-summary.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True, type=Path)
    p.add_argument('--occam', required=True, type=Path)
    p.add_argument('--tokenizer', required=True, type=Path)
    p.add_argument('--work', required=True, type=Path)
    p.add_argument('--port', default=18183, type=int)
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--resume', action='store_true', help='Only resume completed item IDs; no automatic failure retries')
    args = p.parse_args()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True, trust_remote_code=False)
    prompts, keys = benchmark()
    artifacts = validate_artifacts(args.base, args.occam, tokenizer)
    if artifacts['occam_sha256'] != 'e640ec52d141138a1ee568421c821a9308eb5cdbb94112f3d3f2f77418069857':
        raise ValueError('Expected released Occam1 artifact')
    args.work.mkdir(parents=True, exist_ok=True)
    manifest_path = args.work/'matrix-manifest.json'
    write_rows(args.work/'benchmark-prompts.jsonl', prompts)
    write_rows(args.work/'benchmark-keys.jsonl', keys)
    provenance = dict(artifacts=artifacts, settings=SETTINGS, context=8192, parallel=1,
        starting_model='unsloth/Qwen3.5-4B', starting_revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',
        occam_adapter_revision='1a8a07ff2a29f51a2b6a635a8c219191a7377996',
        source_sha256=dict(zip(SOURCES, SOURCE_HASHES)),
        benchmark_prompts_sha256=sha(args.work/'benchmark-prompts.jsonl'),
        script_sha256=sha(Path(__file__)),
        runtime='\n'.join(line for line in subprocess.check_output(
            ['llama-server','--version'],stderr=subprocess.STDOUT,text=True).splitlines()
            if line.startswith(('version:', 'built with'))),
        limitation='Matched local Q4 deployment matrix; not exact reproduction of historical BF16/HF results.',
        mode_policy='Only native thinking template flag changes; original messages/no added system prompt.',
        generation_policy='Historical greedy/repetition1.05/output4096 adapted to llama.cpp; same for all four arms. Native GGUF EOG handling; no historical Python exact-loop guard.',
        sample_policy='One deterministic attempt; no outcome-based reruns. Time/token-limit outputs retained.')
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if not args.resume or previous['provenance'] != provenance:
            raise ValueError('Existing run: explicit resume with identical code/artifacts/settings required')
        if previous['complete']:
            raise ValueError('Matrix already complete')
    manifest = dict(complete=False, provenance=provenance, completed=0, error=None)
    write_json(manifest_path,manifest)
    write_json(args.work/'rendered-preview.json', [dict(id=row['id'],thinking=thinking,
        rendered=rendered_input(tokenizer,row['messages'],thinking))
        for row in (prompts[0],next(r for r in prompts if len(r['messages'])>1)) for thinking in (False,True)])
    if args.prepare_only:
        print('Validated matched artifacts and froze original20 + controls12. No model inference run.')
        return
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', args.port)) == 0:
            raise ValueError('Dedicated server port is occupied; refusing to reuse an unknown server')
    rows = read_rows(args.work/'outputs.jsonl') if (args.work/'outputs.jsonl').exists() else []
    done = {(r['condition'],r['id']) for r in rows}
    if len(done) != len(rows):
        raise ValueError('Duplicate completed records')
    try:
        for name, path in (('base',args.base),('occam1',args.occam)):
            if all((f'{name}-thinking-{str(t).lower()}',r['id']) in done for t in (False,True) for r in prompts):
                continue
            with (args.work/f'{name}-server.log').open('a') as log:
                process = subprocess.Popen(['llama-server','--model',str(path),'--alias',f'occam2-matrix-{name}',
                    '--host','127.0.0.1','--port',str(args.port),'--ctx-size','8192','--parallel','1',
                    '--jinja','--n-gpu-layers','99'], stdout=log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic()+120
                    while True:
                        if process.poll() is not None:
                            raise RuntimeError('Dedicated llama-server exited; inspect its log')
                        try:
                            if get_json(f'http://127.0.0.1:{args.port}/health')['status']=='ok':
                                break
                        except (urllib.error.URLError, TimeoutError, RuntimeError):
                            pass
                        if time.monotonic()>deadline:
                            raise TimeoutError('Model loading timed out')
                        time.sleep(.25)
                    props=get_json(f'http://127.0.0.1:{args.port}/props')
                    if Path(props['model_path']).resolve()!=path.resolve():
                        raise ValueError('Wrong served artifact')
                    write_json(args.work/f'{name}-server-props.json',props)
                    for thinking in (False,True):
                        label=f'{name}-thinking-{str(thinking).lower()}'
                        for row in prompts:
                            if (label,row['id']) in done:
                                continue
                            rendered=rendered_input(tokenizer,row['messages'],thinking)
                            count=len(tokenizer.encode(rendered,add_special_tokens=False))
                            if count+SETTINGS['n_predict']>8192:
                                raise ValueError('Prompt/output exceed frozen context')
                            request=dict(prompt=rendered,**SETTINGS)
                            start=time.monotonic()
                            response=get_json(f'http://127.0.0.1:{args.port}/completion',request,timeout=240)
                            if response.get('truncated'):
                                raise ValueError('Server truncated input')
                            reasoning,answer=output_parts(response['content'],thinking)
                            record=dict(id=row['id'],cohort=row['cohort'],category=row['category'],
                                condition=label,thinking=thinking,rendered_prompt=rendered,
                                prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
                                request=request,response=response,reasoning=reasoning,answer=answer,
                                elapsed_s=time.monotonic()-start)
                            rows.append(record);done.add((label,row['id']))
                            write_rows(args.work/'outputs.jsonl',rows)
                            manifest.update(completed=len(rows),outputs_sha256=sha(args.work/'outputs.jsonl'))
                            write_json(manifest_path,manifest)
                            print(f'{len(rows)}/128 {label} {row["id"]}: {response["stop_type"]}, {response["tokens_predicted"]} tokens',flush=True)
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait()
        manifest['complete']=len(rows)==128
    except BaseException as error:
        manifest['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        manifest['completed']=len(rows)
        write_json(manifest_path,manifest)
        summarize(args.work,manifest)


if __name__=='__main__':
    main()
