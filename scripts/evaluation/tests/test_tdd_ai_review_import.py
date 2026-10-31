"""Portable reviews must retain IDs, multiline evidence and exact label strings."""
import unittest
from scripts.evaluation.import_tdd_ai_review import parse_review


class ReviewParsingTests(unittest.TestCase):
    def test_preserves_bullets_and_two_records(self):
        rows=parse_review('record_id: one\nblocking_issues:\n- first\n- second\n\n----\n\nrecord_id: two\nblocking_issues: none\n')
        self.assertEqual([row['record_id'] for row in rows],['one','two'])
        self.assertEqual(rows[0]['blocking_issues'].strip(),'- first\n- second')
        self.assertEqual(rows[1]['blocking_issues'],'none')

    def test_duplicate_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate field'):
            parse_review('record_id: one\napproval: approve\napproval: revise')

    def test_unstructured_prefix_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'before first field'):
            parse_review('Here is my review\nrecord_id: one')


if __name__=='__main__':unittest.main()
