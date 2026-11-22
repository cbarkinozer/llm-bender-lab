"""English guard check for LFM3 variants: IFEval (instruction following) and HumanEval (coding). GPU pod only.

  prepare: python lfm3_guard_eval.py prepare --data-dir D                 pinned downloads, IFEval subset, checksums
  run:     python lfm3_guard_eval.py run --name N --output-dir O [--model M] [--limit K]   both thinking modes, one model load
  score:   python lfm3_guard_eval.py score --run-dir O --vendor V --data-dir D --allow-exec
  compare: python lfm3_guard_eval.py compare --base O1 --candidate O2
HumanEval scoring EXECUTES model-written code (subprocess, 10 s timeout, memory limit): run it only on the disposable pod.
IFEval scoring uses Google's instruction_following_eval code (Apache-2.0) fetched at a pinned commit into --vendor.
Presets: model-card general (T 0.1, top_k 50, rp 1.1), seed 3407, one sample per item; pre-registered rule in
experiments/turkish-capability/lfm3-1.7b/exp-018-english-guard/README.md.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = ROOT / 'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline/config-planned.json'
SOURCES = {
    'ifeval': 'https://huggingface.co/datasets/google/IFEval/resolve/966cd89545d6b6acfd7638bc708b98261ca58e84/ifeval_input_data.jsonl',
    'humaneval': 'https://huggingface.co/datasets/openai/openai_humaneval/resolve/7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544/'
                 'openai_humaneval/test-00000-of-00001.parquet',
}
IFEVAL_SUBSET = 270
PRESET = dict(temperature=0.1, top_p=1.0, top_k=50, repetition_penalty=1.1)
MAX_NEW = {'off': 1536, 'on': 6144}
MAX_MODEL_LEN = 12288
HE_PROMPT = ('Complete the following Python function. Reply with the complete function in one ```python code block and '
             'nothing else.\n\n```python\n{prompt}\n```')
CELLS = [('ifeval_strict', 'off'), ('ifeval_strict', 'on'), ('humaneval', 'off'), ('humaneval', 'on')]


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def cmd_prepare(args):
    args.data_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in SOURCES.items():
        blob = urllib.request.urlopen(url).read()
        manifest[name] = dict(url=url, bytes=len(blob), sha256=sha(blob))
        (args.data_dir / f'{name}-raw{Path(url).suffix}').write_bytes(blob)
    ifeval = [json.loads(x) for x in (args.data_dir / 'ifeval-raw.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(ifeval) == 541, len(ifeval)
    subset = sorted(random.Random(3407).sample(range(len(ifeval)), IFEVAL_SUBSET))
    (args.data_dir / 'ifeval.jsonl').write_text('\n'.join(json.dumps(ifeval[i]) for i in subset) + '\n', encoding='utf-8')
    rest = [i for i in range(len(ifeval)) if i not in set(subset)]
    (args.data_dir / 'ifeval-rest.jsonl').write_text('\n'.join(json.dumps(ifeval[i]) for i in rest) + '\n', encoding='utf-8')
    import pyarrow.parquet as pq
    rows = pq.read_table(args.data_dir / 'humaneval-raw.parquet').to_pylist()
    assert len(rows) == 164, len(rows)
    (args.data_dir / 'humaneval.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n', encoding='utf-8')
    manifest['ifeval_subset'] = dict(size=IFEVAL_SUBSET, seed=3407, indices=subset)
    (args.data_dir / 'sources.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print('prepared', {k: v.get('sha256', '')[:12] for k, v in manifest.items()})


def load_items(data_dir, limit=None, ifeval_file='ifeval.jsonl'):
    ife = [json.loads(x) for x in (data_dir / ifeval_file).read_text(encoding='utf-8').splitlines()]
    he = [json.loads(x) for x in (data_dir / 'humaneval.jsonl').read_text(encoding='utf-8').splitlines()]
    return (ife[:limit], he[:limit]) if limit else (ife, he)


def cmd_run(args):
    import torch
    from transformers import AutoTokenizer, GenerationConfig
    from vllm import LLM, SamplingParams

    base = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))['model']
    ife, he = load_items(args.data_dir, args.limit, args.ifeval_file)
    wanted = args.tasks.split(',')
    tasks = ([('ifeval', f'ifeval-{r["key"]}', r['prompt']) for r in ife] if 'ifeval' in wanted else []) + \
            ([('humaneval', r['task_id'].replace('/', '-'), HE_PROMPT.format(prompt=r['prompt'].rstrip())) for r in he]
             if 'humaneval' in wanted else [])
    tokenizer = AutoTokenizer.from_pretrained(base['repo'], revision=base['revision'])
    eos = GenerationConfig.from_pretrained(base['repo'], revision=base['revision']).eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    model_id = args.model or base['repo']
    engine_args = dict(model=model_id, tokenizer=base['repo'], tokenizer_revision=base['revision'], dtype='bfloat16',
                       max_model_len=MAX_MODEL_LEN, gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=96,
                       seed=3407, trust_remote_code=True, generation_config='vllm', enable_prefix_caching=False)
    if not args.model:
        engine_args.update(revision=base['revision'], code_revision=base['revision'])
    args.output_dir.mkdir(parents=True, exist_ok=False)
    run = dict(name=args.name, model=model_id, base_model=base, preset=PRESET, max_new_tokens=MAX_NEW, limit=args.limit,
               tasks=args.tasks, modes=args.modes, ifeval_file=args.ifeval_file,
               sources=json.loads((args.data_dir / 'sources.json').read_text(encoding='utf-8')), engine_args=engine_args,
               script_sha256=sha(Path(__file__).read_bytes()), gpu=torch.cuda.get_device_name(), started=time.strftime('%FT%T%z'))
    llm = LLM(**engine_args)
    jobs = []
    for mode in args.modes.split(','):
        for task, item_id, user in tasks:
            text = tokenizer.apply_chat_template([dict(role='user', content=user)], tokenize=False,
                                                 add_generation_prompt=True, enable_thinking=(mode == 'on'))
            assert text.endswith('<think>' if mode == 'on' else '<think></think>'), text[-40:]
            ids = tokenizer(text, add_special_tokens=False)['input_ids']
            assert len(ids) + MAX_NEW[mode] <= MAX_MODEL_LEN, item_id
            jobs.append(dict(task=task, id=item_id, mode=mode, ids=ids))
    started = time.perf_counter()
    outs = llm.generate([dict(prompt_token_ids=j['ids']) for j in jobs],
                        [SamplingParams(max_tokens=MAX_NEW[j['mode']], seed=3407, stop_token_ids=eos, ignore_eos=True,
                                        detokenize=False, **PRESET) for j in jobs])
    with (args.output_dir / 'answers.jsonl').open('w', encoding='utf-8') as f:
        for j, out in zip(jobs, outs):
            res = out.outputs[0]
            tokens = list(res.token_ids)
            f.write(json.dumps(dict(
                task=j['task'], id=j['id'], thinking=j['mode'], raw_output=tokenizer.decode(tokens, skip_special_tokens=False),
                generated_tokens=len(tokens), finish_reason='eos' if res.finish_reason == 'stop' else res.finish_reason,
                hit_max_new_tokens=len(tokens) >= MAX_NEW[j['mode']]), ensure_ascii=False) + '\n')
    run.update(wall_seconds=round(time.perf_counter() - started, 1), generations=len(jobs), finished=time.strftime('%FT%T%z'))
    (args.output_dir / 'run-manifest.json').write_text(json.dumps(run, indent=1) + '\n', encoding='utf-8')
    print(f'done {len(jobs)} generations in {run["wall_seconds"]}s', flush=True)


def visible(raw, thinking):
    text = raw
    for t in ('<|im_end|>', '<|endoftext|>', '<|startoftext|>'):
        text = text.replace(t, '')
    if thinking == 'on':
        return text.rsplit('</think>', 1)[1].strip() if '</think>' in text else None  # unclosed thinking = no answer
    return text.rsplit('</think>', 1)[-1].strip()


def extract_code(answer):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', answer, flags=re.S | re.I)
    return blocks[-1] if blocks else answer


def run_humaneval(row, answer):
    code = extract_code(answer)
    imports = '\n'.join(x for x in row['prompt'].splitlines() if x.startswith(('import ', 'from ')))
    program = (imports + '\n' + code) if f'def {row["entry_point"]}(' in code else (row['prompt'] + code)
    program += f'\n\n{row["test"]}\n\ncheck({row["entry_point"]})\n'
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / 'candidate.py'
        script.write_text(program, encoding='utf-8')
        try:
            import resource

            def limits():
                resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
            done = subprocess.run([sys.executable, '-I', str(script)], cwd=tmp, capture_output=True, timeout=10,
                                  preexec_fn=limits)
            return done.returncode == 0
        except subprocess.TimeoutExpired:
            return False


def cmd_score(args):
    if not args.allow_exec:
        raise SystemExit('HumanEval scoring executes model-written code; pass --allow-exec on the disposable pod only')
    sys.path.insert(0, str(args.vendor))
    from instruction_following_eval import evaluation_lib
    ife, he = load_items(args.data_dir, ifeval_file=args.ifeval_file)
    ife_by = {f'ifeval-{r["key"]}': r for r in ife}
    he_by = {r['task_id'].replace('/', '-'): r for r in he}
    rows = []
    for line in (args.run_dir / 'answers.jsonl').read_text(encoding='utf-8').splitlines():
        a = json.loads(line)
        answer = visible(a['raw_output'], a['thinking'])
        if a['task'] == 'ifeval':
            r = ife_by[a['id']]
            inp = evaluation_lib.InputExample(key=r['key'], instruction_id_list=r['instruction_id_list'], prompt=r['prompt'],
                                              kwargs=r['kwargs'])
            text = answer or ''
            strict = evaluation_lib.test_instruction_following_strict(inp, {r['prompt']: text})
            loose = evaluation_lib.test_instruction_following_loose(inp, {r['prompt']: text})
            rows.append(dict(task='ifeval', id=a['id'], thinking=a['thinking'], ifeval_strict=bool(strict.follow_all_instructions),
                             ifeval_loose=bool(loose.follow_all_instructions), answered=answer is not None,
                             tokens=a['generated_tokens'], hit_max=a['hit_max_new_tokens']))
        else:
            r = he_by[a['id']]
            ok = bool(answer) and run_humaneval(r, answer)
            rows.append(dict(task='humaneval', id=a['id'], thinking=a['thinking'], humaneval=ok, answered=answer is not None,
                             tokens=a['generated_tokens'], hit_max=a['hit_max_new_tokens']))
    (args.run_dir / 'scores.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n', encoding='utf-8')
    summary = {}
    for metric, task in (('ifeval_strict', 'ifeval'), ('ifeval_loose', 'ifeval'), ('humaneval', 'humaneval')):
        for mode in ('off', 'on'):
            sel = [r for r in rows if r['task'] == task and r['thinking'] == mode]
            if not sel:
                continue
            summary[f'{metric}|{mode}'] = dict(n=len(sel), accuracy=round(sum(r[metric] for r in sel) / len(sel), 4),
                                               answered=round(sum(r['answered'] for r in sel) / len(sel), 4),
                                               hit_max=round(sum(r['hit_max'] for r in sel) / len(sel), 4),
                                               mean_tokens=round(statistics.mean(r['tokens'] for r in sel), 1))
    (args.run_dir / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    for k, v in summary.items():
        print(k, v)


def verdict(delta, lo):
    if delta >= -0.05 and lo >= -0.10:
        return 'PASS'
    return 'FAIL' if delta < -0.10 else 'AMBIGUOUS'


def cmd_compare(args):
    def per_item(run_dirs):
        out = {}
        for run_dir in run_dirs:
            for line in (run_dir / 'scores.jsonl').read_text(encoding='utf-8').splitlines():
                r = json.loads(line)
                for metric in ('ifeval_strict', 'ifeval_loose', 'humaneval'):
                    if metric in r:
                        key = (metric, r['thinking'], r['id'])
                        assert key not in out, f'duplicate item {key}'
                        out[key] = float(r[metric])
        return out
    a, b = per_item(args.base), per_item(args.candidate)
    result = {}
    for metric, mode in CELLS + [('ifeval_loose', 'off'), ('ifeval_loose', 'on')]:
        keys = sorted(k for k in a if k[0] == metric and k[1] == mode and k in b)
        if not keys:
            continue
        diffs = [b[k] - a[k] for k in keys]
        rng = random.Random(3407)
        means = sorted(statistics.mean(diffs[rng.randrange(len(diffs))] for _ in diffs) for _ in range(4000))
        delta, lo, hi = statistics.mean(diffs), means[100], means[3899]
        cell = dict(n=len(keys), base=round(statistics.mean(a[k] for k in keys), 4), candidate=round(statistics.mean(b[k] for k in keys), 4),
                    delta=round(delta, 4), lo=round(lo, 4), hi=round(hi, 4))
        if (metric, mode) in CELLS:
            cell['verdict'] = verdict(delta, lo)
        result[f'{metric}|{mode}'] = cell
        print(metric, mode, cell)
    verdicts = [v['verdict'] for v in result.values() if 'verdict' in v]
    result['guard'] = 'PASS' if all(v == 'PASS' for v in verdicts) else ('FAIL' if 'FAIL' in verdicts else 'AMBIGUOUS')
    print('guard:', result['guard'])
    (args.candidate[0] / args.out_name).write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--data-dir', type=Path, required=True)
    p.set_defaults(func=cmd_prepare)
    p = sub.add_parser('run')
    p.add_argument('--name', required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--data-dir', type=Path, required=True)
    p.add_argument('--model')
    p.add_argument('--limit', type=int)
    p.add_argument('--tasks', default='ifeval,humaneval')
    p.add_argument('--modes', default='off,on')
    p.add_argument('--ifeval-file', default='ifeval.jsonl', help="'ifeval-rest.jsonl' = the 271 prompts outside the subset")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser('score')
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--vendor', type=Path, required=True)
    p.add_argument('--data-dir', type=Path, required=True)
    p.add_argument('--allow-exec', action='store_true')
    p.add_argument('--ifeval-file', default='ifeval.jsonl')
    p.set_defaults(func=cmd_score)
    p = sub.add_parser('compare')
    p.add_argument('--base', type=Path, action='append', required=True, help='repeatable: runs merged item by item')
    p.add_argument('--candidate', type=Path, action='append', required=True)
    p.add_argument('--out-name', default='compare-vs-base.json')
    p.set_defaults(func=cmd_compare)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
