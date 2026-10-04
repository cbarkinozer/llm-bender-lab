"""CPU-only release schema, content preservation and fail-closed checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from build_release import EXPERIMENT, HERE, clean, rows, sha


class ReleaseTests(unittest.TestCase):
    def test_frozen_counts_hashes_and_messages(self):
        config = json.loads((EXPERIMENT / 'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
        for split, count in [('train', 104), ('validation', 20)]:
            path = EXPERIMENT / f'data-reviewed-v1/{split}-reviewed.jsonl'
            self.assertEqual(sha(path), config['dataset']['hashes'][path.name])
            original = rows(path)
            self.assertEqual(len(original), count)
            for row in original:
                result = clean(row, split == 'validation')
                self.assertEqual(result['messages'][:-1], row['messages'])
                self.assertEqual(result['messages'][-1], {'role': 'assistant', 'content': row['desired_answer']})
                self.assertEqual(set(result), {'id', 'category', 'subtype', 'scenario_group_id',
                    'origin', 'source_id', 'evaluation_only', 'messages'})

    def test_rejects_bad_target(self):
        with self.assertRaises(ValueError):
            clean({'id': 'bad', 'messages': [{'role': 'user', 'content': 'hello'}], 'desired_answer': ''}, False)

    def test_no_source_mutation(self):
        original = {'id': 'test', 'messages': [{'role': 'user', 'content': 'Merhaba'}], 'desired_answer': 'Merhaba.'}
        before = json.dumps(original, ensure_ascii=False)
        clean(original, False)
        self.assertEqual(json.dumps(original, ensure_ascii=False), before)

    def reject(self, extra, expected):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'new-release'
            process = subprocess.run([sys.executable, str(HERE / 'build_release.py'),
                '--adapter-dir', str(Path(folder) / 'no-adapter'), '--output-dir', str(output), *extra],
                capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(expected, process.stderr)
            self.assertFalse(output.exists())

    def test_license_requires_attestation(self):
        self.reject(['--model-license', 'apache-2.0'], 'explicit owner rights-review attestation')

    def test_attestation_requires_real_ids_and_licenses(self):
        self.reject(['--rights-reviewed'], 'real IDs and both license selections')


if __name__ == '__main__':
    unittest.main()
