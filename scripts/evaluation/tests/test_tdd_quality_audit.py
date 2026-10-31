import sys
import importlib.util
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

spec=importlib.util.spec_from_file_location('quality_audit',Path(__file__).resolve().parents[1]/'audit_tdd_quality.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class QualityAuditTests(unittest.TestCase):
    def test_auditor_output_covers_active_replacement(self):
        import json
        from active_tdd_data import active_paths, rows, EXP
        paths=active_paths()
        report=json.loads((EXP/paths['config']['active_test_quality_audit']).read_text(encoding='utf-8'))
        self.assertEqual({r['record_id'] for r in report['rows']},{r['record_id'] for r in rows(paths['tests'])})
        replacement=next(r for r in report['rows'] if r['task_id']=='experiment-preflight')
        self.assertEqual(replacement['record_id'],'experiment-preflight-quality-after-v01')
        self.assertNotIn('only-expected-exceptions-no-observable-success-control',{f['kind'] for f in replacement['findings']['flags']})

    def flags(self,text):
        return {r['kind'] for r in audit.inspect_tests(text)['flags']}

    def test_numeric_oracles_are_not_mistaken_for_no_assertions(self):
        for text in ('assert_frame_equal(actual, expected)', 'torch.testing.assert_close(actual,expected)'):
            self.assertNotIn('no-recognized-oracle-review-custom-helpers',self.flags(text))

    def test_negative_only_spy_is_flagged(self):
        text='with pytest.raises(ValueError):\n    run(data)\ntrainer.assert_not_called()\n'
        self.assertIn('only-expected-exceptions-no-observable-success-control',self.flags(text))
        self.assertNotIn('only-expected-exceptions-no-observable-success-control',self.flags(text+'assert run(valid)["status"] == "completed"\n'))

    def test_skip_tautology_and_broad_exception_request_review(self):
        text='@pytest.mark.skip\ndef test_bad():\n    assert result == result\n    with pytest.raises(Exception):\n        run()\n'
        flags=self.flags(text)
        self.assertTrue({'disabled-or-expected-failing-test','self-comparison','broad-expected-exception'}<=flags)


if __name__=='__main__': unittest.main()
