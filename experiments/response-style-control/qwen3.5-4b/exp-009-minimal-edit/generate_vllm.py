"""Offline vLLM drafts; frozen inputs, native termination, no training or W&B."""
import argparse
import importlib.metadata
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from generate_base import HERE, git_info, json_file, sha256, validate_inputs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output-dir', type=Path)
    p.add_argument('--ids')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    config_path = HERE / 'generation-config.json'
    cfg, dataset, rows = validate_inputs(config_path)
    if args.ids:
        selected = args.ids.split(',')
        if len(set(selected)) != len(selected) or not set(selected) <= {r['id'] for r in rows}:
            raise ValueError('Unknown or duplicate IDs')
        rows = [r for r in rows if r['id'] in selected]
    if args.dry_run:
        print(json.dumps({'validated_rows': len(rows), 'backend': 'vllm'}))
        return
    if args.output_dir is None:
        raise ValueError('--output-dir required')
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(status='initializing', config=cfg, git=git_info(), argv=sys.argv,
                    python=platform.python_version(), created_at=datetime.now(timezone.utc).isoformat(),
                    dataset_sha256=sha256(dataset), config_sha256=sha256(config_path),
                    entrypoint_sha256=sha256(Path(__file__)), selected_ids=[r['id'] for r in rows])
    json_file(out / 'run-manifest.json', manifest)
    try:
        import torch
        from transformers import AutoTokenizer, GenerationConfig
        from vllm import LLM, SamplingParams
        from vllm.transformers_utils.config import get_config
        model = cfg['model']
        tokenizer = AutoTokenizer.from_pretrained(model['name'], revision=model['tokenizer_revision'])
        mc = get_config(model['name'], trust_remote_code=False, revision=model['revision'])
        try:
            gc = GenerationConfig.from_pretrained(model['name'], revision=model['revision'])
        except OSError as error:
            if 'generation_config.json' not in str(error):
                raise
            gc = GenerationConfig.from_model_config(mc)
        native = gc.eos_token_id or tokenizer.eos_token_id
        eos = native if isinstance(native, list) else [native]
        if not eos or any(not isinstance(i, int) for i in eos):
            raise ValueError('Missing native stop tokens')
        engine = dict(model=model['name'], revision=model['revision'], tokenizer_revision=model['tokenizer_revision'],
                      dtype='bfloat16', max_model_len=model['context_tokens'], seed=cfg['generation']['seed'],
                      gpu_memory_utilization=0.85, max_num_seqs=1, enforce_eager=True,
                      enable_prefix_caching=False, limit_mm_per_prompt={'image': 0, 'video': 0},
                      generation_config='vllm')
        manifest.update(backend='vllm', engine=engine, native_eos_ids=eos,
                        chat_template=tokenizer.chat_template,
                        packages={n: importlib.metadata.version(n) for n in ['vllm', 'torch', 'transformers', 'tokenizers']},
                        hardware=dict(gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda))
        json_file(out / 'effective-model-config.json', mc.to_dict())
        json_file(out / 'native-generation-config.json', gc.to_dict())
        json_file(out / 'run-manifest.json', manifest)
        llm = LLM(**engine)
        manifest['status'] = 'generating'
        json_file(out / 'run-manifest.json', manifest)
        incomplete = []
        with (out / 'attempts.jsonl').open('x', encoding='utf-8') as af, (out / 'drafts.jsonl').open('x', encoding='utf-8') as df:
            for row in rows:
                rendered = tokenizer.apply_chat_template(row['messages'], tokenize=False, add_generation_prompt=True, enable_thinking=False)
                prompt_ids = tokenizer.encode(rendered, add_special_tokens=False)
                if len(prompt_ids) + cfg['generation']['output_token_budgets'][-1] > model['context_tokens']:
                    raise ValueError('Context overflow; input truncation forbidden')
                for attempt, budget in enumerate(cfg['generation']['output_token_budgets'], 1):
                    params = SamplingParams(temperature=0, top_p=1, top_k=-1, repetition_penalty=1,
                                            max_tokens=budget, seed=cfg['generation']['seed'],
                                            stop_token_ids=eos, ignore_eos=False, skip_special_tokens=True)
                    started = time.monotonic()
                    result = llm.generate([{'prompt_token_ids': prompt_ids}], params, use_tqdm=False)[0].outputs[0]
                    ids = list(result.token_ids)
                    native_stop = result.finish_reason == 'stop' and (result.stop_reason in eos or
                                  (result.stop_reason is None and (tokenizer.eos_token_id in eos)))
                    finish = 'native_eos' if native_stop else ('length_limit' if result.finish_reason == 'length' else 'unexpected_stop')
                    latest = dict(id=row['id'], split=row['split'], category=row['category'], dataset_version=row['dataset_version'],
                                  input_messages_sha256=row['input_messages_sha256'], rendered_prompt=rendered,
                                  input_tokens=len(prompt_ids), output_tokens=len(ids), generated_token_ids=ids,
                                  output=result.text, raw_output_with_special_tokens=tokenizer.decode(ids, skip_special_tokens=False),
                                  finish_reason=finish, engine_finish_reason=result.finish_reason, engine_stop_reason=result.stop_reason,
                                  attempt=attempt, max_new_tokens=budget, elapsed_seconds=time.monotonic()-started)
                    af.write(json.dumps(latest, ensure_ascii=False)+'\n'); af.flush()
                    print(f"{row['id']} {finish} tokens={len(ids)} stop={result.stop_reason}", flush=True)
                    if finish != 'length_limit':
                        break
                latest['review_eligible'] = finish == 'native_eos' and bool(latest['output'].strip())
                df.write(json.dumps(latest, ensure_ascii=False)+'\n'); df.flush()
                if not latest['review_eligible']:
                    incomplete.append(row['id'])
        manifest.update(status='completed' if not incomplete else 'incomplete', incomplete_ids=incomplete,
                        drafts_sha256=sha256(out/'drafts.jsonl'), attempts_sha256=sha256(out/'attempts.jsonl'),
                        finished_at=datetime.now(timezone.utc).isoformat())
        json_file(out/'run-manifest.json', manifest)
        if incomplete:
            raise RuntimeError(f'Incomplete drafts: {incomplete}')
    except Exception as error:
        manifest.update(status='failed', error=str(error))
        json_file(out/'run-manifest.json', manifest)
        raise


if __name__ == '__main__':
    main()
