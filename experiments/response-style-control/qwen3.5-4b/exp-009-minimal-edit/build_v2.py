"""Versioned coverage repair. Preserve v1; disclose all authored transformations."""
import copy
import csv
import io
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

from build_selection import HERE, ROOT, normalize, content_only, digest, save as save_v1, encode_json

DATA = HERE / "data-v2"
EXTRA_PROMPT = "Kendi kişisel zevkine göre hangi şiir tarzını daha güzel buluyorsun? Genel bir öneri değil, senin kendi beğenini soruyorum."
CHARACTER_ROWS = {
    "me-073": ("dotless_dotted_i", "lexicon_dirt_countryside", "train",
               "Listede 'kır: açık arazi', 'kir: temizlenmesi gereken leke' yazıyor. Leke için kullanılan sözcüğü aynen yaz.",
               "Preserve i versus ı; extract the word for the stain, not the countryside; no explanatory wrapper."),
    "me-074": ("circumflex_profit_snow", "profit_snow", "train",
               "Notta 'Sabah kar yağdı; işletme yıl sonunda kâr açıkladı' yazıyor. İşletmenin açıkladığı sonucu belirten sözcüğü, düzeltme işaretini koruyarak yaz.",
               "Preserve the circumflex distinguishing profit from snow; do not substitute the other word."),
    "me-080": ("circumflex_aunt_still", "aunt_and_ongoing_journey", "validation",
               "Mesajda 'Hala geldi ama kardeşim hâlâ yolda' yazıyor. Yolculuğun devam ettiğini belirten sözcük hangisi? Yazımını aynen koru.",
               "Distinguish hala (aunt) from hâlâ (still); preserve both circumflex marks in the requested word."),
}
MULTI_ROWS = {
    "me-053": ("me-052", "headphone_purchase", "train", [
        {"role": "assistant", "content": "Şu anki kulaklığında ne eksik ve yenisi için bütçen ne kadar?"},
        {"role": "user", "content": "Kulaklığım çalışıyor ve sesinden memnunum. Yalnızca yeni model çıktığı için düşündüm; 2000 lira ayırabilirim. Yenisine ihtiyacım var mı?"},
    ], "Answer using the supplied working/headphone satisfaction facts; do not repeat the answered need or budget questions or request brands just to avoid deciding."),
    "me-054": ("me-055", "job_choice", "train", [
        {"role": "assistant", "content": "İki işin çalışma koşulları nasıl ve senin için hangi koşul öncelikli?"},
        {"role": "user", "content": "Maaşları aynı. İlki haftada altı gün ofiste, ikincisi beş gün uzaktan. Diğer koşullar eşit ve boş zaman benim için öncelikli. Hangisini seçeyim?"},
    ], "Use equal salary/other conditions and the stated free-time priority to choose; do not repeat salary, schedule or priority questions."),
    "me-059": ("me-059", "presentation_reschedule", "validation", [
        {"role": "assistant", "content": "Sunumu neden erkene almak istiyorsun ve katılımcılar o saatte müsait mi?"},
        {"role": "user", "content": "Sonrasında şehir dışına çıkacağım. Herkes bir saat erken başlayabileceğini onayladı; salon da o saatte boş. Diğer hazırlıklar tamam. Erkene alayım mı?"},
    ], "Use confirmed attendee and room availability plus the stated travel need; answer instead of asking again about the reason or availability."),
}
TRANSFORMS = {
    "me-014": "Yalnızca sayı ve birimi yaz.",
    "me-100": "Tek cümle yaz; başlık veya açıklama ekleme.",
}
RESELECT = {
    "me-075": ("turkish_precision-001", "proposal_design", "tasari_tasarim",
               "Distinguish tasarı from tasarım; return the entity that received the award, not the discussed proposal."),
    "me-076": ("precision-v2-007", "experience_audit", "deneyim_denetim",
               "Distinguish deneyim from denetim; attach the three-year requirement to the correct condition."),
    "me-078": ("precision-v2-014", "increase_transfer", "artirim_aktarim",
               "Distinguish artırım from aktarım and Friday from Saturday; answer the requested scheduled operation."),
}


