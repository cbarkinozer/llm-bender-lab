"""Original benchmark identity, context preservation and artifact-parity guards."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import occam_matrix as matrix
from review_occam_matrix import positions,CONDITIONS


class MatrixChecks(unittest.TestCase):
    def test_original_twenty_and_controls_are_unchanged_prompt_only(self):
        prompts, keys = matrix.benchmark()
        self.assertEqual(sum(r['cohort']=='original20' for r in prompts),20)
        self.assertEqual(sum(r['cohort']=='controls12' for r in prompts),12)
        self.assertEqual({r['id'] for r in prompts},{r['id'] for r in keys})
        self.assertTrue(all('reference' not in r and 'evaluation_criteria' not in r for r in prompts))
        multi=next(r for r in prompts if r['id']=='me-059')
        self.assertEqual([m['role'] for m in multi['messages']],['user','assistant','user'])

    def test_mismatched_quantization_is_rejected(self):
        a=dict(tensors={'layer':dict(shape=[2,2],type=12)},template='native',vocabulary=['x'],token_types=[1],file_type=15)
        b=a|dict(tensors={'layer':dict(shape=[2,2],type=14)})
        with patch.object(matrix,'gguf_signature',side_effect=[a,b]):
            with self.assertRaisesRegex(ValueError,'tensors mismatch'):
                matrix.validate_artifacts(None,None,SimpleNamespace(chat_template='native'))

    def test_unfinished_thinking_is_not_a_final_answer(self):
        self.assertEqual(matrix.output_parts('Bir olasılık daha...',True),('Bir olasılık daha...',''))
        self.assertEqual(matrix.output_parts('İki koşul sağlandı.\n</think>\nEvet.',True),
                         ('İki koşul sağlandı.','Evet.'))
        self.assertEqual(matrix.output_parts('Kısa yanıt.',False),('','Kısa yanıt.'))

    def test_review_positions_are_balanced_and_reproducible(self):
        ids=[row['id'] for row in matrix.benchmark()[0]]
        mapping=positions(ids)
        self.assertEqual(mapping,positions(ids))
        for position in 'ABCD':
            self.assertEqual({c:sum(row[position]==c for row in mapping.values()) for c in CONDITIONS},
                             {c:8 for c in CONDITIONS})


if __name__=='__main__':
    unittest.main()
