"""Detectors, editing worksheet, edit validator and pair builder for the Turkish answer-quality DPO data (preference-rl exp-003).

  python tr_dpo_flags.py flag      --prompts P --answers A --out DIR                  flags for every sampled answer
  python tr_dpo_flags.py worksheet --prompts P --answers A --flags F --out DIR        the answers an editor should repair
  python tr_dpo_flags.py validate  --worksheet W [--out DIR]                          checks the edits (does not change them)
  python tr_dpo_flags.py pairs     --worksheet W --out DIR                            rejected = model answer, chosen = edit
Needs `pip install zeyrek wordfreq` (run it in a venv). The detectors are an aid, not the truth: Zeyrek misses real words (names,
loanwords) and cannot see a wrong word that looks valid (for example "suyi"), nor an answer that does the wrong task. The editor
judges those; the validator only enforces what can be counted (size of the edit, constraints, ending, flagged words).
"""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
import lfm3_sft_constraints as atlas_constraints  # noqa: E402
import turkish_nonword_rate as nonword  # noqa: E402

WORD = re.compile(r"[\wçğıöşüÇĞİÖŞÜ'’-]+")
BULLET = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+', re.M)
ENGLISH_STOP = {'the', 'and', 'is', 'are', 'to', 'of', 'that', 'this', 'with', 'for', 'you', 'your', 'it', 'in', 'on', 'be', 'have', 'not'}
WEIGHTS = dict(unfinished=3, constraint=3, loop=3, english_reply=4, empty=4)
HOLDOUT_PERCENT = 15
COMMON_ZIPF = 3.0  # wordfreq 'tr' Zipf value from which a word form counts as real
MAX_EDIT_RATIO = 0.25
LENGTH_BAND = (0.85, 1.15)
SHORT_ANSWER_WORDS = 20  # below this the length band is replaced by +-5 words


def read_jsonl(path):
    """One JSON row per newline (str.splitlines would also split on U+2028 inside strings)."""
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8', newline='\n')


def visible(raw):
    return raw.replace('<|im_end|>', '').strip()


def words(text):
    return WORD.findall(text)


def count_sentences(text):
    text = re.sub(r'\d+[.,]\d+', 'N', text)
    return len([s for s in re.split(r'(?<=[.!?…])\s+', text.strip()) if re.search(r'\w', s)])


def constraint_failures(prompt_row, text):
    """Countable constraints: Atlas items (lfm3_sft_constraints) or the writing-probe spec of the template prompts."""
    check = prompt_row.get('check')
    if not check:
        return []
    if 'items' in check:
        return list(atlas_constraints.check_constraints(check['items'], text)[1])
    out = []
    if 'max_words' in check and len(text.split()) > check['max_words']:
        out.append(f"max_words {check['max_words']}: {len(text.split())} words")
    if 'exact_sentences' in check and count_sentences(text) != check['exact_sentences']:
        out.append(f"exact_sentences {check['exact_sentences']}: {count_sentences(text)} sentences")
    if 'bullets' in check and len(BULLET.findall(text)) != check['bullets']:
        out.append(f"bullets {check['bullets']}: {len(BULLET.findall(text))} bullets")
    for word in check.get('must_include', []):
        if word.lower() not in text.lower():
            out.append(f'must_include {word}')
    return out


def has_loop(text):
    # Repeated equation terms are expected in worked calculations.
    text = re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)', ' ', text, flags=re.S)
    ws = [w.lower() for w in words(text)]
    grams = Counter(tuple(ws[i:i + 4]) for i in range(len(ws) - 3))
    sentences = Counter(s.strip().lower() for s in re.split(r'(?<=[.!?…])\s+', text) if len(s.split()) >= 4)
    return any(c >= 3 for c in grams.values()) or any(c >= 2 for c in sentences.values())


def is_known(analyzer, word):
    """Zeyrek knows it, or it is a frequent Turkish word form (Zeyrek is flaky on some common forms such as 'olabilir')."""
    from wordfreq import zipf_frequency
    return analyzer.known(word) or zipf_frequency(word, 'tr') >= COMMON_ZIPF