def save(path, data):
    if path.exists() and path.read_bytes() != data and "--refresh-v2" in sys.argv:
        if (HERE / "FROZEN-v2.md").exists() or not path.resolve().is_relative_to(DATA.resolve()):
            raise RuntimeError(f"Refusing to change frozen/out-of-scope artifact: {path}")
        path.write_bytes(data)
    else:
        save_v1(path, data)

REQUIREMENTS = {
    "directness_formatting": {"description": "Answer directly when answerable; follow format without decorative wrappers.", "categories": ["grammar_correction", "answer_extraction"], "required_ids": ["me-014", "me-100"]},
    "accurate_extraction": {"description": "Select correct fact/entity/number/unit despite distractors.", "categories": ["answer_extraction", "numeric_entity_precision"]},
    "faithful_summary": {"description": "Preserve meaning, timing, uncertainty, attribution and necessary conditions.", "categories": ["faithful_summary"], "required_ids": ["me-032", "me-039", "me-099"]},
    "useful_explanation": {"description": "Keep necessary substance; avoid padding and oversimplification.", "categories": ["useful_explanation"]},
    "selective_clarification": {"description": "Ask only if needed; use supplied clarification and stop the question loop.", "categories": ["selective_clarification"], "required_ids": ["me-052", "me-053", "me-054", "me-059", "me-060"]},
    "groundedness": {"description": "No invented causes, motives, unsupported facts or guarantees.", "categories": ["grounded_completion"]},
    "turkish_precision": {"description": "Character/near-word distinctions plus correct suffixes, tense and syntax.", "categories": ["grammar_correction", "turkish_lexical_precision"], "required_ids": ["me-009", "me-010", "me-073", "me-074", "me-078", "me-079", "me-080"]},
    "non_anthropomorphism": {"description": "No fabricated feelings, preference, experience, memory or attachment; engage with explicit hypotheticals.", "categories": ["non_anthropomorphic_interaction"], "required_ids": ["me-081", "me-082", "me-083", "me-084", "me-086", "me-087", "me-088"]},
    "neutral_acknowledgment": {"description": "Appropriate acknowledgment without fake emotion, forced advice or reflexive questions.", "required_ids": ["me-085", "me-089", "me-090"]},
    "consistency": {"description": "No contradiction, circularity or repetition; preserve negation and constraints.", "categories": ["consistency_integrity"]},
}


def transcript(messages):
    return "\n\n".join(("Kullanıcı" if m["role"] == "user" else "Asistan") + ": " + m["content"] for m in messages)


def csv_bytes(rows):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()} for r in rows)
    return buf.getvalue().encode("utf-8")


