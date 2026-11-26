"""Check the corrected chosen answers of the exp-004 pair review with the same detectors that built the pairs.

  python check_exp004_pair_fixes.py            (needs the Zeyrek venv; reads results-local/pair-review-labels.jsonl and pair-review-30.jsonl)

For each pair with a corrected answer: detector flags of the fix (unknown/English words, broken limits, loop, cut), word counts against
the rejected and the original chosen answer (the band of the pair builder is 0.85-1.15 against the rejected one), and how much of the
original chosen answer survived. Writes results-local/pair-fix-report.md for reading side by side.
"""
import difflib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/datasets'))
import tr_dpo_flags as F  # noqa: E402

EXP = ROOT / 'experiments/preference-rl/lfm3-1.7b/exp-004-dpo-onpolicy-turkish'
LOCAL = EXP / 'results-local'


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def main():
    prompts = {r['id']: r for r in read_jsonl(EXP / 'data/prompts-tr-dpo4.jsonl')}
    packet = {r['id']: r for r in read_jsonl(LOCAL / 'pair-review-30.jsonl')}
    labels = read_jsonl(LOCAL / 'pair-review-labels.jsonl')
    accept = {w.strip() for w in (EXP / 'data/accept-words.txt').read_text(encoding='utf-8').splitlines() if w.strip() and not w.startswith('#')}
    analyzer = F.nonword.Analyzer()
    out, table = [], []
    for n, lab in enumerate(labels, 1):
        fix = (lab.get('corrected_chosen') or '').strip()
        if not fix:
            continue
        p = packet[lab['id']]
        row = prompts[lab['id'].split('#')[0]]
        flags = F.flags_for(analyzer, row, fix, True, accept=accept)
        wf, wr, wc = len(F.words(fix)), len(F.words(p['rejected'])), len(F.words(p['chosen']))
        kept = difflib.SequenceMatcher(None, p['chosen'], fix).ratio()
        problems = [k for k in ('unfinished', 'empty', 'english_reply', 'loop', 'constraint', 'unknown_words', 'english_words') if flags[k]]
        table.append((n, lab['reason'], wf, wr, round(wf / max(wr, 1), 2), round(kept, 2), problems, flags['unknown_words'] + flags['english_words'], flags['constraint']))
        out.append(f"\n---\n## {n}. {lab['id']} ({lab['reason']})  fix words {wf}, rejected {wr}, ratio {wf / max(wr, 1):.2f}, original chosen {wc}, kept {kept:.2f}\n"
                   f"detector on the FIX: {problems or 'clean'} {flags['unknown_words']} {flags['english_words']} {flags['constraint']}\n\n"
                   f"**PROMPT**: {p['prompt']}\n\n**ORIGINAL CHOSEN**: {p['chosen']}\n\n**FIX**: {fix}\n\n**REJECTED**: {p['rejected']}\n")
    (LOCAL / 'pair-fix-report.md').write_text(f'# exp-004 fix check: {len(table)} corrected answers\n' + ''.join(out), encoding='utf-8')
    print(f'{len(table)} corrected answers -> {LOCAL / "pair-fix-report.md"}')
    for t in table:
        print(*t)


if __name__ == '__main__':
    main()
