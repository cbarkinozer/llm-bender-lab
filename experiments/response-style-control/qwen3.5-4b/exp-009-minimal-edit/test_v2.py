import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from build_v2 import DATA, HERE, save
from generate_base import classify_finish, validate_inputs


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(line) for line in (DATA / "prompts-100.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_exact_split_and_no_shared_groups_or_sources(self):
        self.assertEqual(Counter(r["split"] for r in self.rows), {"train": 80, "validation": 20})
        train = [r for r in self.rows if r["split"] == "train"]
        val = [r for r in self.rows if r["split"] == "validation"]
        self.assertFalse({r["scenario_group_id"] for r in train} & {r["scenario_group_id"] for r in val})
        self.assertFalse({(r["source_path"], r["source_id"]) for r in train} & {(r["source_path"], r["source_id"]) for r in val})

    def test_all_requirements_mapped_in_both_splits(self):
        coverage = json.loads((DATA / "coverage-map.json").read_text(encoding="utf-8"))
        self.assertEqual(len(coverage), 10)
        for requirement in coverage.values():
            self.assertTrue(requirement["train_ids"])
            self.assertTrue(requirement["validation_ids"])

    def test_near_words_are_not_replaced_by_character_only_coverage(self):
        by_id = {r["id"]: r for r in self.rows}
        for rid, words in [("me-071", ["doktor", "doktora"]), ("me-075", ["tasarı", "tasarım"]),
                           ("me-076", ["deneyim", "denetim"]), ("me-078", ["artırımı", "aktarımı"]),
                           ("me-079", ["Vergi", "veri"]), ("me-073", ["kır", "kir"]),
                           ("me-074", ["kar", "kâr"]), ("me-080", ["Hala", "hâlâ"])]:
            for word in words:
                self.assertIn(word, by_id[rid]["prompt_tr"])

    def test_clarification_resolution_and_context_only_assistant(self):
        multi = [r for r in self.rows if r["is_multi_turn"]]
        self.assertEqual(Counter(r["split"] for r in multi), {"train": 2, "validation": 1})
        for row in multi:
            self.assertEqual([m["role"] for m in row["messages"]], ["user", "assistant", "user"])
            self.assertEqual(row["expected_mode"], "answer")
            self.assertIn("final reviewed response", row["context_assistant_supervision"])

    def test_csv_retains_actual_messages(self):
        with (DATA / "prompts-100.csv").open(encoding="utf-8", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        self.assertEqual(len(csv_rows), 100)
        for csv_row, json_row in zip(csv_rows, self.rows):
            self.assertEqual(csv_row["prompt_tr"], json_row["prompt_tr"])
            self.assertEqual(json.loads(csv_row["messages"]), json_row["messages"])

    def test_generation_inputs_validate_without_gpu(self):
        config, _, rows = validate_inputs(HERE / "generation-config.json")
        self.assertEqual(len(rows), 100)
        self.assertEqual(config["generation"]["output_token_budgets"], [4096, 8192, 16384])
        self.assertIsNone(config["model"]["adapter"])

    def test_stop_reasons_do_not_disguise_truncation(self):
        eos = [99, 100]
        self.assertEqual(classify_finish([1, 99], 4096, eos), "native_eos")
        self.assertEqual(classify_finish([1, 100], 2, eos), "native_eos")
        self.assertEqual(classify_finish([1, 2], 2, eos), "length_limit")
        self.assertEqual(classify_finish([1, 2], 4096, eos), "unexpected_stop")
        self.assertEqual(classify_finish([], 4096, eos), "empty")

    def test_forced_eos_configuration_is_rejected(self):
        config = json.loads((HERE / "generation-config.json").read_text(encoding="utf-8"))
        config["dataset_path"] = str(DATA / "prompts-100.jsonl")
        config["generation"]["forced_eos_token_id"] = 99
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_inputs(path)

    def test_v2_freeze_blocks_draft_override(self):
        path = DATA / "prompts-100.csv"
        before = path.read_bytes()
        with patch.object(sys, "argv", ["test", "--refresh-v2"]):
            with self.assertRaises(RuntimeError):
                save(path, b"not a valid replacement")
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
