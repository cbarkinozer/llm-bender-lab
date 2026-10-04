"""CPU-only checks of frozen evaluator inputs and blind ordering."""
import unittest
from evaluate_models import rows,repeated_tail
from import_comparison import balanced_mapping,POSITIONS,MODELS

class ExecutionTests(unittest.TestCase):
    def test_evaluation_inputs(self):
        data,hashes=rows()
        self.assertEqual(len(data),32)
        self.assertEqual(sum(r['split']=='control' for r in data),12)
        self.assertEqual(sum(r['split']=='validation' for r in data),20)
        self.assertEqual(len(hashes),2)
        self.assertTrue(all(r['evaluation_only'] for r in data))
    def test_balancing(self):
        ids=[str(i) for i in range(32)]
        mapping=balanced_mapping(ids)
        self.assertEqual(mapping,balanced_mapping(ids))
        self.assertGreater(len({tuple(m.values()) for m in mapping.values()}),4)
        for position in POSITIONS:
            for model in MODELS:
                self.assertEqual(sum(m[position]==model for m in mapping.values()),8)
        for assignment in mapping.values():
            self.assertEqual(set(assignment.values()),set(MODELS))
    def test_loop_guard(self):
        self.assertEqual(repeated_tail(list(range(32))*4),32)
        self.assertIsNone(repeated_tail(list(range(128))))
        self.assertIsNone(repeated_tail([1]*31))

if __name__=='__main__':
    unittest.main()
