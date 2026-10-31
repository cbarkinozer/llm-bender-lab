"""Check evidence semantics: collection/runtime faults cannot masquerade as assertion kills."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('external_task_batch', SCRIPTS / 'external_task_batch.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


class EvidenceTests(unittest.TestCase):
    def run_fixture(self, text):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'batch_probe.py').write_text(batch.PLUGIN, encoding='utf-8')
            (root/'test_sample.py').write_text(text, encoding='utf-8')
            (root/'condition.json').write_text(json.dumps(dict(mutation=None, seed=17)), encoding='utf-8')
            result = subprocess.run([sys.executable,'-m','pytest','-q','-p','batch_probe','test_sample.py'],
                                    cwd=root, env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=folder),
                                    capture_output=True, timeout=20)
            execution=json.loads((root/'execution.json').read_text())
            return result.returncode, execution

    def test_assertion_and_missing_expected_exception_are_explicit_failures(self):
        for text in ('def test_bad():\n    assert 1 == 2\n',
                     'import pytest\ndef test_bad():\n    with pytest.raises(ValueError):\n        pass\n'):
            with self.subTest(text=text):
                code,data=self.run_fixture(text)
                self.assertEqual(code,1)
                self.assertTrue(any(r['assertion'] for r in data['reports']))

    def test_collection_failure_has_no_call_assertion(self):
        code,data=self.run_fixture('import nonexistent_batch_test_dependency\n')
        self.assertEqual(code,2)
        self.assertFalse(any(r['assertion'] for r in data['reports']))

    def test_runtime_type_error_is_not_counted_as_assertion(self):
        code,data=self.run_fixture('def test_bad():\n    return 1 + None\n')
        self.assertEqual(code,1)
        self.assertFalse(any(r['assertion'] for r in data['reports']))


if __name__=='__main__':
    unittest.main()
