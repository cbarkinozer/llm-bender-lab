"""CPU-only frozen-input, selection and adapter identity regression checks."""
import collections
import hashlib
import json
import random
import unittest

from prepare import HERE, SOURCE, COUNTS, digest, load


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.rows = load(HERE / 'data-v1/questions-100.jsonl')

    def test_count_and_frozen_hash(self):
        m = json.loads((HERE / 'data-v1/manifest.json').read_text())
        self.assertEqual(len(self.rows), 100)
        self.assertEqual(len({r['id'] for r in self.rows}), 100)
        self.assertEqual(digest(HERE / 'data-v1/questions-100.jsonl'), m['questions_sha256'])
        self.assertEqual(collections.Counter(r['task'] for r in self.rows), dict.fromkeys(COUNTS, 20))

    def test_selection_ignores_old_outputs(self):
        for task, size in COUNTS.items():
            old = load(SOURCE / task / 'samples.jsonl')
            chosen = sorted(random.Random('cetvel-tiny-v1-3407-' + task).sample(range(size), 20))
            new = [r for r in self.rows if r['task'] == task]
            for row, index in zip(new, chosen):
                source = old[index]
                self.assertEqual(row['document'], source['document'])
                self.assertEqual(row['semantic_prompt'], source['semantic_prompt'])
                self.assertEqual(row['target'], source['target'])
                self.assertNotIn('raw_output', row)
                self.assertNotIn('generated_tokens', row)
                self.assertTrue(row['evaluation_only'])
                self.assertEqual(row['messages'], [{'role': 'user', 'content': row['semantic_prompt']}])

    def test_human_subset_and_leakage(self):
        ids = json.loads((HERE / 'data-v1/human-review-20-ids.json').read_text())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 20)
        subset = [r for r in self.rows if r['id'] in ids]
        self.assertEqual(collections.Counter(r['task'] for r in subset), dict.fromkeys(COUNTS, 4))
        audit = json.loads((HERE / 'data-v1/leakage-audit.json').read_text())
        self.assertEqual(audit['exact_overlaps'], [])
        self.assertEqual(audit['near_duplicate_candidates'], [])

    def test_adapter_is_recovered_f(self):
        config = json.loads((HERE / 'config.json').read_text())
        frozen = json.loads((HERE.parents[3] / 'experiments/response-style-control/qwen3.5-4b/'
                             'exp-015-target-quality-sft/gpu-results-v1/F-evaluation-v1/manifest.json').read_text())
        self.assertEqual(config['model'], frozen['model'])
        self.assertEqual(config['revision'], frozen['revision'])
        for name, expected in config['adapter_hashes'].items():
            self.assertEqual(expected, frozen['adapter_hashes'][name])


if __name__ == '__main__':
    unittest.main()