def flags_for(analyzer, prompt_row, text, finished, accept=()):
    """Flag dict for one answer. `accept` are words an editor verified as real (kept out of the unknown-word list)."""
    prompt_words = set(nonword.tokens(prompt_row['prompt']))
    lexical_text = re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)', ' ', text, flags=re.S)
    own = [w for w in nonword.tokens(lexical_text) if prompt_row['kind'] == 'translate' or w not in prompt_words]
    types = Counter(own)
    unknown = [w for w in types if w not in accept and not is_known(analyzer, w)]
    english = [w for w in unknown if analyzer.is_english(w)]
    invented = [w for w in unknown if w not in english]
    reply = text
    if prompt_row['kind'] == 'translate':
        # A quoted copy of the supplied English sentence is allowed.
        for quoted in re.findall(r'"([^"\n]+)"|“([^”\n]+)”', prompt_row['prompt']):
            source = next(s for s in quoted if s)
            reply = reply.replace(source, '')
    lower = [w.lower() for w in words(reply)]
    stop_share = sum(w in ENGLISH_STOP for w in lower) / max(1, len(lower))
    flags: dict = dict(
        unfinished=not finished,
        empty=len(words(text)) < 3,
        constraint=constraint_failures(prompt_row, text),
        loop=has_loop(text),
        english_reply=len(lower) >= 8 and stop_share > 0.15,
        unknown_words=sorted(invented),
        english_words=sorted(english),
    )
    severity = sum(WEIGHTS[k] for k in WEIGHTS if flags[k] and k != 'constraint') + (WEIGHTS['constraint'] if flags['constraint'] else 0)
    severity += min(len(invented), 4) + min(len(english), 3)
    flags['severity'] = severity
    return flags


def describe(flags):
    parts = []
    if flags['unfinished']:
        parts.append('answer was cut at the token cap (no end token)')
    if flags['empty']:
        parts.append('empty or almost empty')
    if flags['english_reply']:
        parts.append('looks English')
    if flags['loop']:
        parts.append('repeats itself')
    parts += [f'constraint: {c}' for c in flags['constraint']]
    if flags['unknown_words']:
        parts.append('words the analyzer does not know: ' + ', '.join(flags['unknown_words']))
    if flags['english_words']:
        parts.append('English words in a Turkish answer: ' + ', '.join(flags['english_words']))
    return parts


def load_inputs(prompts_path, answers_path):
    prompts = {r['id']: r for r in read_jsonl(prompts_path)}
    answers = read_jsonl(answers_path)
    for a in answers:
        assert a['id'] in prompts, f"answer for unknown prompt {a['id']}"
    return prompts, answers


def cmd_flag(args):
    prompts, answers = load_inputs(args.prompts, args.answers)
    analyzer = nonword.Analyzer()
    accept = {w for path in args.accept_from or [] for r in read_jsonl(path) for w in (r.get('accept_words') or [])}
    if args.accept_words:
        accept |= {w.strip() for w in args.accept_words.read_text(encoding='utf-8').splitlines() if w.strip() and not w.startswith('#')}
    out = []
    for a in answers:
        p = prompts[a['id']]
        text = visible(a['raw_output'])
        out.append(dict(id=a['id'], sample=a['sample'], kind=p['kind'], source=p['source'], words=len(words(text)),
                        **flags_for(analyzer, p, text, a['finish_reason'] == 'eos', accept=accept)))
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / 'flags.jsonl', out)
    by_flag = {k: sum(bool(r[k]) for r in out) for k in ('unfinished', 'empty', 'english_reply', 'loop', 'constraint', 'unknown_words', 'english_words')}
    by_kind = {}
    for r in out:
        d = by_kind.setdefault(r['kind'], dict(answers=0, flagged=0))
        d['answers'] += 1
        d['flagged'] += r['severity'] > 0
    prompts_flagged = len({r['id'] for r in out if r['severity'] > 0})
    summary = dict(answers=len(out), prompts=len(prompts), prompts_with_a_flagged_answer=prompts_flagged, answers_by_flag=by_flag,
                   by_kind=by_kind, answers_sha256=hashlib.sha256(Path(args.answers).read_bytes()).hexdigest())
    (args.out / 'flags-summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1, ensure_ascii=False))


def is_holdout(prompt_id):
    """Seeded 15% of the prompts, by hash of the id: never edited, never trained on, used only to measure."""
    return int(hashlib.sha256(prompt_id.encode('utf-8')).hexdigest()[:8], 16) % 100 < HOLDOUT_PERCENT


def cmd_worksheet(args):
    prompts, answers = load_inputs(args.prompts, args.answers)
    holdout = sorted(pid for pid in prompts if is_holdout(pid))
    answers = [a for a in answers if not is_holdout(a['id'])]
    flags = {(r['id'], r['sample']): r for r in read_jsonl(args.flags)}
    done = set()
    seen = set()
    for path in args.skip_edited or []:
        done |= {r['id'] for r in read_jsonl(path) if r.get('edit_kind') in ('minimal', 'larger')}
    for path in args.skip_samples or []:
        seen |= {(r['id'], r['sample']) for r in read_jsonl(path)}
    best = {}
    for a in answers:
        f = flags[(a['id'], a['sample'])]
        if f['severity'] <= 0 or a['id'] in done or (a['id'], a['sample']) in seen:
            continue
        # 'mild': the least-broken flagged answer that ended properly, so a minimal repair is possible; 'worst' tends to need a rewrite
        key = (f['severity'] if args.select == 'worst' else -f['severity'] - (0 if a['finish_reason'] == 'eos' else 1000))
        if a['id'] not in best or key > best[a['id']][2]:
            best[a['id']] = (a, f, key)
    rows = []
    for pid, (a, f, _) in sorted(best.items()):
        p = prompts[pid]
        rows.append(dict(id=pid, kind=p['kind'], source=p['source'], prompt=p['prompt'], check=p['check'],
                         sample=a['sample'], temperature=a['temperature'], model_answer=visible(a['raw_output']),
                         model_answer_finished=a['finish_reason'] == 'eos', severity=f['severity'], detector_notes=describe(f),
                         edited_answer='', edit_kind='', accept_words=[], editor_notes=''))
    # every template row is kept (those are the weak categories); Atlas rows fill the rest, most severe first
    keep = [r for r in rows if r['source'] == 'template']
    atlas = sorted((r for r in rows if r['source'] != 'template'), key=lambda r: ((-r['severity'] if args.select == 'worst' else r['severity']), r['id']))
    rows = sorted(keep + atlas[:max(0, args.max_rows - len(keep))], key=lambda r: r['id'])
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / 'edit-worksheet.jsonl', rows)
    (args.out / 'holdout-ids.json').write_text(json.dumps(holdout, indent=0) + '\n', encoding='utf-8')
    print(json.dumps(dict(rows=len(rows), holdout_prompts=len(holdout), by_kind=dict(Counter(r['kind'] for r in rows)),
                          unfinished=sum(not r['model_answer_finished'] for r in rows)), indent=1))


