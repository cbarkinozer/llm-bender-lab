import sys
import json
from pathlib import Path
import unittest

EXP=Path(__file__).resolve().parents[3]/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import active_paths
ACTIVE=active_paths()
def rows(path):return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]


class ReviewedIntentDataTests(unittest.TestCase):
    def test_plans_label_proposals_and_include_real_integration_tasks(self):
        plans=rows(ACTIVE['planning'])
        self.assertEqual(len(plans),15)
        for row in plans:
            plan=json.loads(row['messages'][-1]['content'])
            self.assertIn('proposed',plan['requirements_and_design']['interface_status'])
            self.assertTrue(plan['requirements_and_design']['blocking_behavior_decisions'])
            self.assertTrue(any(t['test_file'].startswith('tests/integration/') for t in plan['tasks']))
            for task in plan['tasks']:
                if 'delivery' in task['id']:
                    self.assertTrue(any(p.endswith('.py') for p in task['implementation_files']))

    def test_first_observed_baseline_cannot_be_silently_changed_to_first_positive(self):
        records=rows(ACTIVE['reliability'])
        record=next(r for r in records if r['record_id'].startswith('correct-wrong-baseline-test-'))
        self.assertIn('must not skip a bad observed value',record['messages'][1]['content'])
        self.assertEqual(json.loads(record['messages'][-1]['content'])['action'],'correct_inconsistent_test')

    def test_projection_has_78_records_and_no_audit_columns(self):
        total=0
        for name,count in [('tests',50),('planning',13),('reliability',15)]:
            projected=rows(ACTIVE['preview']/f'{name}-train-preview.jsonl')
            self.assertEqual(len(projected),count);total+=len(projected)
            for row in projected:self.assertEqual(set(row),{'messages'})
        self.assertEqual(total,78)


if __name__=='__main__': unittest.main()
