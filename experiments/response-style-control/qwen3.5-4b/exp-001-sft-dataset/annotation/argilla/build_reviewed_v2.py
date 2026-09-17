"""Build reviewed-v2 from the second Argilla review pass.

The source candidates are immutable.  This script snapshots the 30 recorded
Argilla decisions, applies the reviewer's literal repairs, then performs only
narrow repairs for repeated defects demonstrated by those reviews.  Every row
left in the pending output still requires human review.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "reviewed-v1"
OUT = ROOT / "reviewed-v2"
INPUT = V1 / "pending-after-known-repairs-v1.csv"
V1_ACCEPTED = V1 / "accepted-reviewed.csv"
DATASET_ID = "b4d31227-9cba-4a99-9256-a8ada06ea7ca"
API_URL = os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900").rstrip("/")
API_KEY = os.getenv("ARGILLA_API_KEY", "argilla.apikey")
REVIEWER_ID = "a3cedf29-50c3-4f85-b552-6317636192a5"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_reviews() -> dict[str, dict]:
    """Fetch all saved responses through Argilla's REST API.

    The SDK cannot deserialize this old dataset's obsolete suggestion objects;
    the REST representation remains complete and is the authoritative review
    record for this migration.
    """
    endpoint = f"{API_URL}/api/v1/datasets/{DATASET_ID}/records/search"
    headers = {"X-Argilla-Api-Key": API_KEY}
    by_id: dict[str, dict] = {}
    offset = 0
    while True:
        response = requests.post(
            endpoint,
            headers=headers,
            params={"offset": offset, "limit": 1000, "include": "responses"},
            json={},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload["items"]:
            record = item["record"]
            responses = [
                item for item in record["responses"]
                if item["user_id"] == REVIEWER_ID and item["status"] in {"submitted", "discarded"}
            ]
            if len(responses) > 1:
                raise ValueError(f"Multiple saved responses for {record['external_id']}")
            if responses:
                by_id[record["external_id"]] = responses[0]
        offset += len(payload["items"])
        if offset >= payload["total"]:
            break
    if len(by_id) != 30:
        raise ValueError(f"Expected exactly 30 saved second-pass reviews, found {len(by_id)}")
    return by_id


def value(response: dict, field: str) -> str:
    return response.get("values", {}).get(field, {}).get("value", "")


def set_messages(row: dict[str, str], *, user: str | None = None, assistant: str | None = None, note: str) -> None:
    messages = json.loads(row["messages"])
    if [message["role"] for message in messages] != ["user", "assistant"]:
        raise ValueError(f"{row['id']}: invalid message order")
    if user is not None:
        messages[0]["content"] = user
    if assistant is not None:
        messages[1]["content"] = assistant
    row["messages"] = json.dumps(messages, ensure_ascii=False)
    row["quality_status"] = "accepted"
    row["reviewer"] = "cbark"
    row["notes"] = (row.get("notes", "") + f" | {note}").strip(" |")


# These are literal applications of notes where the text field was not itself
# the desired final field (or where the note expressly supplied a better answer).
EXPLICIT_REPAIRS = {
    "bare_gec__017": {"assistant": "Tren dağ geçidine yaklaşırken telefonların bağlantısı birkaç dakika kesildi; yalnızca bu ayrıntı gözden kaçtı."},
    "bare_gec__446": {"assistant": "Beklenmedik gecikmeye rağmen, yerel tarihçi sözlü tarih kayıtlarını ailelere göre sınıflandırdı; sonuç aynı gün kayda geçti; rehberlerde de aynı öneriyi yineledi."},
    "bare_gec__378": {"assistant": "Sen toplantıya katılacaksın; toplantıdan önce tur rehberi, kalabalık büyümeden grubu üst kata çıkardı; toplantı başlamadan birkaç dakika önce not, toplantı tutanağına eklendi."},
    "bare_gec__340": {"assistant": "Sen toplantıya katılacaksın; toplantıdan önce okul yönetimi müze gezisinin programını sınıflarla paylaştı; plan yeniden gözden geçirildikten sonra kayıtlar aynı gün arşive taşındı."},
    "bare_qa_span__165": {"user": "Kaynak: Kayıtlara göre Osmanlı Devleti'nin kuruluş yılı 1299 yılına denk gelmektedir.\n\nSoru: Osmanlı Devleti'nin kuruluş yılı hangisidir?\n\nCevap:"},
    "bare_qa_span__131": {"user": "Kaynak: Kayıtlara göre Python programlama dilinin ilk sürümünün yayımlanması 1991 yılına denk gelmektedir.\n\nSoru: Python programlama dilinin ilk sürümünün yayımlandığı yıl hangisidir?\n\nCevap:"},
    "bare_qa_span__375": {"user": "Kaynak: Dünya Kupası ilk kez Uruguay'da düzenlenmiştir.\n\nSoru: Dünya Kupası'nın ilk düzenlendiği ülke neresidir?\n\nCevap:", "assistant": "Uruguay"},
    "terse_summary__114": {"user": "Başlık: Maç sonucu\n\nMetin: Gençlerbirliği, Kocaeli'de oynanan deplasman maçında Kuzey Birlik'i 3-0 yendi. Maçın 12. dakikasında atılan gol sonucu belirledi. Bu galibiyetle Gençlerbirliği, puan durumunda dördüncü sıraya yükseldi.\n\nÖzet:", "assistant": "Gençlerbirliği ile Kuzey Birlik arasındaki maç 3-0 sonuçlandı ve Gençlerbirliği bu sonuçla dördüncü sıraya yükseldi."},
    "numeric_entity_precision_qa__484": {"user": "Kaynak: Şehir Hastanesi tarafından Malatya'da tanıtılan Ateş Ölçüm Cihazı sigorta kapsamına alındı. Fizik Tedavi Paketi ise yalnızca özel kliniklerde sunuldu. Değerlendirme, klinik verilerle desteklendi.\n\nSoru: Aşağıdaki metne göre, 'yalnızca özel kliniklerde sunuldu' hangi ürün için geçerli?\n\nCevap:", "assistant": "Fizik Tedavi Paketi"},
    "numeric_entity_precision_qa__444": {"user": "Kaynak: Yeşil Mahalle Kooperatifi, Çanakkale'de bölgedeki geri dönüşüm noktalarını arttırdı. Kent Market Zinciri ise aynı dönemde yeni bir gönüllü programı başlattı. Karar, muhtarlık kararıyla kesinleşti.\n\nSoru: Aşağıdaki metne göre, 'bölgedeki geri dönüşüm noktalarını arttırdı' eylemini hangi kurum gerçekleştirdi?\n\nCevap:"},
    "open_ended_counterexample__001": {"assistant": "Hafta içi için birkaç kolay yemek belirleyip alışverişi buna göre planlamak iyi bir başlangıç olur. Mümkünse hafta sonu bazı malzemeleri önceden hazırlayabilir veya birkaç porsiyon fazla pişirip buzdolabında ya da dondurucuda saklayabilirsin. Böylece akşam ne yiyeceğine karar vermek ve sıfırdan yemek yapmak yerine, hazır bir seçeneği kısa sürede tamamlaman yeterli olur."},
    "open_ended_counterexample__067": {"assistant": "İki haftayı küçük denemelere böl. İlk hafta her gün kısa bir konu seçip onu 2-3 dakikada tek bir ana fikir ve bir örnek üzerinden anlatmaya çalış. Nerede dağıldığını fark etmek için mümkünse ses kaydı al veya anlatımdan sonra kısa not çıkar. İkinci hafta ise aynı yöntemi bir başkasına anlatırken uygula ve sonunda ondan ne anladığını bir iki cümleyle özetlemesini iste. Böylece hem anlatımını sadeleştirir hem de hangi noktalarda gereksiz ayrıntıya girdiğini daha kolay fark edersin."},
    "open_ended_counterexample__141": {"assistant": "Önce sorunun internet hızından mı yoksa Wi-Fi kapsamasından mı kaynaklandığını ayırmaya çalış. Aynı cihazla modemin yanında ve sorun yaşadığın odalarda hız testi yap. Uzak odalarda belirgin düşüş varsa modemi daha merkezi ve açık bir konuma taşımayı dene. Bu da yeterli olmazsa mesh sistem veya ek erişim noktası gibi çözümleri değerlendirebilirsin."},
    "open_ended_counterexample__264": {"user": "Samimi ve kişisel bir şekilde tebrik etmek için uğraşıyorum ama mesaj uzadıkça odağı kendime çeviriyormuşum gibi oluyor. Nerede hata yaptığımı nasıl anlayabilirim?", "assistant": "Tebriğin merkezinde onun başarısı, gösterdiği çaba ve bunun sende uyandırdığı takdir kalsın. Kendi hislerinden bahsedeceksen bunu kısa tut ve tekrar onun başarısına bağla. Mesajı bitirdikten sonra ‘Bu cümle karşı tarafı mı anlatıyor, yoksa beni mi?’ diye her cümleyi kontrol etmek iyi bir ölçüt olabilir."},
}


def repair_repeated_patterns(rows: list[dict[str, str]]) -> Counter[str]:
    """Repair only repeated defects evidenced by second-pass reviews."""
    counts: Counter[str] = Counter()
    malformed_year = re.compile(r"(Kaynak: Kayıtlara göre .+?), (\d{4}) yılına denk gelmektedir\.")
    for row in rows:
        messages = json.loads(row["messages"])
        user, assistant = messages
        changed = False
        # e.g. "... kurulduğu, 1299 yılına denk gelmektedir" -> a grammatical source sentence.
        replaced, n = malformed_year.subn(r"\1 yıl \2'dir.", user["content"])
        if n:
            user["content"] = replaced
            counts["qa_malformed_year_source"] += 1
            changed = True
        # The reviewer consistently asked for the copula in price questions.
        if row["category"] == "numeric_entity_precision_qa" and "belirlenen ücret kaç TL?" in user["content"]:
            user["content"] = user["content"].replace("belirlenen ücret kaç TL?", "belirlenen ücret kaç TL'dir?")
            counts["numeric_price_question_copula"] += 1
            changed = True
        if row["category"] == "numeric_entity_precision_qa":
            # "Ateş Ölçüm Cihazı ürünü" is redundant when the named item is
            # already the subject. Limit this to the two generated templates.
            updated = re.sub(r"(tanıtılan .+?) ürünü ([^.]+\.)", r"\1 \2", user["content"])
            updated = re.sub(r"([A-ZÇĞİÖŞÜ][^.]+?) ürünü ise", r"\1 ise", updated)
            if updated != user["content"]:
                user["content"] = updated
                counts["numeric_redundant_product_word"] += 1
                changed = True
            if "geri dönüşüm noktalarını artırdı" in user["content"]:
                user["content"] = user["content"].replace("geri dönüşüm noktalarını artırdı", "geri dönüşüm noktalarını arttırdı")
                counts["numeric_arttirdi_spelling"] += 1
                changed = True
        if changed:
            row["messages"] = json.dumps(messages, ensure_ascii=False)
            row["notes"] = (row.get("notes", "") + " | second-pass repeated-pattern repair").strip(" |")
    return counts


def main() -> None:
    pending, fieldnames = load_csv(INPUT)
    old_accepted, old_fieldnames = load_csv(V1_ACCEPTED)
    if fieldnames != old_fieldnames:
        raise ValueError("v1 accepted and pending schemas differ")
    if len(pending) != 2400 or len(old_accepted) != 47:
        raise ValueError("Unexpected reviewed-v1 inventory")
    reviews = fetch_reviews()
    pending_by_id = {row["id"]: row for row in pending}
    if set(reviews) - set(pending_by_id):
        raise ValueError("Argilla response references a record outside the v1 pending pool")

    accepted_now: list[dict[str, str]] = []
    for candidate_id, response in sorted(reviews.items()):
        row = dict(pending_by_id[candidate_id])
        repair = EXPLICIT_REPAIRS.get(candidate_id)
        if repair:
            set_messages(row, user=repair.get("user"), assistant=repair.get("assistant"), note="Argilla v2 explicit review repair")
        else:
            # Submitted rows preserve the reviewer's text exactly.
            user = value(response, "reviewed_user_input") or json.loads(row["messages"])[0]["content"]
            assistant = value(response, "reviewed_target")
            if not assistant:
                raise ValueError(f"{candidate_id}: saved review has no target")
            set_messages(row, user=user, assistant=assistant, note="Argilla v2 submitted review")
        accepted_now.append(row)

    remaining = [dict(row) for row in pending if row["id"] not in reviews]
    for row in remaining:
        row["quality_status"] = "needs_review"
    pattern_counts = repair_repeated_patterns(remaining)
    if len(accepted_now) != 30 or len(remaining) != 2370:
        raise ValueError("Second-pass split count mismatch")

    OUT.mkdir(exist_ok=True)
    accepted_all = old_accepted + accepted_now
    write_csv(OUT / "accepted-reviewed.csv", accepted_all, fieldnames)
    write_csv(OUT / "pending-after-v2.csv", remaining, fieldnames)
    decision_snapshot = {
        "version": "argilla-v2",
        "dataset_id": DATASET_ID,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_id": REVIEWER_ID,
        "review_count": len(reviews),
        "responses": reviews,
    }
    snapshot_path = OUT / "argilla-v2-decisions.json"
    snapshot_path.write_text(json.dumps(decision_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "version": "reviewed-v2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "v1_accepted_count": len(old_accepted),
        "v2_reviewed_count": len(accepted_now),
        "accepted_total_count": len(accepted_all),
        "pending_count": len(remaining),
        "explicit_review_repair_ids": sorted(EXPLICIT_REPAIRS),
        "repeated_pattern_repairs": dict(pattern_counts),
        "input_sha256": {INPUT.name: sha256(INPUT), V1_ACCEPTED.name: sha256(V1_ACCEPTED)},
        "decision_snapshot_sha256": sha256(snapshot_path),
        "output_sha256": {
            "accepted-reviewed.csv": sha256(OUT / "accepted-reviewed.csv"),
            "pending-after-v2.csv": sha256(OUT / "pending-after-v2.csv"),
        },
        "category_counts": {"accepted": Counter(row["category"] for row in accepted_all), "pending": Counter(row["category"] for row in remaining)},
        "pending_quality_status": "needs_review for every row",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
