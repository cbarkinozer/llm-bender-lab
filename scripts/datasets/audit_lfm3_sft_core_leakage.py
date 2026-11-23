"""SFT core v01: lexical leakage and duplicate audit of the pack and the core prompts against the protected eval sets (CPU).

  python audit_lfm3_sft_core_leakage.py [--out REPORT.json] [--local-out MATCHES.jsonl]

Protected sets: eval v2 math/symbolic/tool pairs (EN+TR), the 100-item GSM8K final test, the 40 writing prompts, Belebele EN+TR,
TurBLiMP 1600, CETVEL-500, HumanEval, BFCL (queries), IFEval 541. Training sides: the 2,909-row pack and the 2,500 core prompts.
Method (same family as audit_turkish_source_overlap.py): normalised word n-grams. Flags per (training text, protected item):
exact (equal normalised text), near (>= 3 shared 6-grams and >= 50% of the smaller text's 6-grams), run12 (a shared 12-gram),
short (a protected sentence of 4 to 5 words found inside a training text), numsig (math: same multiset of >= 3 numbers, which
also catches translations). Lexical checks do not prove semantic or cross-lingual clearance. The committed report holds ids and
counts only; matched text goes to the ignored local file.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
CORE = LAB / 'sft-core-v01'
SKIP_KEYS = {'tests', 'setup', 'gold', 'gold_calls', 'id', 'pair_id', 'family', 'language', 'tools', 'link', 'dialect', 'ds'}


def norm(text):
    return ' '.join(re.findall(r'\w+', text.replace('İ', 'i').replace('I', 'ı').lower()))


def grams(words, n):
    return {' '.join(words[i:i + n]) for i in range(len(words) - n + 1)}


def strings(obj, key=None):
    if isinstance(obj, str):
        return [] if key in SKIP_KEYS else [obj]
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out.extend(strings(v, k))
        return out
    if isinstance(obj, list):
        return [s for v in obj for s in strings(v, key)]
    return []


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def user_text(messages):
    if isinstance(messages, str):
        return messages
    return '\n'.join(m['content'] for m in messages if m.get('role') == 'user')


def numbers(text):
    return tuple(sorted(re.findall(r'\d+', text)))


def protected_sets():
    sets = {}
    def add(name, items):
        sets[name] = items
    for fam in ('math', 'symbolic', 'toolcall'):
        rows = read_jsonl(LAB / f'eval-v2/data-local/{fam}-pairs.jsonl')
        add(f'evalv2-{fam}', [(r['id'], [user_text(r['messages'])]) for r in rows])
    add('writing-tr-40', [(r['id'], [r['prompt']]) for r in read_jsonl(LAB / 'eval-v2/writing-prompts-tr.jsonl')])
    for lang in ('eng_Latn', 'tur_Latn'):
        rows = read_jsonl(LAB / f'eval-v2/source-cache/belebele-{lang}.jsonl')
        add(f'belebele-{lang}', [(f'{lang}:{r["link"]}:{r["question_number"]}', [r['flores_passage'], r['question']]) for r in rows])
    add('turblimp-1600', [(r['id'], [r['sentence_good'], r['sentence_bad']]) for r in read_jsonl(LAB / 'exp-000-baseline/data-local/turblimp-1600.jsonl')])
    add('cetvel-500', [(r['id'], strings(r['document']) + [r['semantic_prompt']] + [user_text(r['messages'])]) for r in
                       read_jsonl(LAB / 'exp-000-baseline/data-local/questions-500.jsonl')])
    add('ifeval-541', [(f'ifeval:{r["key"]}', [r['prompt']]) for r in read_jsonl(CORE / 'source-cache/google__IFEval/ifeval_input_data.jsonl')])
    import pyarrow.parquet as pq
    he = pq.read_table(CORE / 'source-cache/openai__openai_humaneval/openai_humaneval/test-00000-of-00001.parquet').to_pylist()
    add('humaneval-164', [(r['task_id'], [r['prompt']]) for r in he])
    bfcl = []
    for name in ('simple', 'multiple', 'parallel'):
        path = LAB / f'eval-v2/data-local/source-cache/gorilla-llm__Berkeley-Function-Calling-Leaderboard/BFCL_v3_{name}.json'
        for line in path.read_text(encoding='utf-8').split('\n'):
            if line.strip():
                r = json.loads(line)
                bfcl.append((r['id'], [user_text(q) if isinstance(q, list) else str(q) for q in r['question']] if isinstance(r['question'][0], list)
                             else [str(r['question'])]))
    add('bfcl-v3', bfcl)
    core_rows = read_jsonl(CORE / 'prompts-en.jsonl')
    add('gsm8k-final-test', [(r['id'], [r['en']['q']]) for r in core_rows if r['category'] == 'math_final_test'])
    return sets


def build_index(items):
    texts, index, short = [], defaultdict(set), []
    for item_id, strs in items:
        for s in strs:
            words = norm(s).split()
            tid = len(texts)
            texts.append((item_id, ' '.join(words), len(words)))
            g6 = grams(words, 6)
            for g in g6:
                index[('6', g)].add(tid)
            for g in grams(words, 12):
                index[('12', g)].add(tid)
            if 4 <= len(words) <= 5:
                short.append((tid, ' ' + ' '.join(words) + ' '))
    return texts, index, short


def flags_for(text, texts, index, short):
    norm_text = norm(text)
    words = norm_text.split()
    g6, g12 = grams(words, 6), grams(words, 12)
    shared6, shared12 = Counter(), Counter()
    for g in g6:
        for tid in index.get(('6', g), ()):
            shared6[tid] += 1
    for g in g12:
        for tid in index.get(('12', g), ()):
            shared12[tid] += 1
    found = {}
    for tid, count in shared6.items():
        item_id, prot_norm, prot_len = texts[tid]
        prot_g6 = max(1, prot_len - 5)
        if prot_norm == norm_text:
            found.setdefault(item_id, set()).add('exact')
        elif count >= 3 and count / min(len(g6), prot_g6) >= 0.5:
            found.setdefault(item_id, set()).add('near')
    for tid in shared12:
        found.setdefault(texts[tid][0], set()).add('run12')
    padded = ' ' + norm_text + ' '
    for tid, key in short:
        if key in padded:
            found.setdefault(texts[tid][0], set()).add('short')
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=CORE / 'leakage-audit-v01.json')
    parser.add_argument('--local-out', type=Path, default=CORE / 'samples-local/leakage-audit-matches.jsonl')
    args = parser.parse_args()
    pack = read_jsonl(CORE / 'pack-local/lfm3-base-v1/train.jsonl')
    core = read_jsonl(CORE / 'prompts-en.jsonl')
    train = {'pack': [(r['id'], user_text(r['prompt'])) for r in pack],
             'core-prompts': [(r['id'], '\n'.join(strings({k: v for k, v in r.get(lang, {}).items() if k != 'tests'}))) for r in core
                              for lang in ('en', 'tr') if lang in r]}
    sets = protected_sets()
    report: dict = dict(protected_sets={k: dict(items=len(v), texts=sum(len(s) for _, s in v)) for k, v in sets.items()},
                  training_sets={k: len(v) for k, v in train.items()}, method=(__doc__ or '').split('\n')[0], matches={})
    local = []
    category = {r['id']: r['category'] for r in pack}
    for name, items in sets.items():
        texts, index, short = build_index(items)
        for tname, rows in train.items():
            hits = defaultdict(lambda: defaultdict(set))
            for tid, text in rows:
                if len(text.split()) < 4:
                    continue
                for prot_id, kinds in flags_for(text, texts, index, short).items():
                    if name == 'gsm8k-final-test' and tid.startswith('c-mathtest'):
                        continue
                    for kind in kinds:
                        hits[kind][tid].add(prot_id)
                    local.append(dict(protected=name, protected_id=prot_id, train_set=tname, train_id=tid, kinds=sorted(kinds), train_text=text[:400]))
            summary = {kind: dict(train_rows=len(ids), ids=sorted(ids)[:40]) for kind, ids in hits.items()}
            report['matches'][f'{tname} vs {name}'] = summary or 'none'
    # numeric signature (math rows against eval math and the final test, EN texts)
    prot_sig = defaultdict(set)
    for r in core:
        if r['category'] == 'math_final_test':
            sig = numbers(r['en']['q'])
            if len(sig) >= 3:
                prot_sig[sig].add(r['id'])
    for r in read_jsonl(LAB / 'eval-v2/data-local/math-pairs.jsonl'):
        sig = numbers(user_text(r['messages']))
        if len(sig) >= 3:
            prot_sig[sig].add(r['id'])
    sig_hits = {}
    for r in core:
        if r['category'] == 'math':
            sig = numbers(r['en']['q'])
            if len(sig) >= 3 and sig in prot_sig:
                sig_hits[r['id']] = sorted(prot_sig[sig])
    report['numsig_math_train_vs_eval_and_final'] = sig_hits or 'none'
    # duplicates inside the pack
    by_norm = defaultdict(list)
    for tid, text in train['pack']:
        by_norm[norm(text)].append(tid)
    dup_prompts = {k: v for k, v in by_norm.items() if len(v) > 1}
    by_completion = defaultdict(list)
    for r in pack:
        comp = r['completion']
        comp = '\n'.join(m['content'] for m in comp) if isinstance(comp, list) else comp
        by_completion[norm(comp)].append(r['id'])
    dup_completions = {k: v for k, v in by_completion.items() if len(v) > 1}
    texts, index, short = build_index([(tid, [t]) for tid, t in train['pack']])
    near_pairs = set()
    for tid, text in train['pack']:
        words = norm(text).split()
        if len(words) < 10:
            continue
        g = grams(words, 6)
        counts = Counter(t for x in g for t in index.get(('6', x), ()))
        for t, c in counts.items():
            other = texts[t][0]
            if other != tid and other.rsplit('-', 1)[0] != tid.rsplit('-', 1)[0] and c / max(len(g), 1) >= 0.8 and c / max(1, texts[t][2] - 5) >= 0.8:
                near_pairs.add(tuple(sorted((tid, other))))
    report['pack_duplicates'] = dict(exact_prompt_groups=len(dup_prompts), exact_prompt_rows=sum(len(v) for v in dup_prompts.values()),
                                     examples=[v for v in list(dup_prompts.values())[:15]], exact_completion_groups=len(dup_completions),
                                     exact_completion_examples=[v for v in list(dup_completions.values())[:10]],
                                     near_duplicate_prompt_pairs_80pct=len(near_pairs), near_examples=sorted(near_pairs)[:15])
    # Atlas opening diversity in the pack
    openings = Counter(' '.join(norm(t).split()[:4]) for tid, t in train['pack'] if category.get(tid) == 'tr_general')
    total = sum(openings.values())
    report['atlas_prompt_openings_in_pack'] = dict(rows=total, distinct_4word_openings=len(openings), top10=openings.most_common(10),
                                                   rows_with_an_opening_seen_at_least_5_times=sum(c for c in openings.values() if c >= 5))
    tool_rows = [r for r in pack if r['category'] == 'tool']
    tool_completions = Counter(norm('\n'.join(m['content'] for m in r['completion']) if isinstance(r['completion'], list) else r['completion'])
                               for r in tool_rows)
    report['tool_rows_redundancy'] = dict(rows=len(tool_rows), distinct_completions=len(tool_completions),
                                          largest_identical_groups=sorted(tool_completions.values(), reverse=True)[:8])
    report['inputs_sha256'] = dict(pack=hashlib.sha256((CORE / 'pack-local/lfm3-base-v1/train.jsonl').read_bytes()).hexdigest(),
                                   core_prompts=hashlib.sha256((CORE / 'prompts-en.jsonl').read_bytes()).hexdigest())
    args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    args.local_out.parent.mkdir(parents=True, exist_ok=True)
    args.local_out.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in local) + ('\n' if local else ''), encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('protected_sets',)}, indent=1, ensure_ascii=False)[:6000])


if __name__ == '__main__':
    main()
