"""Same pinned vLLM engine for base/F, explicit token prompts and request guards."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft'))
from evaluate_models import repeated_tail


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--probe-only', action='store_true')
    parser.add_argument('--experiment-dir', type=Path, default=HERE)
    args = parser.parse_args()
    assert not args.output_dir.exists(), 'Never overwrite outputs'
    experiment = args.experiment_dir.resolve()
    config = json.loads((experiment / 'config.json').read_text())
    for name, expected in config['adapter_hashes'].items():
        assert sha(args.adapter / name) == expected, ('Wrong F adapter', name)
    config.update(backend='vLLM', max_context_tokens=8192, batch_size=8,
                  vllm_version='0.30.0', enforce_eager=True, enable_prefix_caching=False,
                  gpu_memory_utilization=.85, language_model_only=True)
    questions = experiment / config.get('questions_file', 'data-v1/questions-100.jsonl')
    frozen = json.loads((experiment / 'data-v1/manifest.json').read_text())
    assert sha(questions) == frozen['questions_sha256'] and frozen['near_duplicate_candidates'] == 0
    from vllm import EngineArgs, LLMEngine, SamplingParams
    from vllm.lora.request import LoRARequest
    from transformers import AutoConfig, AutoTokenizer
    import torch
    tokenizer = AutoTokenizer.from_pretrained(config['model'], revision=config['revision'])
    hf_config = AutoConfig.from_pretrained(config['model'], revision=config['revision'])
    model_eos = hf_config.text_config.eos_token_id
    assert model_eos == 248044
    config.update(model_eos_token_id=model_eos, tokenizer_eos_token_id=tokenizer.eos_token_id)
    engine_args = dict(model=config['model'], revision=config['revision'], tokenizer_revision=config['revision'],
        dtype='bfloat16', max_model_len=8192, max_num_seqs=8, max_num_batched_tokens=8192,
        enable_lora=True, max_lora_rank=16, max_loras=1, gpu_memory_utilization=.85,
        enforce_eager=True, enable_prefix_caching=False, language_model_only=True,
        seed=config['seed'], generation_config='vllm')
    engine = LLMEngine.from_engine_args(EngineArgs(**engine_args))
    lora = LoRARequest('exp016-F-final40', 1, str(args.adapter))
    assert engine.add_lora(lora), 'F LoRA failed to load'
    args.output_dir.mkdir(parents=True)
    save(args.output_dir / 'engine-settings.json', engine_args)
    if args.probe_only:
        data = [dict(id='diagnostic-1', task='diagnostic', messages=[dict(role='user', content='Yalnızca sonucu yaz: 17 + 8 kaçtır?')]),
                dict(id='diagnostic-2', task='diagnostic', messages=[dict(role='user', content='Şu cümleyi İngilizceye çevir: Bugün hava açık.')])]
    else:
        data = [json.loads(line) for line in questions.read_text(encoding='utf-8').splitlines()]
        assert len(data) == config.get('expected_count', 100) == frozen['count']
    packages = {n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'vllm', 'peft')}
    template_hash = hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
    for arm in ('base', 'F'):
        folder = args.output_dir / arm
        folder.mkdir()
        (folder / 'chat_template.jinja').write_text(tokenizer.chat_template, encoding='utf-8')
        manifest = dict(status='running', count=0, arm=arm, config=config,
            questions_sha256=sha(questions), packages=packages, backend='vLLM', precision='BF16',
            adapter_hashes=config['adapter_hashes'] if arm == 'F' else {},
            chat_template_sha256=template_hash, eos_token_ids=[model_eos],
            probe_only=args.probe_only, device=torch.cuda.get_device_name(),
            source_hashes={path.name: sha(path) for path in [
                Path(__file__), experiment / 'config.json', HERE / 'score_pair.py',
                ROOT / 'scripts/evaluation/score_cetvel_generation.py',
                ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft/evaluate_models.py']})
        save(folder / 'manifest.json', manifest)
        params = SamplingParams(temperature=0, top_p=1, top_k=-1, repetition_penalty=1.05,
            max_tokens=256 if args.probe_only else 4096, seed=3407,
            # HF generation uses model EOS=endoftext, NOT tokenizer EOS=im_end.
            # Disable the renderer's implicit EOS so only the same model EOS stops us.
            stop_token_ids=[model_eos], ignore_eos=True)
        active, done, next_index = {}, {}, 0
        with (folder / 'partial-answers.jsonl').open('x', encoding='utf-8') as partial:
            while next_index < len(data) or active:
                while next_index < len(data) and len(active) < 8:
                    row = data[next_index]
                    ids = tokenizer.apply_chat_template(row['messages'], tokenize=True,
                        add_generation_prompt=True, enable_thinking=False, return_dict=False)
                    assert isinstance(ids, list) and all(isinstance(token, int) for token in ids)
                    assert len(ids) + params.max_tokens <= 8192, 'Never truncate input'
                    key = arm + '-' + row['id']
                    engine.add_request(key, dict(prompt_token_ids=ids), params,
                                       lora_request=lora if arm == 'F' else None)
                    # add_request returns an internal randomized ID; outputs use the EXTERNAL ID.
                    active[key] = dict(row=row, ids=ids, started=time.monotonic(), tokens=[])
                    next_index += 1
                outputs = engine.step()
                if not outputs and active and not engine.has_unfinished_requests():
                    raise RuntimeError('Engine finished but active IDs remain; request routing mismatch')
                for request in outputs:
                    key = request.request_id
                    if key not in active:
                        continue
                    item = active[key]
                    prediction = request.outputs[0]
                    item['tokens'] = list(prediction.token_ids)
                    guard = None
                    if len(item['tokens']) % 16 == 0 and repeated_tail(item['tokens']):
                        guard = 'repetition_guard'
                    if time.monotonic() - item['started'] > 180:
                        guard = guard or 'wall_time_guard'
                    if not request.finished and not guard:
                        continue
                    if guard and not request.finished:
                        engine.abort_request([key])
                    # Only the model EOS is configured as a stop token; no string stops.
                    native = request.finished and prediction.finish_reason == 'stop' and prediction.stop_reason == model_eos
                    result = dict(item['row'], raw_output=tokenizer.decode(item['tokens'], skip_special_tokens=True),
                        prompt_token_ids=item['ids'], output_token_ids=item['tokens'],
                        generated_tokens=len(item['tokens']),
                        rendered_prompt=tokenizer.apply_chat_template(item['row']['messages'], tokenize=False,
                            add_generation_prompt=True, enable_thinking=False),
                        native_eos=native, hit_max_new_tokens=prediction.finish_reason == 'length',
                        engine_finish_reason=prediction.finish_reason, engine_stop_reason=prediction.stop_reason,
                        finish_reason='native_eos' if native else guard or (
                            'length_limit' if prediction.finish_reason == 'length' else 'unexpected_stop'),
                        latency_seconds=time.monotonic() - item['started'])
                    done[result['id']] = result
                    partial.write(json.dumps(result, ensure_ascii=False) + '\n')
                    partial.flush()
                    del active[key]
                    print(arm, result['id'], result['generated_tokens'], result['finish_reason'], flush=True)
                    save(args.output_dir / 'progress.json', dict(arm=arm, completed=len(done), total=len(data)))
        with (folder / 'answers.jsonl').open('x', encoding='utf-8') as output:
            for row in data:
                output.write(json.dumps(done[row['id']], ensure_ascii=False) + '\n')
        manifest.update(status='completed', count=len(done),
            native_eos_count=sum(r['native_eos'] for r in done.values()),
            incomplete_ids=[r['id'] for r in done.values() if not r['native_eos']],
            answers_sha256=sha(folder / 'answers.jsonl'))
        save(folder / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
