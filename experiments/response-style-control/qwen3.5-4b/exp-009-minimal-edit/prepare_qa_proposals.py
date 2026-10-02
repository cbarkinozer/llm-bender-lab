"""Create isolated QA proposals, never overwrite human-reviewed originals."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPOSALS = {
    'me-007': ('Fiilin çatısını koru.', 'Hava yolu temsilcisi kaçırılan uçuş için yeni bir bilet düzenledi; ikinci denemede sorun tekrarlamayınca işlem özeti oluşturuldu.'),
    'me-068': ('Desteklenmeyen iddiaları ve süslemeyi kaldır.', 'Olabilir, ancak yalnızca akşamları yavaşlaması sağlayıcının bilerek kısıtladığını göstermez. Ağ yoğunluğu veya evdeki bağlantının paylaşılması da neden olabilir. Nedeni araştırmak için aynı bağlantıda farklı saatlerde hız ölçümlerini karşılaştırabilirsiniz.'),
    'me-073': ('İstenen sözcüğü büyük/küçük harfini değiştirmeden kopyala.', 'kir'),
    'me-082': ('Ürün belleği hakkında genel iddia yerine mevcut bağlamı belirt.', 'Dünkü konuşma bu bağlamda görünmüyor. Konuyu kısaca hatırlatırsanız oradan devam edebiliriz.'),
    'me-083': ('Mutlak kira bilinmeden elde kalan geliri hesaplama.', 'Verdiğin bilgilere göre Eskişehir’deki uzaktan iş daha uygun olabilir: ailen orada ve işe gidip gelmen gerekmez.\n\nAncak kira tutarları belirtilmediği için 25 bin TL’lik maaş farkının ne kadarını kiranın götüreceğini veya hangi seçenekte elinde daha fazla para kalacağını söyleyemeyiz. İki seçeneği gerçek kira ve diğer giderlerle karşılaştırmak gerekir.\n\nİstanbul’daki iş belirgin biçimde daha iyi bir kariyer fırsatı sunuyorsa bu da kararını değiştirebilir.'),
    'me-058': ('Geri alınabilir denemeye odaklan; gereksiz talimatları kaldır.', 'Sabahları vaktiniz olduğuna göre denemeye değer. Bu, geri alınabilir bir değişiklik. Bir iki hafta sabah koşup nasıl gittiğine bakabilir, size uymazsa akşama dönebilirsiniz. Deneme sonunda sürdürebildiğiniz ve size daha uygun gelen saati seçebilirsiniz.'),
    'me-071': ('İstenen ayrımı koru; gereksiz kurumsal istisnayı kaldır.', 'Hayır, bu koşulu sağlamıyorsunuz. "Doktora derecesi", doktora programını tamamlayanlara verilen akademik derecedir. Tıp fakültesini bitirmek "doktor" (hekim) unvanı kazandırır, ancak doktora derecesi sayılmaz.'),
    'me-089': ('Tavsiye ve düzelme tahmini yerine kısa karşılık ver.', 'Yeni evin henüz sana aitmiş gibi gelmiyor.'),
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--approve', action='store_true', help='Only with explicit user approval of the scoped QA fixes')
    args = parser.parse_args()
    source = HERE/'reviewed-v1'
    version = 'reviewed-v2' if args.approve else 'qa-proposals-v1'
    dest = HERE/version
    if dest.exists():
        raise ValueError('Refusing to overwrite proposals')
    manifest = json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Parent hash changed: '+name)
    rows = []
    for split in ('train', 'validation'):
        rows.extend(json.loads(line) for line in (source/f'{split}-reviewed.jsonl').read_text(encoding='utf-8').splitlines())
    by_id = {r['id']: r for r in rows}
    # Preserve the rest of these longer explanations verbatim.
    old = by_id['me-042']['desired_answer']
    needle = 'Aynı fotoğrafın kopyalarını ve açılmayan dosyaları silin.'
    assert old.count(needle) == 1
    PROPOSALS['me-042'] = ('Açılmayan fotoğrafları kurtarma olasılığı için sakla; silmeden önce yedeği doğrula.', old.replace(needle, 'Aynı fotoğrafın kopyalarını belirleyin; silme işlemini ikinci yedeği oluşturup doğruladıktan sonra yapın. Açılmayan dosyaları hemen silmeyin, kurtarma ihtimali için ayrı bir klasörde saklayın.'))
    old = by_id['me-043']['desired_answer']
    needle = 'Bu yöntemle sonuç değişmediğinde bile bir şey öğrenirsiniz: O değişken büyük olasılıkla sorunun kaynağı değildir.'
    assert old.count(needle) == 1
    PROPOSALS['me-043'] = ('Tek denemede fark görülmemesi değişkeni elemez.', old.replace(needle, 'Bu yöntemle sonuç değişmediğinde bile bir şey öğrenirsiniz: Denediğiniz değişiklik o denemede belirgin bir fark yaratmamıştır; bu, değişkenin etkisiz olduğunu tek başına göstermez.'))
    changes = []
    for id_, (reason, answer) in sorted(PROPOSALS.items()):
        row = by_id[id_]
        assert answer.strip() and answer != row['desired_answer']
        changes.append(dict(id=id_, split=row['split'], conversation='\n\n'.join(m['role']+': '+m['content'] for m in row['messages']), previous_answer=row['desired_answer'], proposed_answer=answer, reason=reason, approval='user-authorized-direct-qa' if args.approve else 'pending'))
        row['parent_desired_answer'] = row['desired_answer']
        row['desired_answer'] = answer
        row['qa_proposal_reason'] = reason
    for row in rows:
        row['dataset_version'] = version
        row['answer_status'] = 'qa-corrected-user-authorized' if args.approve else 'qa-proposals-pending-user-approval'
    assert len(rows) == 100 and sum(r['split'] == 'train' for r in rows) == 80
    dest.mkdir()
    for split in ('train', 'validation'):
        subset = sorted((r for r in rows if r['split'] == split), key=lambda r:r['id'])
        (dest/f'{split}-reviewed.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in subset), encoding='utf-8', newline='\n')
    (dest/'changes.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    with (dest/'changes.csv').open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(changes[0]))
        writer.writeheader()
        writer.writerows(changes)
    readable = ('# QA düzeltmeleri — kullanıcı yetkisiyle uygulandı\n\n' if args.approve else '# QA düzeltme önerileri — onay bekliyor\n\n') + 'Argilla değerlendirmeleri değiştirilmedi. 9 eğitim, 1 doğrulama düzeltmesi.\n\n'
    for c in changes:
        readable += f"## {c['id']} ({c['split']})\n\n{c['reason']}\n\n### Önceki yanıt\n\n{c['previous_answer']}\n\n### Önerilen yanıt\n\n{c['proposed_answer']}\n\n"
    (dest/'REVIEW.md').write_text(readable, encoding='utf-8', newline='\n')
    report = dict(status='qa-corrections-applied' if args.approve else 'pending-user-approval', changes=len(changes), train_changes=9, validation_changes=1, splits={'train':80,'validation':20}, parent_manifest_sha256=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(), annotations_modified=False, training_started=False, unchanged_rows=90, remaining_gates=['revised prompt benchmark audit', 'tokenization and final-assistant-only masking', 'training configuration and GPU preflight'], files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()})
    (dest/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}, indent=2))

if __name__ == '__main__':
    main()
