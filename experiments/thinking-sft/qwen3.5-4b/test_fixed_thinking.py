import unittest

from fixed_thinking_matrix import BUDGETS,selected_attempts,request_for
from test_recovery import attempt


class FixedThinkingChecks(unittest.TestCase):
    def test_completed_and_limited_thinking_both_rerun(self):
        rows=[attempt(),attempt(finish='eos',generated=100),attempt('base-thinking-false')]
        self.assertEqual(selected_attempts(rows),rows[:2])

    def test_only_one_budget_and_fixed_time_allowance(self):
        self.assertEqual(BUDGETS,(16384,))
        for old in [attempt(),attempt(finish='eos',generated=100)]:
            new=request_for(old,16384)
            self.assertEqual(new['n_predict'],16384)
            self.assertEqual(new['t_max_predict_ms'],1200000)
            self.assertEqual({k for k in new if new[k]!=old['request'][k]},
                             {'n_predict','t_max_predict_ms'})

    def test_adaptive_budget_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'exactly16384'):
            request_for(attempt(),8192)


if __name__=='__main__':unittest.main()
