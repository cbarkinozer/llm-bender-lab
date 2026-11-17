"""Generate human-readable reports for the bilingual pilot from the frozen data + validation outputs.

  python scripts/datasets/report_lfm3_bilingual_pilot.py
Writes reports/TRANSLATION-ISSUES.{md,json}, reports/LENGTH-DISTRIBUTIONS.md, inspection/STRATIFIED-SAMPLE.md.
Deterministic (sample selection uses random.Random(3407)); files must be byte-identical on rerun after deletion.
"""
import collections
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import DIRECTIONS, PILOT, json_bytes, read_jsonl

ORIGINAL_TYPES = {'mistake_suspected', 'ambiguity', 'time_sensitive', 'formatting'}
SEV = ['high', 'medium', 'low', 'info']
MANDATORY = ['g007', 'g011', 'g041', 'g103', 'g119', 'g153']  # language-bound, noise, constraint, figurative sense, inconsistent prompt
SEED = 3407


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


def issues_report(flags, originals):
    by_group = {o['group_id']: o for o in originals}
    orig_issues, notes = [], []
    for f in flags:
        o = by_group[f['group_id']]
        item = dict(group_id=f['group_id'], source_row_id=f['source_row_id'], category=o['category'], severity=f['severity'],
                    type=f['type'], note=f['note'])
        is_original = f['type'] in ORIGINAL_TYPES or (f['type'] == 'verification' and f['severity'] != 'info')
        (orig_issues if is_original else notes).append(item)
    key = lambda x: (SEV.index(x['severity']), x['group_id'])  # noqa: E731
    orig_issues.sort(key=key)
    notes.sort(key=key)
    summary = dict(
        reviewed_originals_flagged=len({i['group_id'] for i in orig_issues}),
        original_issue_counts_by_severity=dict(collections.Counter(i['severity'] for i in orig_issues)),
        original_issue_counts_by_type=dict(collections.Counter(i['type'] for i in orig_issues)),
        translation_note_counts_by_type=dict(collections.Counter(i['type'] for i in notes)),
        policy='The reviewed Turkish originals were NOT modified. TR rows are byte-identical to the frozen reviewed text (plus the language instruction).')
    md = ['# Translation and original-quality issue report', '',
          'Status: agent-authored translations; the reviewed Turkish originals were **not** changed. Items below are suspected mistakes,',
          'ambiguities or unverifiable claims found while inspecting every original, plus translation decisions. Severity is the agent\'s',
          'judgement, not an owner ruling. Legal/historical/product claims were preserved verbatim and not independently source-verified.', '',
          '## Summary', '', f"- Originals with at least one suspected issue / ambiguity / unverified claim: **{summary['reviewed_originals_flagged']} of 160**",
          f"- By severity: {summary['original_issue_counts_by_severity']}", f"- By type: {summary['original_issue_counts_by_type']}",
          f"- Translation-decision notes by type: {summary['translation_note_counts_by_type']}", '',
          '## A. Suspected mistakes, ambiguities and unverified claims in the reviewed originals (owner decision needed)', '',
          '| Sev | Group | Source row | Category | Type | Note |', '|---|---|---|---|---|---|']
    for i in orig_issues:
        md.append(f"| {i['severity']} | {i['group_id'].replace('bp01-', '')} | `{i['source_row_id']}` | {i['category']} | {i['type']} | {i['note'].replace('|', '/')} |")
    md += ['', '## B. Translation decisions and language-bound content', '', '| Sev | Group | Type | Note |', '|---|---|---|---|']
    for i in notes:
        md.append(f"| {i['severity']} | {i['group_id'].replace('bp01-', '')} | {i['type']} | {i['note'].replace('|', '/')} |")
    return summary, orig_issues, notes, '\n'.join(md) + '\n'


def fmt_stats(d):
    return f"{d['n']} | {d['median']} | {d['p90']} | {d['p95']} | {d['p99']} | {d['max']} | {d['total']}"


def length_report(tr):
    lines = ['# Token and length distributions (native LFM3 template, local tokenizer, no truncation at 4096)', '',
             f"Tokenizer: `{tr['tokenizer']['path']}` (sha256 `{tr['tokenizer']['sha256'][:16]}...`). Renderer verified: {tr['tokenizer']['renderer_verified_against_historical_pilot160']}.",
             f"Supervised policy: {tr['supervised_policy']}. Truncated rows: {tr['truncated_rows']}; zero-supervised rows: {tr['zero_supervised_rows']}.", '',
             f"Supervised tokens per direction: {tr['supervised_totals_by_direction']} (all: {tr['supervised_total_all']}). pilot160 historical: {tr['historical_pilot160_supervised_tokens']}.", '']
    for title, key in (('By direction', 'by_direction'), ('By reasoning presence', 'by_reasoning'), ('By direction x reasoning', 'by_direction_and_reasoning'),
                       ('By category', 'by_category'), ('By source', 'by_source')):
        for field, label in (('supervised', 'Supervised (target) tokens'), ('length', 'Total sequence tokens'), ('masked', 'Context (masked) tokens')):
            lines += [f'## {title}: {label}', '', '| Group | rows | median | p90 | p95 | p99 | max | total |', '|---|---|---|---|---|---|---|---|']
            for name, fields in tr[key].items():
                lines.append(f'| {name} | {fmt_stats(fields[field])} |')
            lines.append('')
    return '\n'.join(lines) + '\n'


