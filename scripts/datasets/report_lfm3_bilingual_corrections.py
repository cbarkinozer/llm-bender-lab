"""Single owner report: the 15 medium-severity flagged originals with exact before/after text and a fix/retain/drop
recommendation. NOTHING is applied; the reviewed originals and all data files are unchanged."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import PILOT, json_bytes, read_jsonl

PHRASE = 'Not: Ürün özellikleri ve gizlilik politikaları sık değişir; karar vermeden önce güncel resmî sayfaları kontrol edin.'
# group -> dict(field, edits=[(before, after)], rec, why, evidence)
C = {
    'g153': dict(field='assistant', rec='FIX', pri='P1',
                 why='Prompt is internally inconsistent (stated mean density 1.012x1.007=1.019084 vs 1.019583 implied by the 1:1.4 volumes; recomputed). The reviewed reasoning says the inconsistency must be mentioned but the answer omits it.',
                 edits=[('- Dip tabakası: 607 × 1,4 ÷ 2,4 ≈ 354,08 km³\n',
                         '- Dip tabakası: 607 × 1,4 ÷ 2,4 ≈ 354,08 km³\n\nNot: Verilen ortalama yoğunluk koşulu (1,012 × 1,007 = 1,019084 g/cm³) hacim oranından hesaplanan değerle (≈ 1,019583 g/cm³) tutarsızdır; sonuç hacim oranına göre verilmiştir.\n')]),
    'g028': dict(field='user', rec='FIX', pri='P1',
                 why='Ambiguous constraint: if the 1100 TL limit covered the whole 62.4 L trip (~2,808 TL) it would be infeasible; the answer silently treats it as the cost of refuelled fuel (535.68 TL).',
                 edits=[('toplam yakıt maliyetinin 1100 TL’yi aşmaması', 'ikmal edilen yakıtın toplam maliyetinin 1100 TL’yi aşmaması')]),
    'g035': dict(field='user', rec='RETAIN', pri='P1',
                 why='Shift length is missing, but the reviewed answer opens by naming this gap and states its assumption (4 h shifts, all six assigned), which is the behaviour the system prompt asks for ("Belirsizliği belirt"). Fixing the prompt would make that answer redundant (larger rewrite). Alternative: DROP if you prefer well-posed tasks only.',
                 edits=[("toplam çalışan-saat 24'ü geçmemelidir", "her vardiya 4 saat sürer ve toplam çalışan-saat 24'ü geçmemelidir   [only if FIX; answer paragraphs 1 and 4 would then need shortening]")]),
    'g068': dict(field='assistant', rec='FIX', pri='P1',
                 why='Objective typos: "taka" should be "takas" (trade-off); "Takayı" should be "Takası".',
                 edits=[('Buradaki taka, su kuşlarının', 'Buradaki takas, su kuşlarının'), ('Takayı görünür kılan adım', 'Takası görünür kılan adım')]),
    'g030': dict(field='assistant', rec='FIX', pri='P2',
                 why='Wrong attribution. VERIFIED against the official Constitution text (mevzuat.gov.tr/mevzuatmetin/1.5.2709.pdf): Art. 56 says preventing pollution is "Devletin ve vatandaşların ödevidir".',
                 edits=[('çevre kirlenmesini önlemeyi doğrudan devletin ödevi sayar', 'çevre kirlenmesini önlemeyi devletin ve vatandaşların ödevi sayar')]),
    'g139': dict(field='assistant', rec='FIX', pri='P2',
                 why='Misquote. VERIFIED against the official text: Art. 65 reads "malî kaynaklarının yeterliliği ölçüsünde". (My earlier concern about the Art. 57 comma was wrong: the official text has a comma; no change there.)',
                 edits=[('“mali kaynakların yeterliliği ölçüsünde”', '“mali kaynaklarının yeterliliği ölçüsünde”')]),
    'g012': dict(field='assistant', rec='FIX', pri='P2',
                 why='Inconsistent rule: the first two conjunction "ki" get commas, the third is said never to; a comma before purpose-result "ki" is optional, not forbidden.',
                 edits=[('ve kendisinden önce virgül konmaz, tıpkı', 've önünde virgül zorunlu değildir, tıpkı')]),
    'g095': dict(field='assistant', rec='FIX', pri='P2',
                 why='Incomplete citation (secondary sources): HMK 116/1-b and 117 are right; the arbitration objection is also governed by HMK 413.',
                 edits=[('cevap süresi içinde ileri sürülmek zorundadır (HMK m. 117)', 'cevap süresi içinde ileri sürülmek zorundadır (HMK m. 117 ve 413)')]),
    'g075': dict(field='assistant', rec='FIX', pri='P3',
                 why='Time-sensitive product/privacy-policy claims (Alexa has no Turkish; 2025 Amazon cloud processing; Google retention options) will go stale.',
                 edits=[('ancak kurulumu daha fazla teknik bilgi ister.\n', 'ancak kurulumu daha fazla teknik bilgi ister.\n\n' + PHRASE + '\n')]),
    'g154': dict(field='assistant', rec='FIX', pri='P3',
                 why='"Doğru künyeli" examples were requested. The Kuvâyi Milliye line was VERIFIED (Book 8 of Kuvâyi Milliye per secondary sources). "Açların Gözbebekleri" exists (written in Moscow, first free-verse poem) but its content description is unverified, so the minimal fix keeps only the verified Salkımsöğüt description.',
                 edits=[('“Açların Gözbebekleri” açlık çeken yığınları, “Salkımsöğüt” vurulup suya düşen bir Kızıl süvariyi anlatır.', '“Salkımsöğüt” vurulup suya düşen bir Kızıl süvariyi anlatır.')]),
    'g066': dict(field='assistant', rec='RETAIN', pri='P3', edits=[], why='No error found. Von Hannover (No. 2) / Axel Springer criteria and Art. 17/28, ECHR 8/10 are real; Law 5651 blanket-block case law not verified. Optional lawyer check.'),
    'g067': dict(field='assistant', rec='RETAIN', pri='P3', edits=[], why='No error found; TTK 369/553/555/557, TBK 50-51, Law 3095 not independently verified. Optional lawyer check.'),
    'g102': dict(field='assistant', rec='RETAIN', pri='P3', edits=[], why='No error found; HMK 27, Const. 36, ECHR 6 plausible/standard; "Yargıtay bozma sebebidir" not verified. Optional lawyer check.'),
    'g112': dict(field='assistant', rec='RETAIN', pri='P3', edits=[], why='TTK 393 (participation ban) confirmed by secondary sources; TTK 202, 369, 553 unverified but plausible. Optional lawyer check.'),
    'g159': dict(field='assistant', rec='RETAIN', pri='P3', edits=[], why='Const. 38/152, TCK 2 and 2/3, ECHR 7, Kokkinakis v. Greece are standard; not independently verified. Optional lawyer check.'),
}
ORDER = ['g153', 'g028', 'g035', 'g068', 'g030', 'g139', 'g012', 'g095', 'g075', 'g154', 'g066', 'g067', 'g102', 'g112', 'g159']


def main():
    orig = {o['group_id']: o for o in read_jsonl(PILOT / 'data/source-originals.jsonl')}
    md = ['# Correction report: the 15 medium-severity flagged originals', '',
          'Nothing is applied. Exact before/after text is shown for every proposed edit; "RETAIN" items have no edit. Verification used the official Constitution PDF where marked VERIFIED; other web checks used secondary sources only.', '']
    items = []
    for g in ORDER:
        c = C[g]
        o = orig[f'bp01-{g}']
        text = o[c['field']]
        md += [f"## {g} · {c['pri']} · **{c['rec']}** · `{o['source_row_id']}`", '', f"Prompt: {o['user'][:260].replace(chr(10), ' ')}", '', f"**Why:** {c['why']}", '']
        for k, (before, after) in enumerate(c['edits'], 1):
            if c['rec'] == 'FIX':
                assert before in text, (g, before)
            md += [f"**Edit {k} ({c['field']}) - before:**", '', '```text', before, '```', '', '**after:**', '', '```text', after, '```', '']
        if not c['edits']:
            md += ['(no text change proposed)', '']
        items.append(dict(group_id=f'bp01-{g}', field=c['field'], recommendation=c['rec'], priority=c['pri'], why=c['why'],
                          edits=[dict(before=b, after=a) for b, a in c['edits']] if c['rec'] == 'FIX' else [], applied=False))
    fixes = [g for g in ORDER if C[g]['rec'] == 'FIX']
    user_fix = [g for g in fixes if C[g]['field'] == 'user']
    md += ['## What "apply recommended" would change', '',
           f"- FIX {len(fixes)} groups: {', '.join(fixes)}. RETAIN {15 - len(fixes)}: {', '.join(g for g in ORDER if C[g]['rec'] == 'RETAIN')}. DROP 0.",
           f"- Prompt edits: {', '.join(user_fix)} (all four direction rows of the group change: TR prompt and its EN translation). Answer edits: {', '.join(g for g in fixes if C[g]['field'] == 'assistant')}.",
           '- Every fixed group needs its EN text updated (small edits to the matching `translations/part-*.txt` entries); TR rows change only at the quoted spans; group counts stay 160/640.',
           '- Consequences: new dataset revision (new hashes in build-manifest, token plan and exp configs recalculated; the supervised-token totals shift by a few dozen tokens), `source-originals.jsonl` keeps the unedited reviewed text and gains a `correction` record. The frozen eval is unaffected.', '']
    (PILOT / 'reports/CORRECTION-REPORT.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    (PILOT / 'reports/proposed-corrections.json').write_bytes(json_bytes(items))
    print(len(items), 'groups;', len(fixes), 'fix')


main()