def edit_metrics(original, edited):
    a, b = words(original), words(edited)
    ratio = 1 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    return dict(edit_ratio=round(ratio, 3), words_before=len(a), words_after=len(b),
                length_ratio=round(len(b) / max(1, len(a)), 3))


def validate_row(analyzer, row, prompt_row, max_edit=MAX_EDIT_RATIO):
    """Reasons an edited row is not usable as a minimal-repair `chosen` answer (empty list: usable)."""
    edited = row['edited_answer'].strip()
    if row['edit_kind'] == 'drop':
        return ['dropped by the editor'] if not edited else ['drop must have an empty edited_answer']
    if not edited:
        return ['not edited']
    if row['edit_kind'] not in ('minimal', 'larger', 'drop'):
        return ['edit_kind must be minimal, larger or drop']
    problems = []
    original = row['model_answer']
    if edited == original.strip():
        problems.append('edit identical to the model answer')
    m = edit_metrics(original, edited)
    if row['edit_kind'] == 'minimal':
        if m['edit_ratio'] > max_edit:
            problems.append(f"edit changes {m['edit_ratio']:.0%} of the words (limit {max_edit:.0%})")
        if row['model_answer_finished']:
            if m['words_before'] >= SHORT_ANSWER_WORDS:
                if not LENGTH_BAND[0] <= m['length_ratio'] <= LENGTH_BAND[1]:
                    problems.append(f"length ratio {m['length_ratio']} outside {LENGTH_BAND}")
            elif abs(m['words_after'] - m['words_before']) > 5:
                problems.append('short answer changed by more than 5 words')
    f = flags_for(analyzer, prompt_row, edited, True, accept=set(row.get('accept_words') or []))
    if f['constraint']:
        problems += [f'constraint still fails: {c}' for c in f['constraint']]
    for key in ('empty', 'english_reply', 'loop'):
        if f[key]:
            problems.append(f'edit still flagged: {key}')
    if f['unknown_words']:
        problems.append('unknown words remain (fix them or list verified real words in accept_words): ' + ', '.join(f['unknown_words']))
    if f['english_words'] and prompt_row['kind'] != 'translate':
        problems.append('English words remain: ' + ', '.join(f['english_words']))
    structured_ending = False
    try:
        json.loads(atlas_constraints.strip_fence(edited))
        structured_ending = True
    except ValueError:
        pass
    # A complete Markdown table or a closed code block needs no trailing period.
    if re.search(r'^\s*\|?\s*:?-{3,}:?\s*\|', edited, re.M) and edited.endswith('|'):
        structured_ending = True
    if edited.startswith('```') and edited.endswith('```') and edited.count('```') % 2 == 0:
        structured_ending = True
    if not structured_ending and edited[-1] not in '.!?…"\')”»)]*' and not re.search(r'[.!?…]\s*$', edited):
        problems.append('edit does not end like a finished answer')
    return problems


