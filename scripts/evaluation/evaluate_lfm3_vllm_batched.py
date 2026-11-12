"""Versioned stratified CETVEL subset with continuous vLLM batching and guards."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import random


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--batch-size', type=int, default=4)
    p.add_argument('--repetition-penalty', type=float, default=1.15)
    p.add_argument('--temperature', type=float, default=0)
    p.add_argument('--top-k', type=int, default=-1)
    p.add_argument('--protocol-name', default='cetvel-stratified100-batched-rp115-v02')
    p.add_argument('--merged-model', type=Path)
    a = p.parse_args()
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import EngineArgs, LLMEngine, SamplingParams
    import torch
    cfg = json.loads((a.experiment_dir/'config-planned.json').read_text())
    model = cfg['model']
    packet = (a.experiment_dir/'data-local/questions-500.jsonl').read_bytes()
    digest = hashlib.sha256(packet).hexdigest()
    assert digest == cfg['historical_comparison']['questions_sha256']
    rows = [json.loads(s) for s in packet.decode().splitlines()]
    assert len(rows) == 500 and 0 < a.limit <= 500 and a.limit % 5 == 0
    assert 1 <= a.batch_size <= 8 and a.repetition_penalty >= 1
    if a.limit:
        tasks = list(dict.fromkeys(r['task'] for r in rows))
        rng = random.Random(3407)
        groups = [rng.sample([r for r in rows if r['task'] == t], a.limit//5) for t in tasks]
        rows = [r for g in zip(*groups) for r in g][:a.limit]
    tokenizer = AutoTokenizer.from_pretrained(model['repo'], revision=model['revision'])
    eos = GenerationConfig.from_pretrained(model['repo'],revision=model['revision']).eos_token_id
    eos = eos if isinstance(eos,list) else [eos]
    assert eos and all(isinstance(i,int) for i in eos)
    engine_args = dict(model=str(a.merged_model) if a.merged_model else model['repo'],
        tokenizer=model['repo'],tokenizer_revision=model['revision'],
        dtype='bfloat16',max_model_len=8192,gpu_memory_utilization=.75,
        enforce_eager=True,max_num_seqs=a.batch_size,seed=3407,trust_remote_code=True,
        generation_config='vllm',enable_prefix_caching=False)
    if not a.merged_model:
        engine_args.update(revision=model['revision'],code_revision=model['revision'])
    a.output_dir.mkdir(parents=True,exist_ok=False)
    manifest = dict(status='initializing',diagnostic=True,model=model,
        protocol=a.protocol_name, selected_ids=[r['id'] for r in rows],
        selection='Random(3407) sample equally per task, round-robin submission; selected before generation',
        merged_model=str(a.merged_model) if a.merged_model else None,
        questions_sha256=digest,expected_count=len(rows),count=0,seed=3407,
        engine_args=engine_args,eos_token_ids=eos,
        chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
        decoding=dict(temperature=a.temperature,top_k=a.top_k,top_p=1.0,repetition_penalty=a.repetition_penalty,max_new_tokens=4096,
            context_budget=8192,enable_thinking=False,ignore_eos=True,stop_token_ids=eos),
        packages={n:importlib.metadata.version(n) for n in ('torch','transformers','vllm')},
        gpu=torch.cuda.get_device_name())
    def save():
        (a.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    try:
        engine = LLMEngine.from_engine_args(EngineArgs(**engine_args))
        params = SamplingParams(temperature=a.temperature,top_k=a.top_k,top_p=1.0,repetition_penalty=a.repetition_penalty,max_tokens=4096,
            seed=3407,ignore_eos=True,stop_token_ids=eos,detokenize=True)
        manifest['status']='running';save()
        wall_start = time.perf_counter()
        pending = iter(rows)
        active = {}
        completed = set()
        exhausted = False
        with (a.output_dir/'answers.jsonl').open('w',encoding='utf-8') as out:
            while active or not exhausted:
                while len(active) < a.batch_size and not exhausted:
                    row = next(pending, None)
                    if row is None:
                        exhausted = True
                        break
                    prompt = tokenizer.apply_chat_template(row['messages'],tokenize=False,
                        add_generation_prompt=True,enable_thinking=False)
                    ids = tokenizer(prompt,add_special_tokens=False)['input_ids']
                    assert len(ids)+4096 <= 8192
                    rid = str(row['id'])
                    engine.add_request(rid,{'prompt_token_ids':ids},params)
                    active[rid] = dict(row=row,prompt=prompt,ids=ids,start=time.perf_counter(),last=None)
                if not active:
                    break
                if not engine.has_unfinished_requests():
                    raise RuntimeError('Engine empty while caller still has active requests')
                for item in engine.step():
                    if item.request_id in completed:
                        # Aborted requests may emit one final engine acknowledgement.
                        continue
                    if item.request_id not in active:
                        raise RuntimeError('Unexpected engine output ID')
                    active[item.request_id]['last'] = item
                for rid, state in list(active.items()):
                    last = state['last']
                    elapsed = time.perf_counter()-state['start']
                    if last is None:
                        if elapsed >= 180:
                            raise RuntimeError('Request timed out before any output')
                        continue
                    result = last.outputs[0]
                    tokens = list(result.token_ids)
                    guard = None
                    if not last.finished:
                        if len(tokens)>=128 and any(tokens[-w:]*4==tokens[-4*w:] for w in (8,16,32)):
                            guard = 'exact_loop'
                        if elapsed >= 180:
                            guard = 'timeout'
                    if not last.finished and not guard:
                        continue
                    if guard:
                        engine.abort_request(rid)
                    record = dict(state['row'],prediction=tokenizer.decode(tokens,skip_special_tokens=True),
                        raw_output=tokenizer.decode(tokens,skip_special_tokens=False),rendered_prompt=state['prompt'],
                        prompt_token_ids=state['ids'],generated_token_ids=tokens,generated_tokens=len(tokens),
                        generation_seconds=elapsed,hit_max_new_tokens=len(tokens)>=4096,
                        finish_reason=guard or ('eos' if result.stop_reason in eos else result.finish_reason),
                        engine_finish_reason=result.finish_reason,engine_stop_reason=result.stop_reason)
                    out.write(json.dumps(record,ensure_ascii=False)+'\n');out.flush()
                    del active[rid]
                    completed.add(rid)
                    manifest['count'] += 1
                    save()
                    print(f"{manifest['count']}/{len(rows)} {rid} {record['finish_reason']} {elapsed:.2f}s",flush=True)
        manifest['wall_seconds'] = time.perf_counter()-wall_start
        manifest['timing_note'] = 'Per-request generation_seconds overlap under batching; use wall_seconds for aggregate throughput.'
        manifest['status']='completed'
    except BaseException:
        manifest['status']='failed'
        raise
    finally:
        save()


if __name__ == '__main__':
    main()
