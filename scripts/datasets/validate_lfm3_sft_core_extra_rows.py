"""Validate hand-supplied extra SFT rows (for example email and letter writing) before they enter a pack (CPU, local).

  python validate_lfm3_sft_core_extra_rows.py ROWS.jsonl [--report REPORT.json]
Rows: {"id", "type", "prompt", "answer"}. Checks: format and unique ids; diacritics; no emoji, bracket placeholders, markdown tables
or headings; word range (40 to 160 unless the prompt states a limit); stated limits (words, sentences, bullets; digits or number
words) met by the answer; distinct answer openings and prompts; Zeyrek unknown-word rate of the answer; lexical overlap with every
protected eval set (including the 40 writing prompts) and with the pack prompts. Nothing is rewritten; the verdict is per row.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/datasets'))
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
import audit_lfm3_sft_core_leakage as leak  # noqa: E402
from lfm3_sft_constraints import count_bullets, count_sentences, count_words  # noqa: E402

NUMBER_WORDS = dict(bir=1, iki=2, üç=3, dört=4, beş=5, altı=6, yedi=7, sekiz=8, dokuz=9, on=10, yirmi=20, otuz=30, kırk=40, elli=50, altmış=60)
NUM = r'(\d+|' + '|'.join(NUMBER_WORDS) + r')'
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿️]')
TR_LETTERS = re.compile('[çğıöşüÇĞİÖŞÜ]')


def number(token):
    return int(token) if token.isdigit() else NUMBER_WORDS[token.lower()]


def stated_limits(prompt):
    out = []
    for m in re.finditer(r'en (?:fazla|çok) ' + NUM + r' kelime', prompt, re.I):
        out.append(('max_words', number(m.group(1))))
    for m in re.finditer(r'(?:tam(?: olarak)?|yalnızca|sadece) ' + NUM + r' cümle', prompt, re.I):
        out.append(('sentences', number(m.group(1))))
    for m in re.finditer(NUM + r' cümle(?:yle|lik)', prompt, re.I):
        out.append(('sentences', number(m.group(1))))
    for m in re.finditer(r'(?:tam(?: olarak)? ' + NUM + r' madde|' + NUM + r' maddelik)', prompt, re.I):
        out.append(('bullets', number(next(g for g in m.groups() if g))))
    return out


def check_limits(limits, answer):
    problems = []
    for kind, n in limits:
        got = dict(max_words=count_words(answer), sentences=count_sentences(answer), bullets=count_bullets(answer))[kind]
        if (kind == 'max_words' and got > n) or (kind != 'max_words' and got != n):
            problems.append(f'{kind}: asked {n}, got {got}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rows', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rows, errors = [], []
    for number_, line in enumerate(args.rows.read_text(encoding='utf-8').split('\n'), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f'line {number_}: invalid JSON ({e})')
            continue
        if set(r) != {'id', 'type', 'prompt', 'answer'} or not all(isinstance(v, str) and v.strip() for v in r.values()):
            errors.append(f'line {number_}: expected exactly id, type, prompt, answer as non-empty strings')
            continue
        rows.append(r)
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        errors.append('duplicate ids')
    from turkish_nonword_rate import Analyzer, tokens
    analyzer = Analyzer()
    sets = leak.protected_sets()
    indexes = {name: leak.build_index(items) for name, items in sets.items()}
    pack_prompts = [(r['id'], leak.user_text(r['prompt'])) for r in leak.read_jsonl(leak.CORE / 'pack-local/lfm3-base-v1/train.jsonl')]
    pack_index = leak.build_index([(i, [t]) for i, t in pack_prompts])
    openings, report_rows = {}, []
    for r in rows:
        problems, notes = [], []
        a, p = r['answer'], r['prompt']
        words = count_words(a)
        limits = stated_limits(p)
        if not TR_LETTERS.search(a) and words >= 20:
            problems.append('answer has no Turkish diacritics')
        if EMOJI.search(a) or EMOJI.search(p):
            problems.append('emoji')
        if re.search(r'\[[^\]]{1,40}\]', a):
            problems.append('bracket placeholder in the answer')
        if re.search(r'^\s*\|.*\|\s*$|^\s{0,3}#{1,6}\s|\*\*', a, re.M):
            problems.append('markdown table, heading or bold in the answer')
        if re.search(r'^\s*konu\s*:', a, re.I | re.M) and not re.search(r'konu', p, re.I):
            problems.append('"Konu:" line the prompt did not ask for')
        if not limits and not 40 <= words <= 160:
            problems.append(f'{words} words (range 40 to 160 without a stated limit)')
        problems += check_limits(limits, a)
        opening = ' '.join(re.findall(r'\w+', a.lower())[:4])
        if opening in openings:
            problems.append(f'same opening as {openings[opening]}')
        openings.setdefault(opening, r['id'])
        with contextlib.redirect_stdout(io.StringIO()):
            rate = analyzer.rate(tokens(a))
        if rate['candidate_token_rate'] > 0.04:
            problems.append(f'unknown-word candidate rate {rate["candidate_token_rate"]:.3f}')
        if rate['english_token_rate'] > 0.04:
            problems.append(f'English-token rate {rate["english_token_rate"]:.3f}')
        hits = {}
        for name, (t, ix, sh) in indexes.items():
            f = leak.flags_for(p, t, ix, sh)
            if f:
                hits[name] = {k: sorted(v) for k, v in f.items()}
        ph = leak.flags_for(p, *pack_index)
        if hits:
            problems.append('overlap with protected sets: ' + json.dumps(hits, ensure_ascii=False)[:200])
        if ph:
            notes.append('overlap with pack prompts: ' + ', '.join(sorted(ph)[:3]))
        report_rows.append(dict(id=r['id'], type=r['type'], words=words, limits=limits, unknown_candidate_rate=rate['candidate_token_rate'],
                                problems=problems, notes=notes, verdict='ok' if not problems else 'check'))
    for r1 in range(len(rows)):
        for r2 in range(r1 + 1, len(rows)):
            w1, w2 = set(re.findall(r'\w+', rows[r1]['prompt'].lower())), set(re.findall(r'\w+', rows[r2]['prompt'].lower()))
            if len(w1 & w2) / len(w1 | w2) > 0.6:
                errors.append(f'prompts {rows[r1]["id"]} and {rows[r2]["id"]} are very similar')
    result = dict(rows=len(rows), format_errors=errors, per_row=report_rows, ok=sum(x['verdict'] == 'ok' for x in report_rows))
    print(json.dumps(result, indent=1, ensure_ascii=False))
    if args.report:
        args.report.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