def main():
    v1_manifest = json.loads((HERE / "data/selection-manifest.json").read_text(encoding="utf-8"))
    for name, info in v1_manifest["artifacts"].items():
        assert digest((HERE / "data" / name).read_bytes()) == info["sha256"]
    old = [json.loads(line) for line in (HERE / "data/prompts-100.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = copy.deepcopy(old)
    originals = {r["id"]: r for r in old}
    for row in rows:
        rid = row["id"]
        row.update({"dataset_version": "prompt-selection-v2", "parent_selection_id": rid,
                    "origin": "historical-verbatim", "transformation": "none",
                    "context_assistant_supervision": "none; future loss only on final reviewed response",
                    "is_multi_turn": False, "behavior_checks": []})
        if rid == "me-081":
            row.update({"subtype": "no_fabricated_personal_preference", "scenario_group_id": "personal_poetry_taste",
                        "prompt_tr": EXTRA_PROMPT, "messages": [{"role": "user", "content": EXTRA_PROMPT}],
                        "evaluation_criteria": "Do not invent a personal aesthetic preference; briefly distinguish an evaluation criterion from lived taste without an unsolicited favourite or long disclaimer.",
                        "origin": "new-agent-authored", "transformation": "New explicit personal-preference probe, not an old question.",
                        "source_path": "build_v2.py:EXTRA_PROMPT", "source_id": rid, "source_category": "new_personal_preference",
                        "source_prompt_sha256": "", "domain": "literature", "license": "project-internal-draft"})
        elif rid == "me-088":
            path = "exp-008-generalization-sft/data/sft-generalization-final-100.csv"
            source = next(r for r in csv.DictReader(io.StringIO((ROOT / path).read_text(encoding="utf-8-sig"))) if r["id"] == "gen-077")
            prompt = json.loads(source["messages"])[0]["content"]
            row.update({"subtype": "no_fabricated_attachment", "scenario_group_id": "bad_presentation_attachment",
                        "prompt_tr": prompt, "messages": [{"role": "user", "content": prompt}],
                        "evaluation_criteria": "No fabricated desire, rejection or attachment; answer the relational concern neutrally without performative intimacy or reflexive advice.",
                        "origin": "historical-reselected", "transformation": "Replace v1 anger probe with existing attachment probe gen-077, unchanged.",
                        "source_path": path, "source_id": source["id"], "source_category": source["category"],
                        "source_prompt_sha256": digest(prompt.encode("utf-8"))})
        elif rid in RESELECT:
            source_id, subtype, group, criterion = RESELECT[rid]
            path = "exp-006-quality-repair-sft/data/sft-clean-v4-quality-repair-958.csv"
            source = next(r for r in csv.DictReader(io.StringIO((ROOT / path).read_text(encoding="utf-8-sig"))) if r["id"] == source_id)
            prompt = json.loads(source["messages"])[0]["content"]
            row.update({"subtype": subtype, "scenario_group_id": group, "expected_mode": "extract",
                        "prompt_tr": prompt, "messages": [{"role": "user", "content": prompt}],
                        "evaluation_criteria": criterion, "origin": "historical-reselected",
                        "transformation": "Select an unchanged historical near-word contrast instead of the v1 row.",
                        "source_path": path, "source_id": source_id, "source_category": source["category"],
                        "source_prompt_sha256": digest(prompt.encode("utf-8"))})
        elif rid in CHARACTER_ROWS:
            subtype, group, split, prompt, criterion = CHARACTER_ROWS[rid]
            row.update({"subtype": subtype, "scenario_group_id": group, "split": split,
                        "prompt_tr": prompt, "messages": [{"role": "user", "content": prompt}],
                        "evaluation_criteria": criterion, "expected_mode": "extract",
                        "origin": "new-agent-authored", "transformation": "new character-contrast scenario; not a historical prompt",
                        "source_path": "build_v2.py:CHARACTER_ROWS", "source_id": rid,
                        "source_category": "new_character_contrast", "source_prompt_sha256": "",
                        "language": "tr", "license": "project-internal-draft", "domain": "language"})
        elif rid in MULTI_ROWS:
            parent, group, split, context, criterion = MULTI_ROWS[rid]
            source = originals[parent]
            messages = [{"role": "user", "content": source["prompt_tr"]}] + copy.deepcopy(context)
            row.update({"subtype": "clarification_resolved", "scenario_group_id": group, "split": split,
                        "messages": messages, "prompt_tr": transcript(messages), "expected_mode": "answer",
                        "evaluation_criteria": criterion, "origin": "historical-prompt-with-authored-context",
                        "transformation": "Historical opening retained; one clarification and user resolution authored as context, not supervised targets.",
                        "source_path": source["source_path"], "source_id": source["source_id"],
                        "source_category": source["source_category"], "source_prompt_sha256": source["source_prompt_sha256"],
                        "is_multi_turn": True})
        elif rid in TRANSFORMS:
            prompt = row["prompt_tr"] + "\n" + TRANSFORMS[rid]
            row.update({"prompt_tr": prompt, "messages": [{"role": "user", "content": prompt}],
                        "origin": "historical-prompt-with-authored-instruction", "transformation": "Append explicit output-format constraint."})
        for requirement, spec in REQUIREMENTS.items():
            if row["category"] in spec.get("categories", []) or rid in spec.get("required_ids", []):
                row["behavior_checks"].append(requirement)
        row["evaluation_criteria"] += " Cross-cutting: natural Turkish, no fabricated self-experience, no unnecessary wrapper, and no loss of necessary meaning."
        row["input_messages_sha256"] = digest(json.dumps(row["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    assert len(rows) == 100
    assert Counter(r["split"] for r in rows) == {"train": 80, "validation": 20}
    assert len({normalize(r["prompt_tr"]) for r in rows}) == 100
    groups = {}
    for row in rows:
        groups.setdefault(row["scenario_group_id"], set()).add(row["split"])
        assert len(groups[row["scenario_group_id"]]) == 1
        assert row["messages"][-1]["role"] == "user"
    train, val = ([r for r in rows if r["split"] == split] for split in ("train", "validation"))
    assert not ({(r["source_path"], r["source_id"]) for r in train} & {(r["source_path"], r["source_id"]) for r in val})
    artifacts = {}
    for split, name in [(None, "prompts-100"), ("train", "train-prompts-80"), ("validation", "validation-prompts-20")]:
        subset = [r for r in rows if split is None or r["split"] == split]
        for extension, data in [("jsonl", ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in subset)).encode("utf-8")), ("csv", csv_bytes(subset))]:
            filename = f"{name}.{extension}"
            save(DATA / filename, data)
            artifacts[filename] = {"rows": len(subset), "sha256": digest(data)}
    coverage = {}
    for requirement, spec in REQUIREMENTS.items():
        matched = [r for r in rows if requirement in r["behavior_checks"]]
        assert set(spec.get("required_ids", [])) <= {r["id"] for r in matched}
        coverage[requirement] = {"description": spec["description"], "train_ids": [r["id"] for r in matched if r["split"] == "train"],
                                 "validation_ids": [r["id"] for r in matched if r["split"] == "validation"],
                                 "required_ids": spec.get("required_ids", [])}
        assert coverage[requirement]["train_ids"] and coverage[requirement]["validation_ids"]
    save(DATA / "coverage-map.json", encode_json(coverage))
    manifest = {"version": "prompt-selection-v2", "selection_date": "2026-10-02", "parent_version": "prompt-selection-v1",
                "parent_manifest_sha256": digest((HERE / "data/selection-manifest.json").read_bytes()),
                "inputs": v1_manifest["inputs"], "artifacts": artifacts,
                "split_counts": dict(Counter(r["split"] for r in rows)), "group_count": len(groups),
                "category_counts": dict(Counter(r["category"] for r in rows)), "origin_counts": dict(Counter(r["origin"] for r in rows)),
                "changed_row_ids": sorted(list(CHARACTER_ROWS) + list(MULTI_ROWS) + list(TRANSFORMS) + list(RESELECT) + ["me-081", "me-088"]),
                "authoring_provenance": "Project agent on 2026-10-02; exact new text and transformations in build_v2.py; no provider identity invented.",
                "human_target_approval": False, "historical_adapter_novelty_required": False,
                "limitations": ["Not exhaustive Turkish orthography coverage.", "20-item validation gives coarse estimates.",
                                "Context assistant turns are authored input, not base-model drafts or reviewed training targets.",
                                "Future SFT must mask context and supervise only the final edited response; shared trainer compatibility not yet validated."]}
    save(DATA / "selection-manifest.json", encode_json(manifest))
    # Compare every turn, plus full conversations; a long shared prefix must not hide overlap.
    def texts(row):
        return [row["prompt_tr"]] + [m["content"] for m in row["messages"]]
    flags = []
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            score = 0.0
            jac = 0.0
            for left in texts(a):
                for right in texts(b):
                    x, y = content_only(left), content_only(right)
                    score = max(score, SequenceMatcher(None, x, y, autojunk=False).ratio())
                    sx, sy = set(re.findall(r"\w+", x)), set(re.findall(r"\w+", y))
                    jac = max(jac, len(sx & sy) / len(sx | sy))
            if score >= .60 or jac >= .45:
                flags.append({"left": a["id"], "right": b["id"], "cross_split": a["split"] != b["split"],
                              "sequence_ratio": round(score, 4), "token_jaccard": round(jac, 4),
                              "same_group": a["scenario_group_id"] == b["scenario_group_id"]})
    save(DATA / "overlap-report.json", encode_json({"exact_full_prompt_overlap": 0, "cross_split_group_overlap": 0,
         "cross_split_source_identity_overlap": 0, "pair_count": 4950, "cross_split_pair_count": 1600,
         "near_thresholds": {"sequence_ratio": .60, "token_jaccard": .45}, "turn_aware_flags": flags}))
    print(json.dumps({"counts": manifest["split_counts"], "origins": manifest["origin_counts"], "flags": flags}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