def cmd_validate(args):
    rows = read_jsonl(args.worksheet)
    analyzer = nonword.Analyzer()
    report, ok = [], 0
    for row in rows:
        prompt_row = dict(kind=row['kind'], prompt=row['prompt'], check=row['check'])
        problems = validate_row(analyzer, row, prompt_row)
        usable = not problems
        ok += usable
        report.append(dict(id=row['id'], usable=usable, problems=problems, edit_kind=row['edit_kind'],
                           **(edit_metrics(row['model_answer'], row['edited_answer']) if row['edited_answer'].strip() else {})))
    summary = dict(rows=len(rows), usable=ok, not_edited=sum(r['problems'] == ['not edited'] for r in report),
                   dropped=sum(r['problems'] == ['dropped by the editor'] for r in report),
                   rejected=[r for r in report if not r['usable'] and r['problems'] not in (['not edited'], ['dropped by the editor'])])
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        write_jsonl(args.out / 'validation.jsonl', report)
        (args.out / 'validation-summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return report


def cmd_pairs(args):
    report = {r['id']: r for r in cmd_validate(argparse.Namespace(worksheet=args.worksheet, out=args.out))}
    pairs = []
    for row in read_jsonl(args.worksheet):
        if not report[row['id']]['usable'] or row['edit_kind'] not in args.include.split(','):
            continue
        m = edit_metrics(row['model_answer'], row['edited_answer'])
        if args.length_band and not (args.length_band[0] <= m['length_ratio'] <= args.length_band[1]):
            continue
        pairs.append(dict(
            id=row['id'], kind=row['kind'], source=row['source'],
            prompt=[dict(role='user', content=row['prompt'])],
            chosen=[dict(role='assistant', content=row['edited_answer'].strip())],
            rejected=[dict(role='assistant', content=row['model_answer'])],
            chat_template_kwargs=dict(enable_thinking=False), rejected_finished=row['model_answer_finished'], detector_notes=row['detector_notes'], label='synthetic', edit_kind=row['edit_kind'], **m))
    write_jsonl(args.out / 'pairs-tr-dpo.jsonl', pairs)
    print(f'{len(pairs)} pairs written to {args.out / "pairs-tr-dpo.jsonl"}')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('flag')
    s.add_argument('--prompts', type=Path, required=True)
    s.add_argument('--answers', type=Path, required=True)
    s.add_argument('--out', type=Path, required=True)
    s.add_argument('--accept-from', type=Path, nargs='*', default=None, help='edited worksheets: their accept_words (verified real words) are not flagged')
    s.add_argument('--accept-words', type=Path, default=None, help='text file, one verified real word per line (# comments allowed)')
    s = sub.add_parser('worksheet')
    s.add_argument('--prompts', type=Path, required=True)
    s.add_argument('--answers', type=Path, required=True)
    s.add_argument('--flags', type=Path, required=True)
    s.add_argument('--out', type=Path, required=True)
    s.add_argument('--max-rows', type=int, default=300)
    s.add_argument('--select', choices=('mild', 'worst'), default='mild', help='which flagged answer of a prompt goes to the editor')
    s.add_argument('--skip-edited', type=Path, nargs='*', default=None, help='earlier worksheets: prompts they already repaired are left out')
    s.add_argument('--skip-samples', type=Path, nargs='*', default=None, help='earlier worksheets: the answers they showed the editor are not offered again')
    s = sub.add_parser('validate')
    s.add_argument('--worksheet', type=Path, required=True)
    s.add_argument('--out', type=Path, default=None)
    s = sub.add_parser('pairs')
    s.add_argument('--worksheet', type=Path, required=True)
    s.add_argument('--include', default='minimal', help='edit kinds that become pairs: minimal, larger or minimal,larger')
    s.add_argument('--length-band', type=float, nargs=2, default=None, metavar=('LOW', 'HIGH'), help='keep only pairs whose chosen/rejected length ratio is in this band')
    s.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    {'flag': cmd_flag, 'worksheet': cmd_worksheet, 'validate': cmd_validate, 'pairs': cmd_pairs}[args.cmd](args)


if __name__ == '__main__':
    main()
