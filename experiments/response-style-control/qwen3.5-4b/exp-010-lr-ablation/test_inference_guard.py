import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parent.parent/'exp-009-minimal-edit/evaluate_adapter.py'
spec=importlib.util.spec_from_file_location('adapter_eval',path)
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class GuardTest(unittest.TestCase):
    def test_exact_loop(self):
        self.assertEqual(module.repeated_tail(list(range(64))*4),64)
    def test_nonrepeating(self):
        self.assertIsNone(module.repeated_tail(list(range(2000))))
    def test_short_repeat_not_enough(self):
        self.assertIsNone(module.repeated_tail(list(range(64))*3))

if __name__=='__main__':
    unittest.main()
