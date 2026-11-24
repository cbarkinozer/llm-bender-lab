"""Prompt pool for the on-policy Turkish DPO pairs (preference-rl exp-004).

  python tr_dpo_onpolicy_prompts.py build --out DIR [--fresh 3500]

Pool = the exp-003 prompts that are not in its 15% held-out set (the held-out prompts stay a pure test) + fresh Turkce Atlas prompts
(MIT; 336k rows, only 500 were used by the SFT core pack, and those 500 are excluded here). Same selection rules as the SFT core
pack (120-1200 characters, Turkish letters, a real reference answer), mix constrained / context / plain = 50 / 30 / 20.
Fresh prompts that are near duplicates (4-gram Jaccard) of a writing-probe or held-out prompt are dropped. Needs the local Atlas file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tr_dpo_prompts as P  # noqa: E402
import tr_dpo_flags as F  # noqa: E402
from lfm3_sft_constraints import parse_constraints  # noqa: E402

EXP003_PROMPTS = ROOT / 'experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality/data/prompts-tr-dpo.jsonl'
ATLAS = ROOT / 'experiments/turkish-capability/lfm3-1.7b/source-audit-v01/raw-local/atlas/train.chat.jsonl'
ATLAS_SHA256 = '3caf3081da91ad46890b93907d5123ec1c03508368b5afbc8f9e33c89042e044'
DIACRITICS = re.compile('[çğıöşüÇĞİÖŞÜ]')
CONTEXT_MARK = re.compile(r'(?:pasaj|metin|veri|orijinal|rapor|bağlam)\s*:', re.I)
MIX = dict(constrained=0.5, context=0.3, plain=0.2)
SEED = 'exp004'


def rank(key):
    return hashlib.sha256(f'{SEED}:{key}'.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['build'])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--fresh', type=int, default=3500, help='fresh Atlas prompts to add')
    ap.add_argument('--near-duplicate', type=float, default=0.7)
    args = ap.parse_args()

    if hashlib.sha256(ATLAS.read_bytes()).hexdigest() != ATLAS_SHA256:
        sys.exit('Atlas checksum mismatch')
    old = P.read_jsonl(EXP003_PROMPTS)
    held = [r for r in old if F.is_holdout(r['id'])]
    keep_old = [r for r in old if not F.is_holdout(r['id'])]
    # every prompt of the SFT core pack's Atlas draw is excluded, trained on or not (exp-003 already used the unseen ones)
    core_prompts = {P.norm(r['messages'][0]['content']) for r in P.read_jsonl(P.ATLAS_RENDER) if r['category'] == 'tr_general'}
    probe = P.read_jsonl(P.PROBE)
    reference = [(r['id'], P.shingles(r['prompt'])) for r in probe] + [(r['id'], P.shingles(r['prompt'])) for r in held]
    pools = dict(constrained=[], context=[], plain=[])
    seen = {P.norm(r['prompt']) for r in old}
    dropped = dict(core=0, dup=0, near_duplicate=0)
    with ATLAS.open(encoding='utf-8') as stream:
        for index, line in enumerate(stream):
            msgs = json.loads(line)['messages']
            user, ref = msgs[1]['content'].strip(), msgs[2]['content'].strip()
            if not 120 <= len(user) <= 1200 or not DIACRITICS.search(user) or len(ref) < 20 or ref.startswith('S:'):
                continue
            key = P.norm(user)
            if key in core_prompts:
                dropped['core'] += 1
                continue
            if key in seen:
                dropped['dup'] += 1
                continue
            seen.add(key)
            items = parse_constraints(user)
            group = 'constrained' if items else 'context' if CONTEXT_MARK.search(user) else 'plain'
            pools[group].append((index, user, items))
    sizes = {k: len(v) for k, v in pools.items()}
    picked = []
    for group, share in MIX.items():
        want = round(args.fresh * share)
        for index, user, items in sorted(pools[group], key=lambda p: rank(f'{group}:{p[0]}')):
            if want == 0:
                break
            sh = P.shingles(user)
            if any(P.jaccard(sh, rsh) > args.near_duplicate for _, rsh in reference):
                dropped['near_duplicate'] += 1
                continue
            kind = 'atlas_constraint' if items else ('atlas_context' if len(user) > 500 else 'atlas_plain')
            picked.append(dict(id=f'dpo4-atlas-{index:06d}', source='atlas_fresh', kind=kind, prompt=user,
                               check=dict(type='constraints', items=items) if items else None, atlas_row=index))
            want -= 1
    picked.sort(key=lambda r: rank(r['id']))
    rows = keep_old + picked
    assert len({r['id'] for r in rows}) == len(rows) and len({P.norm(r['prompt']) for r in rows}) == len(rows)
    held_ids = {r['id'] for r in held}
    assert not held_ids & {r['id'] for r in rows}
    args.out.mkdir(parents=True, exist_ok=True)
    text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    (args.out / 'prompts-tr-dpo4.jsonl').write_text(text, encoding='utf-8', newline='\n')
    kinds = {}
    for r in rows:
        kinds[r['kind']] = kinds.get(r['kind'], 0) + 1
    manifest = dict(rows=len(rows), from_exp003_train=len(keep_old), fresh=len(picked), heldout_excluded=len(held), by_kind=kinds,
                    atlas_pool_sizes=sizes, dropped=dropped, sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
    (args.out / 'prompts-tr-dpo4.manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
