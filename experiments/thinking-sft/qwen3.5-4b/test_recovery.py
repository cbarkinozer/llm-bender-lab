import copy
import unittest

from recover_thinking_limits import request_for, selected_attempts, still_token_limited, summary


def attempt(condition='base-thinking-true', finish='limit', budget=4096, generated=4096):
    return dict(id='example',condition=condition,cohort='original20',thinking=condition.endswith('true'),
        request=dict(prompt='unchanged native prompt',n_predict=budget,t_max_predict_ms=180000,
                     temperature=0,repeat_last_n=8192,seed=3407),
        response=dict(stop_type=finish,tokens_predicted=generated),answer='')


class RecoveryChecks(unittest.TestCase):
    def test_only_limited_thinking_is_selected(self):
        rows=[attempt(),attempt('base-thinking-false'),attempt(finish='eos',generated=100)]
        self.assertEqual(selected_attempts(rows),rows[:1])

    def test_only_output_and_time_allowance_change(self):
        old=attempt()
        snapshot=copy.deepcopy(old)
        new=request_for(old,8192)
        self.assertEqual({k for k in new if new[k]!=old['request'][k]},
                         {'n_predict','t_max_predict_ms'})
        self.assertEqual(new['n_predict'],8192)
        self.assertGreater(new['t_max_predict_ms'],old['request']['t_max_predict_ms'])
        self.assertEqual(old,snapshot)

    def test_time_limit_is_not_mislabeled_token_limit(self):
        self.assertTrue(still_token_limited(attempt(budget=8192,generated=8192)))
        self.assertFalse(still_token_limited(attempt(budget=8192,generated=4000)))
        self.assertFalse(still_token_limited(attempt(finish='eos',generated=100)))

    def test_overlay_preserves_original_and_reports_remaining_limits(self):
        old=attempt()
        new=attempt(finish='eos',budget=8192,generated=5000)
        new['answer']='Tamamlandı.'
        result=summary([old],[new],True)
        cell=result['conditions']['base-thinking-true']['original20']
        self.assertEqual((cell['items'],cell['natural_eos'],cell['still_limited']),(1,1,0))
        self.assertEqual(old['response']['stop_type'],'limit')


if __name__=='__main__':unittest.main()
