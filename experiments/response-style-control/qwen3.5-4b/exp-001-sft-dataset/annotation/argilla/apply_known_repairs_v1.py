"""Apply narrow, reviewer-derived repairs to the pending v1 review pool.

These are mechanical/safety repairs, not approvals: all output rows remain
``needs_review`` and must still receive human review.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "reviewed-v1" / "pending-after-v1.csv"
OUTPUT = ROOT / "reviewed-v1" / "pending-after-known-repairs-v1.csv"

STORY_REPAIRS = {
    "terse_summary__086": ("Malatya'da ana su hattında meydana gelen arıza sonucu bölgede kısa süreli su kesintisi yaşandı. Olay yerine sevk edilen belediye ekipleri, yarım saat içinde müdahale etti.", "Belediye ekipleri, Malatya'daki ana su hattı arızasına yarım saat içinde müdahale etti; bölgede kısa süreli su kesintisi yaşandı."),
    "terse_summary__147": ("Adana'da ana su hattında meydana gelen arıza sonucu bölgede kısa süreli su kesintisi yaşandı. Olay yerine sevk edilen belediye ekipleri, birkaç saat içinde müdahale etti.", "Belediye ekipleri, Adana'daki ana su hattı arızasına birkaç saat içinde müdahale etti; bölgede kısa süreli su kesintisi yaşandı."),
    "terse_summary__327": ("Adana'da meydana gelen trafik kazası sonucu yol bir süre trafiğe kapatıldı. Olay yerine sevk edilen itfaiye ekipleri, yarım saat içinde müdahale etti.", "İtfaiye ekipleri, Adana'daki trafik kazasına yarım saat içinde müdahale etti; yol bir süre trafiğe kapatıldı."),
    "terse_summary__352": ("Kütahya'da ana su hattında meydana gelen arıza sonucu bölgede kısa süreli su kesintisi yaşandı. Olay yerine sevk edilen belediye ekipleri, birkaç saat içinde müdahale etti.", "Belediye ekipleri, Kütahya'daki ana su hattı arızasına birkaç saat içinde müdahale etti; bölgede kısa süreli su kesintisi yaşandı."),
    "terse_summary__394": ("Balıkesir'de ana su hattında meydana gelen arıza sonucu bölgede kısa süreli su kesintisi yaşandı. Olay yerine sevk edilen belediye ekipleri, iki saat içinde müdahale etti.", "Belediye ekipleri, Balıkesir'deki ana su hattı arızasına iki saat içinde müdahale etti; bölgede kısa süreli su kesintisi yaşandı."),
    "terse_summary__424": ("Sivas'ta elektrik şebekesinde meydana gelen arıza nedeniyle elektrik birkaç saat kesildi. Olay yerine sevk edilen acil durum ekipleri, yarım saat içinde müdahale etti.", "Acil durum ekipleri, Sivas'taki elektrik şebekesi arızasına yarım saat içinde müdahale etti; elektrik birkaç saat kesildi."),
    "terse_summary__477": ("Denizli'de meydana gelen trafik kazası sonucu yol bir süre trafiğe kapatıldı. Olay yerine sevk edilen acil durum ekipleri, birkaç saat içinde müdahale etti.", "Acil durum ekipleri, Denizli'deki trafik kazasına birkaç saat içinde müdahale etti; yol bir süre trafiğe kapatıldı."),
}
BOILERPLATE = {
    "open_ended_counterexample__086": "Bu tür iş ve iletişim konularında, bu durumu sadece irade sorunu olarak görmek eksik olur; ortam, belirsizlik ve tekrarlayan kararlar da etkili olur. ",
    "open_ended_counterexample__198": "Verimlilik konularında genelde şu geçerlidir: bu durumu sadece irade sorunu olarak görmek eksik olur; ortam, belirsizlik ve tekrarlayan kararlar da etkili olur. ",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_prompt(prompt: str) -> tuple[str, str, str]:
    prefix, body_and_suffix = prompt.split("Metin: ", 1)
    body, suffix = body_and_suffix.rsplit("\n\nÖzet:", 1)
    return prefix, body, suffix


def main() -> None:
    with INPUT.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None
    repaired_story_ids, capitalized_ids, boilerplate_ids = [], [], []
    for row in rows:
        messages = json.loads(row["messages"])
        user, assistant = messages
        if row["id"] in STORY_REPAIRS:
            prefix, _body, suffix = split_prompt(user["content"])
            replacement_body, replacement_target = STORY_REPAIRS[row["id"]]
            user["content"] = f"{prefix}Metin: {replacement_body}\n\nÖzet:{suffix}"
            assistant["content"] = replacement_target
            repaired_story_ids.append(row["id"])
        if row["category"] == "terse_summary" and assistant["content"] and assistant["content"][0].islower():
            assistant["content"] = assistant["content"][0].upper() + assistant["content"][1:]
            capitalized_ids.append(row["id"])
        if row["id"] in BOILERPLATE:
            phrase = BOILERPLATE[row["id"]]
            if phrase not in assistant["content"]:
                raise ValueError(f"Expected boilerplate absent from {row['id']}")
            assistant["content"] = assistant["content"].replace(phrase, "")
            boilerplate_ids.append(row["id"])
        row["messages"] = json.dumps(messages, ensure_ascii=False)
        row["notes"] = (row.get("notes", "") + " | known-pattern repair v1").strip(" |") if row["id"] in set(repaired_story_ids) | set(capitalized_ids) | set(boilerplate_ids) else row.get("notes", "")
    # Seven of the initially lowercase summaries are replaced wholesale by
    # story repairs above, leaving 52 capitalization-only repairs.
    if len(repaired_story_ids) != 7 or len(capitalized_ids) != 52 or len(boilerplate_ids) != 2:
        raise ValueError("Known-repair inventory mismatch")
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "input": INPUT.name, "input_sha256": sha256(INPUT), "output": OUTPUT.name,
        "output_sha256": sha256(OUTPUT), "row_count": len(rows),
        "story_repaired_ids": repaired_story_ids, "capitalized_terse_target_ids": capitalized_ids,
        "removed_open_ended_boilerplate_ids": boilerplate_ids,
        "quality_status": "needs_review for every row",
    }
    (OUTPUT.with_suffix(".manifest.json")).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
