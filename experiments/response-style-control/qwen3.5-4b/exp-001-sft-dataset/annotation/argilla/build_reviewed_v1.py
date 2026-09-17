"""Build the first reviewed layer from the 47 Argilla v1 decisions.

The raw candidate CSVs are never modified. This script emits one accepted
reviewed set and one pending set, preserving all source metadata and applying
the reviewer's explicit repairs to the 19 discarded rows.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reviewed-v1"
DECISIONS_PATH = OUT / "argilla-v1-decisions.json"
CANDIDATE_FILES = (
    "bare_gec.csv", "bare_qa_span.csv", "terse_summary.csv",
    "numeric_entity_precision_qa.csv", "open_ended_counterexample.csv",
)

# Each patch is a direct application of the reviewer's feedback. ``user`` is
# supplied only when the source prompt itself requires repair.
PATCHES = {
    "bare_gec__098": {"assistant": "Uçağın kapısı erken kapanınca üç yolcu bir sonraki sefere aktarıldı, karar kimseyi sürprize uğratmadı."},
    "bare_gec__207": {
        "user": "Verilen cümlenin yazım hatalarını düzeltin.\nHatalı Cümle: Hava yolu temsilcisi kaçırılan uçuş için yeni bir bilet düzenledi; ikinci denemede sorun tekrarlamıyınca işlem özeti oluşturuldu.\nDüzeltilmiş hali:",
        "assistant": "Hava yolu temsilcisi kaçırılan uçuş için yeni bir bilet düzenledi; ikinci denemede sorun tekrarlanmayınca işlem özeti oluşturuldu.",
    },
    "bare_qa_span__164": {"user": "Kaynak: Fransız İhtilali 1789 yılında patlak verdi.\n\nSoru: Fransız İhtilali'nin patlak verdiği yıl hangisidir?\n\nCevap:", "assistant": "1789"},
    "bare_qa_span__303": {"user": "Kaynak: Son sayıma göre yeni açılan otel sayısı 45 olarak belirlendi.\n\nSoru: Yeni açılan otel sayısı kaçtır?\n\nCevap:", "assistant": "45"},
    "bare_qa_span__359": {"user": "Kaynak: Silikon çip üretiminde öncü bir fabrika, Güney Kore'nin Güney Chungcheong eyaletinde konumlanmıştır.\n\nSoru: Silikon çip üretiminde öncü bir fabrika nerededir?\n\nCevap:", "assistant": "Güney Chungcheong eyaletinde"},
    "bare_qa_span__457": {"user": "Kaynak: Yeni açılan otelin öne çıkan özelliği deniz manzaralı teraslı odalarıdır.\n\nSoru: Yeni açılan otelin öne çıkan özelliği nedir?\n\nCevap:", "assistant": "deniz manzaralı teraslı odalar"},
    "bare_qa_span__505": {"user": "Kaynak: Mısır piramitleri Antik Mısır döneminde inşa edilmiştir.\n\nSoru: Mısır piramitleri Antik Mısır döneminde mi inşa edilmiştir?\n\nCevap:", "assistant": "Evet"},
    "terse_summary__231": {"assistant": "Araştırmacılar, 1200 katılımcıyla altı ay süren çalışmada yazılım güncelleme sıklığı ile veri güvenliğinin güçlenmesi arasında bağlantı bulduklarını duyurdu."},
    "terse_summary__261": {"user": "Başlık: Yerel haber\n\nMetin: Ayşe Kaya (45), Antalya'da otuz yıldır sürdürdüğü el işi üretimi sayesinde belediyeden destek almaya hak kazandı. Komşuları, Ayşe Kaya'nın azmini örnek gösteriyor.\n\nÖzet:", "assistant": "Ayşe Kaya, otuz yıllık el işi üretimi deneyimiyle belediyeden destek almaya hak kazandı."},
    "terse_summary__268": {"assistant": "Marmara Teknoloji, yaklaşık 600 çalışanıyla ikinci çeyrek gelirinin önceki yılın aynı dönemine göre yüzde 18 artarak 2,7 milyar liraya ulaştığını duyurdu."},
    "terse_summary__340": {"user": "Başlık: Altyapı arızası\n\nMetin: Edirne'de ana su hattında meydana gelen arıza nedeniyle yol bir süre trafiğe kapatıldı. Olay yerine sevk edilen belediye ekipleri, bir gün içinde arızaya müdahale etti.\n\nÖzet:", "assistant": "Belediye ekipleri, Edirne'deki ana su hattı arızasına bir gün içinde müdahale etti; yol bir süre trafiğe kapatıldı."},
    "numeric_entity_precision_qa__015": {"user": "Kaynak: İl Spor Federasyonu tarafından Antalya'da tanıtılan Sağlık Tarama Modülü ürünü kulüplerle paylaşıldı. Performans Takip Uygulaması ürünü ise milli takıma entegre edildi.\n\nSoru: Aşağıdaki metne göre, 'kulüplerle paylaşıldı' hangi ürün için geçerli?\n\nCevap:", "assistant": "Sağlık Tarama Modülü"},
    "numeric_entity_precision_qa__482": {"user": "Kaynak: İl Milli Eğitim Müdürlüğü tarafından Trabzon'da yayımlanan raporda sınav başarı oranı %63, devamsızlık oranı ise %55 olarak kaydedildi. Bilgi, veli toplantısında paylaşıldı.\n\nSoru: Aşağıdaki metne göre, devamsızlık oranı kaç olarak kaydedildi?\n\nCevap:", "assistant": "%55"},
    "open_ended_counterexample__120": {"assistant": "Bence önce konuşmanın sonunda gerçekten neyin sende kaldığını görünür hale getir: devam eden işleri, tahmini sürelerini ve teslim tarihlerini kısa bir listeye dök. Sonra birkaç benzer konuşmaya dönüp bakarak hangi noktada işlerin tekrar sana kaldığını karşılaştır; örneğin görevler net mi, sorumlusu belli mi, yoksa ‘biri ilgilenir’ gibi mi kalıyor? Aynı anda yapılamayacak işleri de açıkça ortaya koyup ‘Bunu da yapacaksak hangisini erteleyelim?’ diye sormak, öncelik kararını tek başına üstlenmeni engeller. Buna rağmen işler yine sende toplanıyorsa, hangi işin erteleneceği veya kimin sorumluluğunda olacağı konusunda yöneticiden net bir karar istemek daha sağlıklı olur."},
    "open_ended_counterexample__128": {"assistant": "İlk gün, dosyaları silmeden mevcut sürümleri karşılaştır ve hangisinin gerçekten en güncel ve doğru sürüm olduğunu belirle; özellikle dosya tarihi, son değişiklik zamanı ve içerik farklarına bak. İlk hafta, bundan sonra oluşacak çalışma kopyalarını ana klasörden ayırıp düzenli bir arşiv yapısı kur. Devamında, dosya adlarında yalnızca tarihe güvenmek yerine tutarlı bir sürümleme yöntemi kullan (ör. v1, v2, v3 veya final, rev1 gibi); sistemin düzgün çalıştığından emin olduktan sonra gereksiz ve doğrulanmış eski kopyaları temizleyebilirsin."},
    "open_ended_counterexample__147": {"assistant": "Bence iki haftada hepsini bir anda toparlamaya çalışmak yerine, önce güvenli bir kopya alıp sonra yavaş yavaş tek yerde toplamaya gitmek daha rahat olur. İlk birkaç gün fotoğrafların hangi cihazlarda ve klasörlerde olduğunu çıkar; silmeye veya taşımaya başlamadan önce her kaynağın ayrı bir yedeğini al. İlk hafta fotoğrafları ortak arşive aktar ve mümkünse çekim tarihine göre klasörle; önce her şeyin eksiksiz geldiğinden emin ol. İkinci hafta arşivi birkaç gün kullanıp eksik veya yanlış tarihli dosya var mı kontrol et; her şey yolundaysa kopyaları ve gereksiz dosyaları ayıklamaya başlayabilirsin."},
    "open_ended_counterexample__157": {"assistant": "Bence önce kaybetmek istemediğin dosyaları ve klasörleri belirleyip işe oradan başlamak en mantıklısı. Ardından otomatik günlük yedeklemeyi kur ve mümkünse eski sürümlere dönebileceğin ayrı bir yedek tut; çünkü yalnızca eşitleme kullanırsan yanlışlıkla sildiğin bir dosya diğer cihazlardan da silinebilir. Sistem kurulduktan sonra da ayda bir küçük bir geri yükleme denemesi yaparak yedeğin gerçekten çalıştığından emin ol."},
    "open_ended_counterexample__256": {"user": "Ailemle taşınma kararı hakkında farklı düşünüyoruz. İlk gün, ilk hafta ve devamında neye odaklanmam mantıklı olur?", "assistant": "İlk gün, herkesin temel endişesini sözünü kesmeden dinleyip taşınma kararını etkileyen koşulları netleştir. İlk hafta kendi gerekçeni savunma tonu olmadan açıkla ve seçenekleri maliyet, iş, okul ve destek ağı gibi ortak ölçütlerle karşılaştırın. Devamında hangi bilginin eksik olduğunu ve kararın ne zaman yeniden değerlendirileceğini belirleyin; uzlaşma olmasa bile anlaşmazlığın sınırlarını bilmek ilişkiyi karardan korur."},
    "open_ended_counterexample__310": {"assistant": "Her denemede yalnızca tek bir değişkeni değiştirmek, sonucun neden farklılaştığını anlamanı kolaylaştırır. Örneğin aynı anda hem kilin kalınlığını, hem nemini hem de pişirme süresini değiştirirsen hangi değişikliğin parçayı iyileştirdiğini bilemezsin. Bunun yerine bir denemede sadece kalınlığı değiştirip diğer koşulları mümkün olduğunca sabit tutarsan sonucu önceki parçayla daha anlamlı biçimde karşılaştırabilirsin. Kısa notlar ve fotoğraflar tutmak da zamanla hangi ayarların daha iyi sonuç verdiğini görmene yardımcı olur."},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows() -> tuple[list[dict[str, str]], dict[str, str]]:
    rows, source_hashes = [], {}
    for name in CANDIDATE_FILES:
        path = ROOT / name
        source_hashes[name] = sha256(path)
        with path.open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows, source_hashes


def rewrite_messages(row: dict[str, str], patch: dict[str, str]) -> dict[str, str]:
    messages = json.loads(row["messages"])
    assert [message["role"] for message in messages] == ["user", "assistant"]
    messages[0]["content"] = patch.get("user", messages[0]["content"])
    messages[1]["content"] = patch.get("assistant", messages[1]["content"])
    updated = dict(row)
    updated["messages"] = json.dumps(messages, ensure_ascii=False)
    updated["quality_status"] = "accepted"
    updated["reviewer"] = "cbark"
    updated["notes"] = (updated.get("notes", "") + " | argilla-v1 review repair").strip(" |")
    return updated


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows, source_hashes = load_rows()
    by_id = {row["id"]: row for row in rows}
    if len(rows) != 2447 or len(by_id) != len(rows):
        raise ValueError("Expected 2,447 uniquely identified candidates")
    if set(PATCHES) - set(by_id):
        raise ValueError("A review patch references an unknown candidate")

    if not DECISIONS_PATH.exists():
        raise FileNotFoundError(f"Missing immutable review-decision snapshot: {DECISIONS_PATH}")
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    accepted_unchanged = set(decisions["submitted_ids"])
    flagged_ids = set(decisions["discarded_ids"])
    if len(accepted_unchanged) != 28 or len(flagged_ids) != 19:
        raise ValueError("Expected exactly 28 submitted and 19 reviewer-flagged rows")
    if flagged_ids != set(PATCHES):
        raise ValueError("Every reviewer-flagged row must have one explicit repair patch")
    if (accepted_unchanged | flagged_ids) - set(by_id):
        raise ValueError("The review-decision snapshot references an unknown candidate")

    accepted_ids = accepted_unchanged | set(PATCHES)
    accepted = [rewrite_messages(by_id[item_id], PATCHES[item_id]) if item_id in PATCHES else {**by_id[item_id], "quality_status": "accepted", "reviewer": "cbark"} for item_id in sorted(accepted_ids)]
    pending = [row for row in rows if row["id"] not in accepted_ids]
    if len(accepted) != 47 or len(pending) != 2400:
        raise ValueError(f"Unexpected split: {len(accepted)} accepted, {len(pending)} pending")

    OUT.mkdir(exist_ok=True)
    fieldnames = list(rows[0])
    write_csv(OUT / "accepted-reviewed.csv", accepted, fieldnames)
    write_csv(OUT / "pending-after-v1.csv", pending, fieldnames)
    manifest = {
        "version": "reviewed-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "review_source": "Argilla v1: 28 submitted unchanged, 19 reviewer-flagged rows repaired from explicit feedback",
        "accepted_count": len(accepted),
        "pending_count": len(pending),
        "patched_ids": sorted(PATCHES),
        "decision_snapshot_sha256": sha256(DECISIONS_PATH),
        "source_sha256": source_hashes,
        "output_sha256": {name: sha256(OUT / name) for name in ("accepted-reviewed.csv", "pending-after-v1.csv")},
        "category_counts": {"accepted": Counter(row["category"] for row in accepted), "pending": Counter(row["category"] for row in pending)},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
