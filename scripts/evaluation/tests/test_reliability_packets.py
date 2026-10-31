import sys
"""Protect held-out answers and counterexamples in the new preparation packets."""
import json
from pathlib import Path
import unittest

EXP=Path(__file__).resolve().parents[3]/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import active_paths
ACTIVE=active_paths()


def rows(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


class ReliabilityPacketTests(unittest.TestCase):
    def test_model_requests_exclude_targets_and_training_families(self):
        requests=rows(ACTIVE['baseline']/'requests.jsonl')
        self.assertEqual(len(requests),17)
        train_groups={r['source_group'] for r in rows(ACTIVE['reliability'].parent/'train-candidates.jsonl')}
        for row in requests:
            self.assertNotIn(row['source_group'],train_groups)
            self.assertEqual([m['role'] for m in row['messages']],['system','user'])
            self.assertNotIn('scoring_reference',row)
            self.assertNotIn('reference_target',row)
        references=rows(ACTIVE['baseline']/'scoring-references.jsonl')
        expected={r['record_id']:r for path in (ACTIVE['planning'],ACTIVE['reliability']) for r in rows(path) if r['candidate_split']!='train'}
        for reference in references:
            if reference['record_id'] in expected:
                self.assertEqual(reference['reference_target'],expected[reference['record_id']]['messages'][-1])

    def test_training_has_ask_proceed_and_justified_oracle_corrections(self):
        train=rows(ACTIVE['reliability'].parent/'train-candidates.jsonl')
        self.assertTrue(all(r['candidate_split']=='train' and not r['training_eligible'] for r in train))
        actions={json.loads(r['messages'][-1]['content'])['action'] for r in train}
        self.assertEqual(actions,{'ask','proceed','preserve_contract_and_repair','correct_inconsistent_test'})

    def test_preflight_revision_replaces_one_row_without_inflating_count(self):
        active=rows(ACTIVE['tests'])
        self.assertEqual(len(active),58)
        matches=[r for r in active if r['task_id']=='experiment-preflight']
        self.assertEqual(len(matches),1)
        self.assertIn('test_valid_preflight_reaches_backend',matches[0]['test_functions'])
        runs=matches[0]['validation']['runs']
        self.assertTrue(next(r for r in runs if r['condition']=='reject-every-input')['killed'])


if __name__=='__main__': unittest.main()
