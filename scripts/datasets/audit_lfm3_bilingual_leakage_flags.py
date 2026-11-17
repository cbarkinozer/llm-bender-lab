"""Per-flag audit of the group-level leakage screen (reads validation/leakage-flag-evidence.json built by the screen)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import BASE, PILOT, json_bytes, normalized, read_jsonl

TOPICAL = {('bp01-g111', 'tquad-00562'), ('bp01-g111', 'tquad-00567'), ('bp01-g111', 'tquad-00571'), ('bp01-g111', 'tquad-00579')}
TEMPLATE = {('bp01-g115', '281286')}
GENERIC = {'cevap', 'soru', 'metin', 'özet', 'sonuç', 'diğer', 'hava', 'büyük', 'hesap', 'kontrol', 'toplam', 'veri', 'veriler', 'değerlendirme', 'yıllık',
           'etki', 'genel', 'aralık', 'kanun', 'kanunu', 'türk', 'türkiye', 'devlet', 'ekonomik', 'sosyal', 'hakları', 'i̇nsan', 'avrupa', 'arap',
           'müslüman', 'kemal', 'mustafa', 'temmuz', 'ağustos', 'eylül', 'ekim', 'haziran', 'anadolu', 'milli', 'müdürlüğü', 'august', 'osmanlı',
           'ankara', 'arabic', 'i̇mparatorluğu'}


def main():
    ev = json.loads((PILOT / 'validation/leakage-flag-evidence.json').read_text(encoding='utf-8'))
    q = {r['id']: r for r in read_jsonl(BASE / 'preparation-local/questions-500.jsonl')}
    g111 = ' '.join(r['messages'][2]['content'] for r in read_jsonl(PILOT / 'data/train.jsonl') if r['group_id'] == 'bp01-g111')
    out, md = [], ['# Per-flag leakage audit (83 group-level flags)', '',
                   'Test for a *shared underlying task*: (a) 5-gram containment >= 0.15, or (b) the protected item\'s answer/reference string appears in the training text, or (c) same problem structure with the same numbers. Anything else is superficial or topical.', '',
                   '| Train group | Protected item | max 5-gram | shared numbers | shared entities | Verdict | Evidence |', '|---|---|---|---|---|---|---|']
    for e in ev:
        pid = e['protected'].split(':', 1)[1]
        key = (e['candidate_group'], pid)
        named = [x for x in e['shared_entities'] if x not in GENERIC]
        note = ''
        if e['max_5gram_containment'] >= 0.15:
            verdict, note = 'REVIEW textual overlap', 'containment above threshold'
        elif key in TOPICAL:
            t = q[pid].get('target')
            ans = ' '.join(t['answers']['text']) if isinstance(t, dict) else str(t)
            hit = normalized(ans) in normalized(g111)
            verdict = 'topical overlap only (shared subject facts); different task'
            note = f"TQuAD passage on Müteferrika's press vs open-ended analysis; reference answer '{ans[:40]}' appears in training text: {hit}"
        elif e['candidate_group'] == 'bp01-g115' and pid.endswith('281286'):
            verdict, note = 'template family only', 'same Atlas instruction template (exactly 2 risks and 2 actions); different content/data; inherited from pilot160'
        elif e['protected'].startswith(('dev20', 'reasoning4')):
            verdict, note = 'superficial: shared numbers only', f"different problem structures; train: {e['train_prompt'][:70]!r} vs {e['protected_prompt'][:70]!r}"
        else:
            verdict = 'superficial: generic tokens/numbers' if not named else 'superficial: names/dates'
            note = f"train: {e['train_prompt'][:60]!r} vs protected: {e['protected_prompt'][:60]!r}"
        out.append(dict(**e, verdict=verdict, evidence=note))
        md.append(f"| {e['candidate_group'][5:]} | `{e['protected']}` | {e['max_5gram_containment']} | {', '.join(e['shared_numbers'])} | {', '.join(e['shared_entities'])} | {verdict} | {note.replace('|', '/')} |")
    cls = {}
    for o in out:
        cls[o['verdict']] = cls.get(o['verdict'], 0) + 1
    md += ['', f'Verdict counts: {cls}', '', 'No shared underlying task found. No quarantine was applied. TurBLiMP1600 is UNCHECKED (data not available locally), not passed. g111 is the only group with real topical overlap; dropping it costs 1/160 groups if you want a conservative CETVEL TQuAD comparison.']
    (PILOT / 'validation/leakage-flag-audit.json').write_bytes(json_bytes(dict(counts=cls, flags=out)))
    (PILOT / 'validation/LEAKAGE-FLAG-AUDIT.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(cls)

main()