def sample_report(rows, originals, flags):
    by = collections.defaultdict(dict)
    for r in rows:
        by[r['group_id']][r['direction']] = r
    flag_by = collections.defaultdict(list)
    for f in flags:
        flag_by[f['group_id']].append(f)
    size = {g: sum(len(d[x]['messages'][i]['content']) for x in ('tr-tr', 'tr-en') for i in (1, 2)) + sum(len(d[x]['worked_solution'] or '') for x in ('tr-tr', 'tr-en')) for g, d in by.items()}
    rng = random.Random(SEED)
    chosen = [f'bp01-{m}' for m in MANDATORY]
    buckets = collections.defaultdict(list)
    for g, d in by.items():
        if g in chosen or size[g] > 3600:
            continue
        r = d['tr-tr']
        buckets[(r['source_key'], r['has_reasoning'])].append(g)
    for key in sorted(buckets, key=str):
        pool = sorted(buckets[key])
        chosen += rng.sample(pool, min(2, len(pool)))
    chosen = sorted(set(chosen))
    out = ['# Stratified translation sample for owner inspection', '',
           f'{len(chosen)} of 160 task groups: 6 mandatory edge cases (language-bound, noise, length constraint, figurative sense, inconsistent prompt) plus up to 2 per (source x reasoning) bucket, random.Random({SEED}), groups with <= 3,600 characters only.',
           '', 'For each group check: (1) is the English faithful (numbers, units, entities, negation, time, constraints, answer)? (2) is it natural English?',
           '(3) is the Turkish original untouched? (4) is the language instruction natural? Reasoning is shown only where the original has it.', '',
           'The four rows per group reuse exactly these texts: tr-tr = original + instruction; en-tr = EN prompt + original answer; tr-en = original prompt + EN answer; en-en = EN prompt + EN answer.', '']
    for g in chosen:
        d = by[g]
        o = next(x for x in originals if x['group_id'] == g)
        tr, en_ = d['tr-tr'], d['en-en']
        out += [f"## {g.replace('bp01-', '')} · {o['source_row_id']} · {o['category']} · {o['source_key']} · reasoning={'yes' if tr['has_reasoning'] else 'no'} · EN-output effect={d['tr-en']['output_language_effect']}", '',
                '**TR prompt (original + instruction)**', '', '```text', tr['messages'][1]['content'], '```', '',
                '**EN prompt (translation + instruction)**', '', '```text', en_['messages'][1]['content'], '```', '',
                '**TR answer (original)**', '', '```text', tr['messages'][2]['content'], '```', '',
                '**EN answer (translation)**', '', '```text', en_['messages'][2]['content'], '```', '']
        if tr['has_reasoning']:
            out += ['**TR reasoning (original)**', '', '```text', tr['worked_solution'], '```', '', '**EN reasoning (translation)**', '', '```text', en_['worked_solution'], '```', '']
        if flag_by.get(g):
            out += ['**Agent flags**', ''] + [f"- [{f['severity']}] {f['type']}: {f['note']}" for f in flag_by[g]] + ['']
        out += ['- [ ] faithful  - [ ] natural English  - [ ] original untouched  - [ ] notes: ', '', '---', '']
    return chosen, '\n'.join(out) + '\n'


def main():
    rows = read_jsonl(PILOT / 'data/train.jsonl')
    originals = read_jsonl(PILOT / 'data/source-originals.jsonl')
    flags = read_jsonl(PILOT / 'data/translation-flags.jsonl')
    tr = json.loads((PILOT / 'validation/token-length-report.json').read_text(encoding='utf-8'))
    summary, orig_issues, notes, md = issues_report(flags, originals)
    write(PILOT / 'reports/TRANSLATION-ISSUES.md', md)
    (PILOT / 'reports').mkdir(exist_ok=True)
    (PILOT / 'reports/translation-issues.json').write_bytes(json_bytes(dict(summary=summary, original_issues=orig_issues, translation_notes=notes)))
    write(PILOT / 'reports/LENGTH-DISTRIBUTIONS.md', length_report(tr))
    chosen, sample_md = sample_report(rows, originals, flags)
    write(PILOT / 'inspection/STRATIFIED-SAMPLE.md', sample_md)
    (PILOT / 'inspection/stratified-sample-groups.json').write_bytes(json_bytes(dict(seed=SEED, groups=chosen)))
    print(json.dumps(summary, ensure_ascii=False, indent=1), len(chosen), 'sample groups', len(DIRECTIONS), 'directions')


if __name__ == '__main__':
    main()
