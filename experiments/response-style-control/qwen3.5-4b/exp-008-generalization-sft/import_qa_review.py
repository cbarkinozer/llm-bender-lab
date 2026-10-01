#!/usr/bin/env python3
"""Offer corrections in a separate queue without changing original reviews."""
import json
import os
from pathlib import Path

import argilla as rg

PROPOSALS = {
    "gen-001": "Gündüz teslim alabilecek biri olduğu için iş yeri daha uygun görünüyor. Resepsiyonun kişisel kargo kabul ettiğini teyit et.",
    "gen-003": "Bitkilerin dona dayanıklı olduğundan emin değilsen bu gece içeri alman daha güvenli olur.",
    "gen-007": "Sorun yalnızca fermuarsa 200 liraya tamir ettirmek daha ekonomik; yeni mont 1600 lira daha pahalı.",
    "gen-013": "Kutuda dört saat yazdığı için bir saat sonra kapatmak erken olabilir. Boyanın kullanım talimatındaki kuruma ve yeniden kullanım sürelerine uy.",
    "gen-033": "Bu bilgiyle nedenin banka olduğunu söyleyemeyiz. Başka bir tarayıcıda deneyebilir, sorun sürerse sitenin destek ekibine sorabilirsin.",
    "gen-044": "Yer ayırtmış olman tek başına biletin kesildiğini göstermez. Bilet onayını ve rezervasyonun ödeme koşullarını kontrol et.",
    "gen-058": "Başvurunun kabul edilmesi tek başına kaydının tamamlandığını göstermiyor. Kayıt durumunu ve gereken başka bir adım olup olmadığını kurumdan teyit et.",
    "gen-062": "Hangi hatayı kastettiğini bu mesajdan anlayamıyorum. Yanlış olan kısmı gösterirsen kontrol edip düzeltebilirim.",
    "gen-067": "Tebrik ederim! Bitirdiğin işi paylaşabilirsin; ne üzerinde çalışıyordun?",
    "gen-095": "Zeynep karşı çıktı; diğer katılımcıların görüşleri henüz doğrulanmadı.",
    "gen-097": "Hayır. Hata bulunmadığının söylenmemesi, hata bulunduğunu göstermez; bunun için raporun neyi açıkça belirttiğine bakmak gerekir.",
}


def main():
    root = Path(__file__).resolve().parent
    reviewed = {row["id"]: row for row in (json.loads(line) for line in (root / "data" / "generalization-reviewed-100.jsonl").read_text(encoding="utf-8").splitlines())}
    client = rg.Argilla(api_url=os.getenv("ARGILLA_API_URL", "http://127.0.0.1:6900"), api_key=os.getenv("ARGILLA_API_KEY", "argilla.apikey"))
    dataset = client.datasets(name="exp-008-post-review-qa", workspace="sft-review")
    if dataset is None:
        configuration = rg.Settings(
            guidelines="Review the proposed correction against the user prompt and QA reason. Accept the correction, rewrite it in full, or reject the example. Original human reviews remain preserved separately.",
            fields=[rg.TextField(name=field, use_markdown=False) for field in (
                "prompt_tr", "proposed_response", "boundary", "register", "previous_reviewed_response", "qa_reason")],
            questions=[rg.LabelQuestion(name="decision", labels=["accept", "rewrite", "reject"], required=True),
                       rg.TextQuestion(name="rewritten_response", required=False),
                       rg.TextQuestion(name="review_notes", required=False)])
        report = json.loads((root / "evaluation" / "reviewed-quality-report.json").read_text(encoding="utf-8"))
        issues = {row["id"]: row["issue"] for row in report["semantic_findings"]}
        dataset = rg.Dataset(name="exp-008-post-review-qa", workspace="sft-review", settings=configuration, client=client).create()
        dataset.records.log([rg.Record(id=record_id, fields={
            "prompt_tr": reviewed[record_id]["prompt_tr"], "proposed_response": reply,
            "boundary": reviewed[record_id]["boundary"], "register": reviewed[record_id]["register"],
            "previous_reviewed_response": reviewed[record_id]["reviewed_response"], "qa_reason": issues[record_id]})
            for record_id, reply in PROPOSALS.items()])
    print(json.dumps({"name": dataset.name, "records": len(list(dataset.records)), "url": f"http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode"}, indent=2))


if __name__ == "__main__":
    main()
