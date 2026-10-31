"""Protect decorators, portable artifacts and family exclusions in task extraction."""
import ast
import unittest
from scripts.evaluation.task_test_pilot import extract_tests, validate_record


class TaskPilotTests(unittest.TestCase):
    def test_extraction_retains_parameterization_and_required_aliases(self):
        source=('import pytest\nimport os\nfrom example import check\n'
                '@pytest.mark.parametrize("value",[0,1])\n'
                'def test_check(value):\n    assert check(value)==value\n\n'
                'def test_unrelated():\n    assert False\n')
        selected=extract_tests(source,['test_check'])
        self.assertIn('@pytest.mark.parametrize',selected)
        self.assertIn('from example import check',selected)
        self.assertNotIn('import os',selected)
        self.assertNotIn('test_unrelated',selected)
        self.assertEqual(len(ast.parse(selected).body[-1].decorator_list),1)

    def test_nonexistent_selected_function_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing'):
            extract_tests('def test_real(): pass',['test_missing'])

    def test_called_helper_and_its_imports_are_retained(self):
        source='import math\ndef fixture_value(): return math.sqrt(4)\ndef test_value(): assert fixture_value()==2\ndef unused(): return 3\n'
        selected=extract_tests(source,['test_value'])
        self.assertIn('def fixture_value()',selected)
        self.assertIn('import math',selected)
        self.assertNotIn('def unused()',selected)
        exec(compile(selected,'<trusted-extraction-fixture>','exec'),namespace:={})
        namespace['test_value']()

    def test_holdout_family_and_path_escape_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'training families'):
            validate_record({'target_file':'tests/test_a.py','candidate_split':'train','source':{'parent_split':'eval'}})
        for path in ['tests/../../secret.py','C:/secret.py','/tests/test_a.py','tests\\test_a.py']:
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'target test path'):
                validate_record({'target_file':path})


if __name__=='__main__':unittest.main()
