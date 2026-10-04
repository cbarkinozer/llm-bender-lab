"""CPU-only cohort, source-disjointness, frozen recipe and statistics tests."""
import collections
import hashlib
import json
import random
import unittest

from prepare import HERE, OLD, PARENT, SPECS, canonical, group_text, load, norm, prompt_target, shingles, containment
from paired_analysis import paired


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load(HERE / 'data-v1/questions-500.jsonl')
        cls.manifest = read(HERE / 'data-v1/manifest.json')

    def test_counts_hashes_and_no_outputs(self):
        self.assertEqual(len(self.rows), len({r['id'] for r in self.rows}))
        self.assertEqual(collections.Counter(r['task'] for r in self.rows), dict.fromkeys(SPECS, 100))
        self.assertEqual(hashlib.sha256((HERE / 'data-v1/questions-500.jsonl').read_bytes()).hexdigest(), self.manifest['questions_sha256'])
        for row in self.rows:
            self.assertEqual(hashlib.sha256(canonical(row['document']).encode()).hexdigest(), row['document_sha256'])
            self.assertEqual(prompt_target(row['task'], row['document']), (row['semantic_prompt'], row['target']))
            self.assertTrue(row['evaluation_only'])
            self.assertNotIn('raw_output', row)

    def test_historical_sources_excluded(self):
        for task in SPECS:
            old = load(OLD / task / 'samples.jsonl')
            historical = {norm(group_text(task, r['document'])) for r in old}
            urls = {r['document'].get('url') for r in old} - {None, ''}
            selected = [r for r in self.rows if r['task'] == task]
            self.assertEqual(len({r['source_group_sha256'] for r in selected}), 100)
            for row in selected:
                self.assertGreaterEqual(row['index'], len(old))
                self.assertNotIn(norm(group_text(task, row['document'])), historical)
                self.assertNotIn(row['document'].get('url', ''), urls)
        self.assertTrue({r['id'] for r in self.rows}.isdisjoint(r['id'] for r in load(PARENT / 'data-v1/questions-100.jsonl')))

    def test_near_group_candidates_excluded(self):
        for task in SPECS:
            old = [shingles(group_text(task, r['document'])) for r in load(OLD / task / 'samples.jsonl')]
            seen = []
            for row in (r for r in self.rows if r['task'] == task):
                words = shingles(group_text(task, row['document']))
                self.assertTrue(all(containment(words, other) < .8 for other in old + seen))
                seen.append(words)

    def test_recipe_parity_and_profile(self):
        config = read(HERE / 'config.json')
        actual_parent = read(PARENT / 'results-v1/base/manifest.json')['config']
        for key in ('model', 'revision', 'adapter_hashes', 'precision', 'batch_size', 'thinking',
                'max_context_tokens', 'max_new_tokens', 'repetition_penalty', 'seed', 'backend',
                'model_eos_token_id', 'tokenizer_eos_token_id', 'enforce_eager', 'enable_prefix_caching'):
            self.assertEqual(config[key], actual_parent[key], key)
        profile = read(HERE / 'data-v1/tokenization-profile.json')
        self.assertEqual(len(profile['items']), 500)
        self.assertEqual(profile['input_truncated_count'], 0)
        self.assertLessEqual(profile['max_input_tokens'] + config['max_new_tokens'], config['max_context_tokens'])

    def test_frozen_human30_and_audit(self):
        ids = read(HERE / 'data-v1/human-review-30-ids.json')
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(collections.Counter(r['task'] for r in self.rows if r['id'] in ids), dict.fromkeys(SPECS, 6))
        for task in SPECS:
            expected = random.Random('fresh500-human-v1-3407-' + task).sample([r['id'] for r in self.rows if r['task'] == task], 6)
            self.assertEqual([item_id for item_id in ids if item_id.startswith(task + '-')], expected)
        audit = read(HERE / 'data-v1/leakage-audit.json')
        self.assertEqual(audit['train_rows'], 104)
        for task in audit['tasks'].values():
            self.assertEqual(task['training_candidates_in_selected'], 0)
            self.assertEqual(task['old_source_groups_in_selected'], 0)

    def test_paired_bootstrap(self):
        identical = paired([0] * 100, random.Random(3407), repeats=100)
        self.assertEqual(identical['bootstrap_percentile_95_interval'], [0, 0])
        self.assertEqual(identical['ties'], 100)
        win = paired([1] * 100, random.Random(3407), repeats=100)
        self.assertEqual(win['bootstrap_percentile_95_interval'], [1, 1])
        self.assertEqual(win['wins'], 100)


if __name__ == '__main__':
    unittest.main()
