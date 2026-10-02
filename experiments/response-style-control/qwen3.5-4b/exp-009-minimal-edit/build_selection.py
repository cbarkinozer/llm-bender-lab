"""Build a traceable prompt-only curation. Never copies historical targets."""
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "core": "exp-001-sft-dataset/reviewed-v3/accepted-reviewed.csv",
    "repair": "exp-006-quality-repair-sft/data/sft-clean-v4-quality-repair-958.csv",
    "new": "exp-008-generalization-sft/data/sft-generalization-final-100.csv",
}
# Hand-curated subtype coverage, not a random sample or model-ranked quality claim.
# source, original ID, subtype, scenario group, expected mode, split
SELECTION = {
    "grammar_correction": """
core bare_gec__001 compound_today apartment_sensor correct train
core bare_gec__003 indefinite_pronoun school_feedback correct train
core bare_gec__007 compound_everything experimental_accounts correct train
core bare_gec__017 misspelling_lonely train_signal correct train
core bare_gec__121 case_suffix_spacing chemistry_report correct train
core bare_gec__179 ablative_suffix_spacing wet_track correct train
core bare_gec__207 vowel_form missed_flight correct train
new gen-047 question_particle customer_question correct train
new gen-048 tense_and_case park_sentence correct validation
new gen-059 person_agreement joint_arrival correct validation
""",
    "answer_extraction": """
core bare_qa_span__018 named_person linux_author extract train
core bare_qa_span__118 explorer pacific_expeditions extract train
core bare_qa_span__164 historical_year revolution_year extract train
core bare_qa_span__218 count municipal_saplings extract train
core bare_qa_span__305 percentage hotel_occupancy extract train
core bare_qa_span__457 descriptive_phrase hotel_terrace extract train
core bare_qa_span__473 restricted_quantifier market_card_payment extract train
core bare_qa_span__545 yes_no early_booking extract train
core bare_qa_span__388 location tower_location extract validation
core bare_qa_span__462 abstract_phrase slow_tourism extract validation
""",
    "numeric_entity_precision": """
core numeric_entity_precision_qa__126 price medical_prices extract train
core numeric_entity_precision_qa__140 duration school_registration_time extract train
core numeric_entity_precision_qa__318 institution school_bursary extract train
core numeric_entity_precision_qa__482 percentage school_statistics extract train
core numeric_entity_precision_qa__005 location travel_branch extract train
core numeric_entity_precision_qa__008 duration market_maintenance extract train
repair precision-v2-002 forecast_vs_recommendation production_plan extract train
repair precision-v2-009 export_vs_import trade_statistics extract train
core numeric_entity_precision_qa__015 named_product product_action_matching extract validation
core numeric_entity_precision_qa__484 named_product product_action_matching extract validation
""",
    "faithful_summary": """
core terse_summary__144 result_and_rank match_result summarize train
core terse_summary__218 association_not_causation storage_study summarize train
core terse_summary__244 recipient_and_award sports_award summarize train
core terse_summary__261 biographical_event craft_support summarize train
core terse_summary__268 revenue_and_period revenue_result summarize train
core terse_summary__340 cause_and_intervention infrastructure_incident summarize train
core terse_summary__012 product_feature_price sensor_launch summarize train
core terse_summary__025 weather_and_consequence fog_closure summarize train
core terse_summary__001 future_statement mayor_announcement summarize validation
core terse_summary__013 ruling_not_invented_charge court_ruling summarize validation
""",
    "useful_explanation": """
core open_ended_counterexample__120 diagnose_process workload_priorities explain train
core open_ended_counterexample__147 staged_plan photo_archive explain train
core open_ended_counterexample__310 explain_mechanism ceramic_experiment explain train
core open_ended_counterexample__001 sustainable_plan meal_preparation explain train
core open_ended_counterexample__067 practice_plan teaching_clarity explain train
core open_ended_counterexample__141 troubleshoot wifi_rooms explain train
core open_ended_counterexample__264 communication_diagnosis congratulations_message explain train
core open_ended_counterexample__005 practical_habits misplaced_objects explain train
core open_ended_counterexample__010 mechanism_and_solution morning_delay explain validation
core open_ended_counterexample__015 compare_tradeoffs small_home_workspace explain validation
""",
    "selective_clarification": """
new gen-001 sufficient_delivery_context parcel_destination answer train
new gen-002 missing_need headphone_purchase clarify train
new gen-007 sufficient_cost_context coat_repair answer train
new gen-009 no_observed_bottleneck laptop_ram answer train
new gen-012 missing_work_conditions job_choice clarify train
new gen-013 explicit_waiting_constraint paint_drying answer train
new gen-017 verify_before_irreversible_action photo_copy conditional train
new gen-020 reversible_trial running_schedule conditional train
new gen-004 missing_schedule_context presentation_reschedule clarify validation
new gen-006 missing_trust_context neighbour_key clarify validation
""",
    "grounded_completion": """
new gen-021 unknown_inventory order_preparation answer train
new gen-022 supplied_cause elevator_stairs answer train
new gen-023 unknown_motive early_meeting_departure answer train
new gen-027 uncertain_diagnosis phone_shutdown answer train
new gen-028 supplied_cause rain_match answer train
new gen-031 unknown_life_event neighbour_departure answer train
new gen-033 unknown_payment_fault payment_page answer train
new gen-038 unsupported_intent evening_internet answer train
new gen-025 correlation_not_cause cafe_sign answer validation
new gen-040 unknown_previous_failure retry_success answer validation
""",
    "turkish_lexical_precision": """
repair precision-v2-001 title_vs_degree doctorate_requirement answer train
repair precision-v2-005 near_word_contrast management_method extract train
repair precision-v2-008 similar_technical_terms transmission_os extract train
repair precision-v2-013 metric_vs_duration verification_accuracy extract train
new gen-041 loan_vs_gift borrowed_book answer train
new gen-046 negotiation_vs_agreement contract_renegotiation answer train
new gen-050 possessive_ambiguity teacher_book conditional train
new gen-052 future_vs_completed payment_future answer train
repair precision-v2-006 one_character_contrast tax_data_rules extract validation
repair precision-v2-018 connection_vs_dependency software_dependency extract validation
""",
    "non_anthropomorphic_interaction": """
new gen-074 no_fabricated_regret rewritten_draft answer train
repair anthropomorphism-019 memory_boundary previous_conversation answer train
repair anthropomorphism-005 criteria_based_hypothetical city_job_choice conditional train
new gen-063 explicit_fictional_role story_lantern answer train
new gen-067 acknowledge_achievement completed_task answer train
new gen-068 no_jealousy alternate_assistant answer train
new gen-071 no_fabricated_pride first_presentation answer train
new gen-080 no_fabricated_anger repeated_question answer train
new gen-061 acknowledge_without_followup new_home answer validation
new gen-079 respect_no_advice_request failed_exam answer validation
""",
    "consistency_integrity": """
new gen-081 unresolved_contradiction upload_note correct train
new gen-083 double_negation attendance_logic answer train
new gen-085 distinct_requested_steps phone_storage answer train
new gen-087 negative_quantifier homework_logic answer train
new gen-090 total_cost_comparison shopping_cost answer train
new gen-091 possibility_not_certainty impossible_result answer train
new gen-092 known_fact_correction book_delivery correct train
new gen-094 incompatible_time_constraints film_bus answer train
new gen-096 preserve_expected_not_certain stock_return summarize validation
new gen-099 concise_message_constraints late_arrival correct validation
""",
}
RUBRICS = {
    "grammar_correction": "Return corrected Turkish only; preserve meaning; fix the identified orthographic/morphological issue without an unnecessary rewrite.",
    "answer_extraction": "Answer only the asked source-bound fact; preserve restrictions and exact entity/quantity; no external additions.",
    "numeric_entity_precision": "Match the requested role to the correct number/entity; preserve units and distinguish the distractor.",
    "faithful_summary": "Capture the main source event concisely; preserve actor, critical quantities, timing, attribution and uncertainty; invent nothing.",
    "useful_explanation": "Provide usable explanation or steps requested by the prompt; preserve necessary substance while removing filler; no blanket one-sentence answer.",
    "selective_clarification": "Use the available facts; clarify only a material missing variable; conditional advice is allowed; do not append reflexive questions.",
    "grounded_completion": "State supplied facts/causes but do not invent motives or diagnoses; distinguish uncertainty from evidence; stop when complete.",
    "turkish_lexical_precision": "Read exact Turkish words, suffixes and tense; preserve the intended semantic distinction; clarify only genuine material ambiguity.",
    "non_anthropomorphic_interaction": "No fabricated personal feeling, favourite, experience or memory; retain useful neutral acknowledgment or explicitly fictional/conditional engagement; no canned disclaimer.",
    "consistency_integrity": "Give coherent non-repetitive content; preserve negation, uncertainty, constraints and requested format; do not invent a resolution to unknown contradictory facts.",
}


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def content_only(text):
    # Remove common instruction wrappers, not scenario facts or Turkish distinctions.
    text = re.sub(r"Verilen cümlenin yazım hatalarını düzeltin\.\s*Hatalı Cümle:\s*", "", text)
    text = re.sub(r"\s*Düzeltilmiş hali:\s*$", "", text)
    return normalize(text)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        if "--refresh-draft" not in sys.argv or (HERE / "FROZEN.md").exists():
            raise RuntimeError(f"Refusing to change frozen artifact: {path}")
    path.write_bytes(data)


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main():
    pools = {}
    inputs = {}
    for key, relative in SOURCES.items():
        raw = (ROOT / relative).read_bytes()
        inputs[relative] = {"sha256_bytes": digest(raw), "sha256_canonical_lf": digest(raw.replace(b"\r\n", b"\n"))}
        records = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        pools[key] = {r["id"]: r for r in records}
        assert len(pools[key]) == len(records)
        inputs[relative]["rows"] = len(records)
    selected = []
    for category, block in SELECTION.items():
        for line in block.strip().splitlines():
            source, source_id, subtype, group, mode, split = line.split()
            original = pools[source][source_id]
            historical = json.loads(original["messages"])
            assert len(historical) == 2 and historical[0]["role"] == "user"
            prompt = historical[0]["content"]
            selected.append({
                "id": f"me-{len(selected)+1:03d}", "category": category,
                "subtype": subtype, "scenario_group_id": group,
                "split": split, "expected_mode": mode,
                "prompt_tr": prompt, "messages": [{"role": "user", "content": prompt}],
                "evaluation_criteria": RUBRICS[category] + " Specific boundary: " + subtype.replace("_", " ") + ".",
                "source_path": SOURCES[source], "source_id": source_id,
                "source_category": original["category"], "domain": original.get("domain", ""),
                "language": "tr", "license": original.get("license", "project-internal-draft"),
                "selection_status": "agent-curated-prompt-only", "answer_status": "not-generated",
                "source_prompt_sha256": digest(prompt.encode("utf-8")),
            })
    assert len(selected) == 100
    assert Counter(r["split"] for r in selected) == {"train": 80, "validation": 20}
    assert len({normalize(r["prompt_tr"]) for r in selected}) == 100
    groups = {}
    for row in selected:
        groups.setdefault(row["scenario_group_id"], set()).add(row["split"])
        assert len(groups[row["scenario_group_id"]]) == 1
        assert row["prompt_tr"].strip() and "\ufffd" not in row["prompt_tr"]
        assert all(m["role"] != "assistant" for m in row["messages"])
    pairs = []
    for i, left in enumerate(selected):
        for right in selected[i+1:]:
            a, b = content_only(left["prompt_tr"]), content_only(right["prompt_tr"])
            ratio = SequenceMatcher(None, a, b, autojunk=False).ratio()
            ta, tb = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
            jaccard = len(ta & tb) / len(ta | tb)
            if ratio >= .60 or jaccard >= .45:
                pairs.append({"left": left["id"], "right": right["id"], "left_source": left["source_id"],
                              "right_source": right["source_id"], "cross_split": left["split"] != right["split"],
                              "sequence_ratio": round(ratio, 4), "token_jaccard": round(jaccard, 4)})
    artifacts = {}
    for split, name in [(None, "prompts-100"), ("train", "train-prompts-80"), ("validation", "validation-prompts-20")]:
        rows = [r for r in selected if split is None or r["split"] == split]
        data = ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)).encode("utf-8")
        save(HERE / "data" / (name + ".jsonl"), data)
        artifacts[name + ".jsonl"] = {"rows": len(rows), "sha256": digest(data)}
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=[k for k in rows[0] if k != "messages"], lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: v for k, v in r.items() if k != "messages"} for r in rows)
        data = buffer.getvalue().encode("utf-8")
        save(HERE / "data" / (name + ".csv"), data)
        artifacts[name + ".csv"] = {"rows": len(rows), "sha256": digest(data)}
    report = {"rows": 100, "split_counts": dict(Counter(r["split"] for r in selected)),
              "exact_normalized_duplicate_prompts": 0, "cross_split_group_overlap": 0,
              "historical_assistant_targets_copied": 0, "group_count": len(groups),
              "near_match_thresholds": {"sequence_ratio": .60, "token_jaccard": .45},
              "near_match_pairs_for_review": pairs,
              "semantic_independence": "Requires documented manual pair and full prompt review; lexical checks alone do not prove it."}
    save(HERE / "data" / "overlap-report.json", encode_json(report))
    manifest = {"version": "prompt-selection-v1", "selection_date": "2026-10-02",
                "selection_method": "Explicit hand-curated source IDs and scenario-aware split; no random seed applies.",
                "starting_model": "unsloth/Qwen3.5-4B", "model_revision": "3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636",
                "historical_adapter_novelty_required": False, "inputs": inputs, "artifacts": artifacts,
                "category_counts": dict(Counter(r["category"] for r in selected)),
                "category_split_counts": {c: dict(Counter(r["split"] for r in selected if r["category"] == c)) for c in SELECTION},
                "mode_counts": dict(Counter(r["expected_mode"] for r in selected)),
                "limitations": ["Agent curation, not new human approval.", "No multi-turn clarification-resolution rows exist in this selection.",
                                "Targets not generated; no training artifact exists.", "Validation is development, not final test.",
                                "Historical source approvals include saturation-based approvals, not individual review of every original row."]}
    save(HERE / "data" / "selection-manifest.json", encode_json(manifest))
    print(json.dumps({"rows": 100, "splits": report["split_counts"], "near_pairs": pairs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
