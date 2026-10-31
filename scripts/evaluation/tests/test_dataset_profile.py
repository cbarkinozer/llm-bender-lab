import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from profile_tdd_dataset import stats,complexity,diversity,purpose,similarities


class DatasetProfileTests(unittest.TestCase):
    def test_class_methods_closures_and_inner_methods_count_once(self):
        source='class Example:\n    def method(self):\n        def inner():\n            return 1\n        return inner()\n    class Nested:\n        def nested_method(self):\n            return 2\n'
        result=complexity(source)
        self.assertEqual(sorted(f['name'] for f in result['functions']),['inner','method','nested_method'])

    def test_population_and_sample_std_are_distinguished(self):
        s=stats([1,2,3])
        self.assertEqual(s['mean'],2)
        self.assertAlmostEqual(s['std_population'],math.sqrt(2/3))
        self.assertEqual(s['std_sample'],1)
        self.assertEqual(s['median'],2)
        self.assertEqual(stats([]),{'n':0})

    def test_assertions_do_not_inflate_assert_excluded_complexity(self):
        data=complexity('def test_x():\n    assert x == 1\n    assert y == 2\n')
        f=data['functions'][0]
        self.assertEqual(f['cc'],3);self.assertEqual(f['cc_without_asserts'],1)
        data=complexity('def test_x():\n    if flag:\n        assert x\n')
        self.assertEqual(data['functions'][0]['cc_without_asserts'],2)

    def test_effective_category_count_does_not_claim_row_independence(self):
        self.assertAlmostEqual(diversity({'a':5,'b':5})['effective_categories'],2)
        self.assertEqual(diversity({'a':10})['effective_categories'],1)

    def test_test_purpose_excludes_shared_system_and_interface_boilerplate(self):
        row={'task_id':'read-file','acceptance_criteria':['Preserve UTF-8 and reject invalid bytes.'],
             'messages':[{'content':'SHARED_SYSTEM'},{'content':'SHARED_INTERFACE'}]}
        result=purpose(row,'tests')
        self.assertIn('UTF-8',result);self.assertNotIn('SHARED',result)

    def test_candidate_scores_do_not_create_duplicate_verdicts(self):
        pairs=similarities(['Unicode cache page','Unicode cache page','tensor causal logits'])
        score,i,j=pairs[0]
        self.assertEqual({i,j},{0,1});self.assertAlmostEqual(score,1)


if __name__=='__main__':unittest.main()
