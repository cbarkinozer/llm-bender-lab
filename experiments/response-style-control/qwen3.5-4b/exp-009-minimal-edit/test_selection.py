import csv
import json
import sys
import unittest
from collections import Counter
from unittest.mock import patch

from build_selection import HERE, normalize, save


class SelectionTests(unittest.TestCase):
    def test_turkish_distinctions_survive_normalization(self):
        for a, b in [("kar", "kâr"), ("i", "ı"), ("İ", "I"), ("vergi", "veri")]:
            self.assertNotEqual(normalize(a), normalize(b))
        self.assertEqual(normalize("  A  B "), "A B")

    def test_csv_and_jsonl_agree(self):
        for stem in ["prompts-100", "train-prompts-80", "validation-prompts-20"]:
            with (HERE / f"data/{stem}.csv").open(encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            json_rows = [json.loads(line) for line in (HERE / f"data/{stem}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(csv_rows, [{k: v for k, v in row.items() if k != "messages"} for row in json_rows])

    def test_no_assistant_targets(self):
        rows = [json.loads(line) for line in (HERE / "data/prompts-100.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(Counter(r["split"] for r in rows), {"train": 80, "validation": 20})
        for row in rows:
            self.assertEqual(row["messages"], [{"role": "user", "content": row["prompt_tr"]}])
            self.assertEqual(row["answer_status"], "not-generated")

    def test_frozen_write_refused_even_with_draft_flag(self):
        path = HERE / "data/prompts-100.csv"
        before = path.read_bytes()
        with patch.object(sys, "argv", ["test", "--refresh-draft"]):
            with self.assertRaises(RuntimeError):
                save(path, b"invalid replacement")
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
