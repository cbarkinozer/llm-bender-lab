"""SFT core v01: build the LFM3 pack (the model's own verified answers as training rows) and its report.

  python build_lfm3_sft_pack.py --prompts P.jsonl [P2.jsonl ...] --samples S.jsonl [...] --verified V.jsonl [...] \
      --output-dir D [--zeyrek]

Rows come out in the exp-016 prompt/completion format ({prompt, completion, chat_template_kwargs[, tools]}); thinking rows keep
the model's own reasoning in completion[0]['thinking'].
Selection per prompt: candidates are the verified samples (checker passed, EOS, thinking closed); Turkish answers must also pass
a language and unknown-word filter (Zeyrek, needs the scratch venv); one candidate is then chosen by a seeded hash, NOT by
length or score, so the pack keeps the model's natural answer lengths. Prompts without a candidate are dropped and counted
(math rows are never filled with the English answer: a Turkish prompt with an English reply would teach language drift).
Report: per category/language/thinking counts, drop reasons, length of kept vs all verified answers (drift check), math
survival by solution-step bucket (selection-bias check).
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_eval_v2_scoring as scoring  # noqa: E402
import lfm3_sft_core as core  # noqa: E402

CONTROL = ('<|im_end|>', '<|endoftext|>', '<|startoftext|>')
EN_STOP = {'the', 'and', 'is', 'of', 'to', 'in', 'that', 'it', 'for', 'with', 'as', 'was', 'are', 'this', 'be', 'you', 'have'}
TR_STOP = {'ve', 'bir', 'bu', 'için', 'ile', 'de', 'da', 'olarak', 'daha', 'çok', 'gibi', 'ama', 'olan', 'her', 'ne', 'kadar',
           'ise', 'veya', 'şu', 'o'}
TR_LETTERS = re.compile('[çğıöşüÇĞİÖŞÜ]')
WORD = re.compile(r"[A-Za-zçğıöşüÇĞİÖŞÜ]+")
CODE = re.compile(r'```.*?```|`[^`\n]*`|<tool_call>.*?</tool_call>', re.S)
MAX_TURKISH_CANDIDATE_RATE = 0.04   # human Turkish baseline (Belebele passages) is 1.8%
MAX_ENGLISH_TOKEN_RATE = 0.04       # baseline 0.4%; arm B had 4.3% in the writing probe
MAX_TOTAL_TOKENS = 8000             # train with max_length 8192 (exp-016's 4096 cut off long reasoning); prompt tokens estimated


def split_sample(raw, thinking):
    answer, closed = scoring.split_thinking(raw, thinking)
    reasoning = None
    if thinking:
        text = raw
        for token in CONTROL:
            text = text.replace(token, '')
        reasoning = text.rsplit(scoring.THINK_CLOSE, 1)[0].strip()
    return reasoning, answer.strip()


def prose(answer):
    return CODE.sub(' ', answer)


def language_ok(answer, lang, analyzer, check_unknown=True):
    """Return (ok, reason). Checks only prose outside code and tool calls, and only when there is enough of it.
    check_unknown=False skips the unknown-word limit (math answers repeat character names, which Zeyrek does not know)."""
    text = prose(answer)
    words = [w.lower() for w in WORD.findall(text)]
    if len(words) < 12:
        return True, 'short'
    en_share = sum(w in EN_STOP for w in words) / len(words)
    tr_share = sum(w in TR_STOP for w in words) / len(words)
    letters = sum(len(w) for w in words)
    diacritic = len(TR_LETTERS.findall(text)) / max(1, letters)
    if lang == 'tr':
        if en_share > 0.10 and tr_share < en_share:
            return False, 'english_reply'
        if analyzer is not None:
            from turkish_nonword_rate import tokens
            rate = analyzer.rate(tokens(text))
            if check_unknown and rate['candidate_token_rate'] > MAX_TURKISH_CANDIDATE_RATE:
                return False, 'unknown_words'
            if rate['english_token_rate'] > MAX_ENGLISH_TOKEN_RATE:
                return False, 'english_leak'
    else:
        if diacritic > 0.02 or (tr_share > 0.06 and tr_share > en_share):
            return False, 'turkish_reply_to_english'
    return True, 'ok'


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompts', type=Path, nargs='+', required=True)
    parser.add_argument('--samples', type=Path, nargs='+', required=True)
    parser.add_argument('--verified', type=Path, nargs='+', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--zeyrek', action='store_true', help='apply the unknown-word filter to Turkish answers')
    args = parser.parse_args()
    prompts = {}
    for path in args.prompts:
        for r in read_jsonl(path):
            prompts[r['id']] = r
    samples = {r['id']: r for path in args.samples for r in read_jsonl(path)}
    verified = {r['id']: r for path in args.verified for r in read_jsonl(path)}
    core_rows = {r['id']: r for r in core.load_core()}
    analyzer = None
    if args.zeyrek:
        from turkish_nonword_rate import Analyzer
        analyzer = Analyzer()

    kept, stats = [], defaultdict(Counter)
    lengths = defaultdict(lambda: dict(kept=[], verified=[]))
    survival = defaultdict(Counter)
    for pid, prompt in sorted(prompts.items()):
        if core_rows[prompt['core_id']]['split'] != 'train':
            continue  # the final test is never part of a pack
        cell = f'{prompt["category"]}/{prompt["lang"]}/{"on" if prompt["thinking"] else "off"}'
        stats[cell]['prompts'] += 1
        if prompt['id'] not in samples or prompt['id'] not in verified:
            stats[cell]['not_sampled'] += 1
            continue
        flags, row_samples = verified[pid]['verified'], samples[pid]['samples']
        good = [i for i, ok in enumerate(flags) if ok]
        stats[cell]['with_verified'] += bool(good)
        passed, reasons = [], Counter()
        for i in good:
            reasoning, answer = split_sample(row_samples[i]['raw_output'], prompt['thinking'])
            ok, reason = language_ok(answer, prompt['lang'], analyzer, check_unknown=prompt['category'] == 'tr_general')
            reasons[reason] += 1
            if ok:
                passed.append((i, reasoning, answer))
            lengths[cell]['verified'].append(row_samples[i]['tokens'])
        for reason, n in reasons.items():
            stats[cell][f'sample_{reason}'] += n
        core_row = core_rows[prompt['core_id']]
        if core_row['category'] == 'math':
            survival[core_row['step_bucket']]['groups'] += 1
            survival[core_row['step_bucket']][f'{prompt["lang"]}_kept'] += bool(passed)
        if not passed:
            stats[cell]['dropped_no_candidate'] += 1
            continue
        prompt_chars = sum(len(m['content']) for m in prompt['messages']) + len(json.dumps(prompt.get('tools') or []))
        fits = [p for p in passed if row_samples[p[0]]['tokens'] + prompt_chars / 3 <= MAX_TOTAL_TOKENS]
        if not fits:
            stats[cell]['dropped_too_long'] += 1
            continue
        index, reasoning, answer = min(fits, key=lambda p: core.rank(f'pick:{pid}:{p[0]}'))
        completion = dict(role='assistant', content=answer)
        if prompt['thinking']:
            completion['thinking'] = reasoning
        row = dict(id=pid, core_id=prompt['core_id'], category=prompt['category'], lang=prompt['lang'],
                   prompt=prompt['messages'], completion=[completion],
                   chat_template_kwargs=dict(enable_thinking=bool(prompt['thinking'])))
        if prompt.get('tools'):
            row['tools'] = prompt['tools']
        kept.append(row)
        stats[cell]['kept'] += 1
        lengths[cell]['kept'].append(row_samples[index]['tokens'])
    kept.sort(key=lambda r: core.rank(f'order:pack:{r["id"]}'))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'train.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in kept),
                                                 encoding='utf-8', newline='\n')
    drift = {}
    for cell, v in sorted(lengths.items()):
        if v['kept'] and v['verified']:
            drift[cell] = dict(kept_median=statistics.median(v['kept']), verified_median=statistics.median(v['verified']),
                               ratio=round(statistics.median(v['kept']) / max(1, statistics.median(v['verified'])), 3),
                               kept_p90=pct(v['kept'], .9), verified_p90=pct(v['verified'], .9), n_kept=len(v['kept']))
    report = dict(rows=len(kept), cells={k: dict(v) for k, v in sorted(stats.items())}, length_drift=drift,
                  math_survival_by_step_bucket={str(k): dict(v) for k, v in sorted(survival.items())},
                  zeyrek_filter=bool(args.zeyrek), thresholds=dict(candidate=MAX_TURKISH_CANDIDATE_RATE, english=MAX_ENGLISH_TOKEN_RATE,
                                                                    max_total_tokens=MAX_TOTAL_TOKENS))
    (args.output_dir / 'pack-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8',
                                                      newline='\n')
    print(json.dumps(dict(rows=len(kept), cells=report['cells'], length_drift=drift), indent=1)[:6000])


if __name__ == '__main__':
    main()
