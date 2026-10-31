import sys
import importlib.util
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

spec=importlib.util.spec_from_file_location('intent_preview',Path(__file__).resolve().parents[1]/'export_intent_only_preview.py')
preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        return dict(candidate_split='train',source_code='IMPLEMENTATION_SENTINEL',reference_implementation='REFERENCE_SENTINEL',
                    validation={'source_code':'NESTED_SENTINEL'},scoring_reference='GRADER_SENTINEL',
                    messages=[dict(role='system',content='Write tests',source_code='MESSAGE_SENTINEL'),
                              dict(role='user',content='Build a calculator'),
                              dict(role='assistant',reasoning_content='Check boundary values.',content='def test_sum():\n    assert add(1,2)==3')])

    def test_source_and_audit_columns_cannot_enter_model_text(self):
        import json
        result=preview.project_record(self.fixture())
        self.assertEqual(set(result),{'messages'})
        self.assertNotIn('SENTINEL',json.dumps(result))
        self.assertIn('def test_sum',result['messages'][-1]['content'])
        self.assertEqual(result['messages'][-1]['reasoning_content'],'Check boundary values.')

    def test_heldout_records_are_rejected(self):
        for split in ('development','holdout'):
            row=self.fixture();row['candidate_split']=split
            with self.assertRaises(ValueError): preview.project_record(row)


if __name__=='__main__': unittest.main()
