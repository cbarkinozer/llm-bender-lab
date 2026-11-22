"""SFT core v01: verify sampled answers against each prompt's checker and report rates and lengths.

  python verify_lfm3_sft_samples.py --prompts P.jsonl --samples S.jsonl --output V.jsonl [--allow-exec]

Checkers: math -> final number equals gold (eval-v2 extractor); tool -> parsed calls equal the gold call (eval-v2 matcher);
code -> MBPP asserts pass. Code verification EXECUTES model-written code (subprocess, 10 s, 2 GB): pod only, --allow-exec.
A sample counts only if generation ended with EOS (not cut by the token budget) and, with thinking on, the thinking closed.
Output rows: {id, category, thinking, tokens:[...], verified:[bool...], reasons:[...]} plus a summary printed and saved next to it.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402
from lfm3_sft_constraints import check_constraints  # noqa: E402


def extract_code(answer):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', answer, flags=re.S | re.I)
    return blocks[-1] if blocks else answer


def run_mbpp(check, answer):
    program = (check['setup'] or '') + '\n' + extract_code(answer) + '\n\n' + '\n'.join(check['tests']) + '\n'
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


def verify(prompt, sample, allow_exec):
    if sample['finish_reason'] != 'eos':
        return False, 'no_eos'
    raw, thinking, check = sample['raw_output'], prompt['thinking'], prompt['check']
    answer, closed = scoring.split_thinking(raw, thinking)
    if closed is False:
        return False, 'unclosed_thinking'
    if check['type'] == 'number':
        res = scoring.score_math(raw, check['gold'], prompt['lang'], thinking)
        return bool(res['correct_any']), 'ok' if res['correct_any'] else 'wrong_number'
    if check['type'] == 'toolcall':
        res = scoring.score_toolcall(raw, check['gold_calls'], prompt['tools'], thinking)
        return bool(res['correct']), 'ok' if res['correct'] else res['error']
    if check['type'] == 'constraints':
        ok, failures = check_constraints(check['items'], answer)
        return ok, 'ok' if ok else 'constraint_' + failures[0].split()[0]
    if check['type'] == 'mbpp':
        if not allow_exec:
            return None, 'not_executed'
        ok = run_mbpp(check, answer)
        return ok, 'ok' if ok else 'tests_failed'
    raise ValueError(check['type'])


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompts', type=Path, required=True)
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-exec', action='store_true')
    args = parser.parse_args()
    prompts = {r['id']: r for r in (json.loads(s) for s in args.prompts.read_text(encoding='utf-8').split('\n') if s.strip())}
    cells = defaultdict(lambda: dict(groups=0, groups_any=0, samples=0, verified=0, tokens=[], tokens_ok=[], reasons=defaultdict(int)))
    with args.output.open('w', encoding='utf-8') as out:
        for line in args.samples.read_text(encoding='utf-8').split('\n'):
            if not line.strip():
                continue
            row = json.loads(line)
            prompt = prompts[row['id']]
            results = [verify(prompt, s, args.allow_exec) for s in row['samples']]
            cell = cells[(prompt['category'], 'on' if prompt['thinking'] else 'off')]
            cell['groups'] += 1
            cell['groups_any'] += any(r[0] for r in results)
            for sample, (ok, reason) in zip(row['samples'], results):
                cell['samples'] += 1
                cell['verified'] += bool(ok)
                cell['tokens'].append(sample['tokens'])
                if ok:
                    cell['tokens_ok'].append(sample['tokens'])
                cell['reasons'][reason] += 1
            out.write(json.dumps(dict(id=row['id'], category=prompt['category'], thinking=prompt['thinking'],
                                      tokens=[s['tokens'] for s in row['samples']],
                                      verified=[r[0] for r in results], reasons=[r[1] for r in results])) + '\n')
    summary = {}
    for (category, mode), c in sorted(cells.items()):
        summary[f'{category}/{mode}'] = dict(
            groups=c['groups'], groups_with_a_verified_sample=c['groups_any'],
            group_rate=round(c['groups_any'] / c['groups'], 3), sample_rate=round(c['verified'] / max(1, c['samples']), 3),
            tokens_median_all=statistics.median(c['tokens']), tokens_p90_all=pct(c['tokens'], .9),
            tokens_median_verified=statistics.median(c['tokens_ok']) if c['tokens_ok'] else None,
            tokens_p90_verified=pct(c['tokens_ok'], .9), reasons=dict(c['reasons']))
    args.output.with_suffix('.summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
