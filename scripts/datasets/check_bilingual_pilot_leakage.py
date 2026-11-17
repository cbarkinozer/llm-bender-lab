"""Leakage screen: candidate bilingual training/eval text vs every existing evaluation/holdout packet.

Screens exact normalized overlap, word n-gram containment, and cross-lingual numeric/entity signatures.
These find CANDIDATES for manual review; they do not prove semantic or cross-lingual independence.

  python scripts/datasets/check_bilingual_pilot_leakage.py --set eval   # new frozen eval vs train160 + old packets
  python scripts/datasets/check_bilingual_pilot_leakage.py --set train  # 640 variants vs all packets + new eval
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import BASE, PILOT, all_instruction_texts, json_bytes, normalized, read_jsonl, sha256_file

NGRAM = 5
NUM_RE = re.compile(r'\d+(?:[.,]\d+)*')
ENT_RE = re.compile(r'(?<![.!?]\s)(?<!^)\b[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ]{3,}')


def as_text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


STOP_ENTITIES = {'answer', 'turkish', 'english', 'yanıtını', 'türkçe', 'i̇ngilizce', 'ingilizce', 'turkce'}


def strip_instruction(text):
    for instr in all_instruction_texts():
        if text.rstrip().endswith(instr):
            return text.rstrip()[:-len(instr)].rstrip()
    return text


def msg_text(messages, roles):
    return '\n'.join(m['content'] for m in messages if m['role'] in roles)


def packet_items():
    """(packet, id, [(field, text)]) for every existing evaluation/holdout packet found locally."""
    specs = [
        ('old20-test', BASE / 'sft-pilot160-v01/test.jsonl', 'chat'),
        ('pilot80-test', BASE / 'sft-pilot80-v01/test.jsonl', 'chat'),
        ('reviewed-pilot-test', BASE / 'reviewed-pilot-v01/test.jsonl', 'chat'),
        ('dev20', BASE / 'sft160-dev-v01/questions.jsonl', 'q'),
        ('xling-v01', BASE / 'crosslingual-holdout-v01/questions.jsonl', 'q'),
        ('xling-v01-symbolic', BASE / 'crosslingual-holdout-v01/symbolic-controls.jsonl', 'q'),
        ('reasoning4', BASE / 'pilot160-runtime-local/reasoning4.jsonl', 'q'),
        ('cetvel500-audit', BASE / 'preparation-local/questions-500.jsonl', 'cetvel'),
    ]
    present, missing = [], []
    items = []
    for name, path, kind in specs:
        if not path.exists():
            missing.append(name)
            continue
        rows = read_jsonl(path)
        present.append(dict(packet=name, path=str(path.relative_to(BASE.parents[2])), rows=len(rows), sha256=sha256_file(path)))
        for r in rows:
            fields = [('prompt', msg_text(r['messages'], {'user'}))]
            if kind == 'chat':
                fields.append(('answer', msg_text(r['messages'], {'assistant'})))
                if r.get('worked_solution'):
                    fields.append(('reasoning', r['worked_solution']))
            elif kind == 'q':
                fields.append(('answer', as_text(r.get('target') or '')))
            else:
                fields.append(('answer', as_text(r.get('target') or '')))
                fields.append(('document', as_text(r.get('document') or '')))
            items.append((name, r['id'], fields))
    return items, present, missing


def new_eval_items():
    out = []
    ev = PILOT / 'eval-v01'
    for r in read_jsonl(ev / 'eval-prompts.jsonl'):
        out.append(('bilingual-eval-v01', r['id'], [('prompt', strip_instruction(msg_text(r['messages'], {'user'})))]))
    for r in read_jsonl(ev / 'eval-references.jsonl'):
        out.append(('bilingual-eval-v01-ref', r['id'], [('answer', r['reference_answer'])]))
    for r in read_jsonl(ev / 'symbolic-controls-prompts.jsonl'):
        out.append(('bilingual-eval-v01-symbolic', r['id'], [('prompt', msg_text(r['messages'], {'user'}))]))
    return out


def ngrams(text, n=NGRAM):
    toks = normalized(text).split()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def numbers(text):
    """Non-trivial numbers only: >= 2 digits or decimals (single digits are chance matches)."""
    out = set()
    for n in NUM_RE.findall(text):
        plain = n.replace('.', '').replace(',', '')
        if len(plain) >= 2:
            out.add(plain)
    return out


def entities(text):
    return {e.casefold() for e in ENT_RE.findall(text)} - STOP_ENTITIES


def screen(candidates, protected, ngram_threshold, num_threshold):
    """candidates/protected: [(packet, id, [(field, text)])]. Returns summary + flagged pairs."""
    prot = []
    for packet, pid, fields in protected:
        text = '\n'.join(t for _, t in fields)
        prot.append((packet, pid, normalized(text), ngrams(text), numbers(text), entities(text),
                     {f: normalized(t) for f, t in fields}))
    flagged, exact = [], []
    for cpacket, cid, cfields in candidates:
        ctext = '\n'.join(t for _, t in cfields)
        cn, cg, cnum, cent = normalized(ctext), ngrams(ctext), numbers(ctext), entities(ctext)
        cfn = {f: normalized(t) for f, t in cfields}
        for packet, pid, pn, pg, pnum, pent, pfn in prot:
            for f, v in cfn.items():
                if v and f in pfn and v == pfn[f] and len(v.split()) > 3:
                    exact.append(dict(candidate=cid, protected=f'{packet}:{pid}', field=f))
            contain = (len(cg & pg) / min(len(cg), len(pg))) if cg and pg else 0.0
            shared_nums = cnum & pnum
            num_j = len(shared_nums) / len(cnum | pnum) if (cnum | pnum) else 0.0
            shared_ent = cent & pent
            reasons = []
            if contain >= ngram_threshold:
                reasons.append(f'ngram_containment={contain:.2f}')
            if len(shared_nums) >= 2 and num_j >= num_threshold:
                reasons.append(f'numbers={sorted(shared_nums)} jaccard={num_j:.2f}')
            if len(shared_nums) >= 1 and len(shared_ent) >= 2:
                reasons.append(f'numbers+entities={sorted(shared_nums)}/{sorted(shared_ent)}')
            if reasons:
                flagged.append(dict(candidate=cid, protected=f'{packet}:{pid}', reasons=reasons))
    return exact, flagged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', choices=['eval', 'train'], required=True)
    ap.add_argument('--train-file', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--ngram-threshold', type=float, default=0.15)
    ap.add_argument('--num-threshold', type=float, default=0.5)
    args = ap.parse_args()
    packets, present, missing = packet_items()
    train_originals = []
    for r in read_jsonl(BASE / 'sft-pilot160-v01/train.jsonl'):
        fields = [('prompt', msg_text(r['messages'], {'user'})), ('answer', msg_text(r['messages'], {'assistant'}))]
        if r.get('worked_solution'):
            fields.append(('reasoning', r['worked_solution']))
        train_originals.append(('train160-original', r['id'], fields))
    if args.set == 'eval':
        candidates, protected = new_eval_items(), packets + train_originals
    else:
        rows = read_jsonl(args.train_file)
        candidates = []
        for r in rows:
            fields = [('prompt', strip_instruction(msg_text(r['messages'], {'user'}))), ('answer', msg_text(r['messages'], {'assistant'}))]
            if r.get('worked_solution'):
                fields.append(('reasoning', r['worked_solution']))
            candidates.append(('bilingual-train', r['id'], fields))
        protected = packets + new_eval_items()
    exact, flagged = screen(candidates, protected, args.ngram_threshold, args.num_threshold)
    def base_group(cid):
        return cid.rsplit('-', 2)[0] if cid.startswith('bp01-g') else cid.rsplit('-', 2)[0]
    agg = {}
    for f_ in flagged:
        key = (base_group(f_['candidate']), f_['protected'])
        a_ = agg.setdefault(key, dict(candidate_group=key[0], protected=key[1], variants=0, reasons=set()))
        a_['variants'] += 1
        a_['reasons'].update(f_['reasons'])
    aggregated = [dict(candidate_group=v['candidate_group'], protected=v['protected'], variants_flagged=v['variants'],
                       reasons=sorted(v['reasons'])) for v in agg.values()]
    report = dict(set=args.set, candidates=len(candidates), protected_items=len(protected),
                  packets_checked=present, packets_missing_locally=missing,
                  method=dict(ngram=NGRAM, ngram_containment_threshold=args.ngram_threshold,
                              numeric_jaccard_threshold=args.num_threshold,
                              note='candidates for manual review only; not proof of independence'),
                  exact_overlap=exact, flagged_count=len(flagged), flagged_group_pairs=len(aggregated),
                  flagged_group_pair_list=aggregated, flagged_pairs=flagged)
    print(f'candidates={len(candidates)} protected={len(protected)} exact={len(exact)} flagged={len(flagged)}')
    print('group-level flagged pairs:', len(aggregated))
    for f in aggregated[:80]:
        print(f['candidate_group'], '<->', f['protected'], f['variants_flagged'], f['reasons'])
    if args.out:
        Path(args.out).write_bytes(json_bytes(report))


if __name__ == '__main__':
    main()
