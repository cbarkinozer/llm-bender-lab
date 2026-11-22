"""Validate the owner's filled translation worksheets for SFT core v01. Reports problems per row; writes a JSON report.

  python validate_lfm3_sft_core_translations.py --worksheets DIR [--report OUT.json]

Errors (the row cannot be used): missing/duplicate/unknown ids, empty cells, digits changed, wrapper placeholders missing.
Warnings (inspect): spelled-out numbers, code-like tokens changed, quoted text changed, text left identical to the English,
very different length, tool-query argument values missing from the Turkish text.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_sft_core as core  # noqa: E402

TR_NUMBER_WORDS = re.compile(r'\b(bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|kırk|elli|altmış|yetmiş|seksen|doksan|yüz|bin)\b',
                             re.I)
NUMBER = re.compile(r'\d[\d.,]*\d|\d')
CODEISH = re.compile(r'`[^`]+`|\b\w+_\w+\b|\b[a-z]+[A-Z]\w*\b|\w+\(\)')
PLACEHOLDER = re.compile(r'\{(?:q|text|tests)\}')


def numbers(text):
    return Counter(core.norm_num(t) for t in NUMBER.findall(text))


def read(path):
    with Path(path).open('r', encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check_pairs(file, rows, expected, errors, warnings, kind):
    seen = set()
    for r in rows:
        rid, en, tr = r['id'], r['english'], (r['turkish'] or '').strip()
        if rid in seen:
            errors.append((file, rid, 'duplicate id'))
        seen.add(rid)
        if rid not in expected:
            errors.append((file, rid, 'unknown id'))
            continue
        if expected[rid] != en:
            errors.append((file, rid, 'english column was edited'))
        if not tr:
            errors.append((file, rid, 'empty'))
            continue
        if kind == 'wrapper':
            if sorted(PLACEHOLDER.findall(en)) != sorted(PLACEHOLDER.findall(tr)):
                errors.append((file, rid, f'placeholders differ: {PLACEHOLDER.findall(en)} vs {PLACEHOLDER.findall(tr)}'))
            continue
        en_n, tr_n = numbers(en), numbers(tr)
        if en_n != tr_n:
            errors.append((file, rid, f'digits differ: missing {sorted((en_n - tr_n).elements())} extra {sorted((tr_n - en_n).elements())}'))
        if TR_NUMBER_WORDS.search(tr) and not TR_NUMBER_WORDS.search(en.lower()):
            hits = sorted(set(m.lower() for m in TR_NUMBER_WORDS.findall(tr)))
            warnings.append((file, rid, f'number words in Turkish (check they are not replacing digits): {hits}'))
        for token in set(CODEISH.findall(en)):
            if token not in tr:
                warnings.append((file, rid, f'code-like token not kept: {token}'))
        for quoted in re.findall(r'"([^"]{3,})"', en):
            if quoted not in tr:
                warnings.append((file, rid, f'quoted text changed: {quoted[:50]}'))
        if tr.strip().lower() == en.strip().lower():
            warnings.append((file, rid, 'identical to English'))
        ratio = len(tr) / max(1, len(en))
        if not 0.6 <= ratio <= 1.9:
            warnings.append((file, rid, f'length ratio {ratio:.2f}'))
    for rid in expected:
        if rid not in seen:
            errors.append((file, rid, 'missing row'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worksheets', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rows = core.load_core()
    errors, warnings, summary = [], [], {}
    for file, category, field in core.WORKSHEETS:
        path = args.worksheets / file
        if not path.exists():
            summary[file] = 'not provided'
            continue
        expected = {r['id']: r['en'][field] for r in rows if r['category'] == category}
        data = read(path)
        before = len(errors)
        check_pairs(file, data, expected, errors, warnings, 'text')
        if category == 'tool':
            by_id = {r['id']: r for r in rows if r['category'] == 'tool'}
            for r in data:
                tr = (r['turkish'] or '').strip()
                row = by_id.get(r['id'])
                if not tr or row is None:
                    continue
                (name, params), = row['check']['gold_calls'][0].items()
                for key, values in params.items():
                    if isinstance(values[0], str) and core.norm_text(values[0]) not in core.norm_text(tr):
                        warnings.append((file, r['id'], f'argument value not in Turkish text: {key}={values[0]!r}'))
        summary[file] = dict(rows=len(data), expected=len(expected), errors=len(errors) - before)
    wrappers_path = args.worksheets / '00-wrappers.csv'
    if wrappers_path.exists():
        expected = {f'{cat}:{wid}': tpl for cat, group in core.WRAPPERS.items() for wid, tpl in group.items() if wid != 'bare'}
        data = read(wrappers_path)
        before = len(errors)
        check_pairs('00-wrappers.csv', data, expected, errors, warnings, 'wrapper')
        summary['00-wrappers.csv'] = dict(rows=len(data), expected=len(expected), errors=len(errors) - before)
    else:
        summary['00-wrappers.csv'] = 'not provided'
    report = dict(summary=summary, errors=[dict(file=f, id=i, problem=p) for f, i, p in errors],
                  warnings=[dict(file=f, id=i, problem=p) for f, i, p in warnings])
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(summary, indent=1))
    print(f'errors: {len(errors)}  warnings: {len(warnings)}')
    for f, i, p in errors[:25]:
        print('ERROR  ', f, i, p)
    for f, i, p in warnings[:15]:
        print('WARNING', f, i, p)


if __name__ == '__main__':
    main()
