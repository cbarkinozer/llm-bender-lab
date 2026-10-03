"""CPU tests: unchanged source/splits, controlled recipe, strict review gate."""
import copy
import json
import unittest
from collections import Counter

from prepare_pair import (A,HERE,ROOT,HIGH_SIGNAL,REMOVED,candidates,original,
                          make_config,load_rows,SOURCE_HASHES,sha)
from export_review import approved_targets

def records_for(rows):
    return [dict(external_id=r['id'],fields=dict(
        conversation='\n\n'.join(m['role']+': '+m['content'] for m in r['messages']),
        proposed_answer=r['desired_answer'],substance_check=r['evaluation_criteria'],
        category=r['category'],replacement=r['replaces_id']),responses=[dict(
        status='submitted',id='mock-'+r['id'],updated_at='test-only',
        values={'decision':{'value':'accept'}})]) for r in rows]

class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.train,self.validation=original()
        self.new=candidates()
    def test_candidate_count_unique_groups_and_replacements(self):
        self.assertEqual(len(self.new),24)
        self.assertEqual(len({r['id'] for r in self.new}),24)
        self.assertEqual(len({r['scenario_group_id'] for r in self.new}),24)
        self.assertEqual([r['replaces_id'] for r in self.new],REMOVED)
    def test_composition_and_unchanged_retained_rows(self):
        mapping={r['replaces_id']:r for r in self.new}
        draft=[mapping.get(r['id'],r) for r in self.train]
        self.assertEqual(len(draft),80)
        retained=[r for r in draft if r['id'].startswith('me-')]
        self.assertEqual(len(retained),56)
        self.assertTrue(all(r in self.train for r in retained))
        self.assertEqual(Counter(r['category'] for r in draft),{
            'grammar_correction':2,'answer_extraction':2,'numeric_entity_precision':2,
            'faithful_summary':2,'useful_explanation':18,'grounded_completion':14,
            'selective_clarification':12,'consistency_integrity':12,
            'turkish_lexical_precision':8,'non_anthropomorphic_interaction':8})
    def test_high_signal_items_remain_validation_only(self):
        self.assertTrue(set(HIGH_SIGNAL)<=set(r['id'] for r in self.validation))
        self.assertFalse(set(HIGH_SIGNAL)&set(r['id'] for r in self.train+self.new))
        self.assertEqual(len(self.validation),20)
    def test_only_duration_training_fields_change(self):
        old=json.loads((ROOT/'exp-010-lr-ablation/config.yaml').read_text(encoding='utf-8'))
        a=make_config(A.name,True)
        b=make_config(HERE.name,False,'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH')
        differences={k for k in old['training'] if old['training'][k]!=a['training'][k]}
        self.assertEqual(differences,{'epochs','expected_optimizer_steps'})
        self.assertEqual(a['training'],b['training'])
        self.assertEqual(a['model'],b['model'])
        self.assertEqual(a['inference'],b['inference'])
        self.assertEqual(a['training']['expected_optimizer_steps'],40)
    def test_all_accepted_reviews_keep_proposed_targets(self):
        mapping=approved_targets(records_for(self.new),self.new)
        self.assertEqual(len(mapping),24)
        self.assertTrue(all(mapping[r['replaces_id']]['desired_answer']==r['desired_answer'] for r in self.new))
    def test_explicit_conversation_approval(self):
        approval=json.loads((HERE/'user-approval.json').read_text(encoding='utf-8'))
        rows=records_for(self.new)
        for row in rows: row['responses']=[]
        result=approved_targets(rows,self.new,approval)
        self.assertEqual(len(result),24)
        self.assertTrue(all(r['review_response_id'] is None for r in result.values()))
        self.assertTrue(all(r['review_provenance']=='user-conversation-approval' for r in result.values()))
    def test_conversation_approval_wrong_hash_blocks(self):
        approval=json.loads((HERE/'user-approval.json').read_text(encoding='utf-8'))
        approval['candidate_sha256']='wrong'
        rows=records_for(self.new)
        for row in rows: row['responses']=[]
        with self.assertRaises(ValueError): approved_targets(rows,self.new,approval)
    def test_conversation_approval_missing_id_blocks(self):
        approval=json.loads((HERE/'user-approval.json').read_text(encoding='utf-8'))
        approval['candidate_ids'].pop()
        rows=records_for(self.new)
        for row in rows: row['responses']=[]
        with self.assertRaises(ValueError): approved_targets(rows,self.new,approval)
    def test_conversation_approval_does_not_override_annotations(self):
        approval=json.loads((HERE/'user-approval.json').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError): approved_targets(records_for(self.new),self.new,approval)
    def test_incomplete_review_blocks(self):
        rows=records_for(self.new); rows[0]['responses']=[]
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_reject_blocks(self):
        rows=records_for(self.new); rows[0]['responses'][0]['values']['decision']['value']='reject'
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_empty_rewrite_blocks(self):
        rows=records_for(self.new); rows[0]['responses'][0]['values']['decision']['value']='rewrite'
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_duplicate_reviewer_blocks(self):
        rows=records_for(self.new); rows[0]['responses']*=2
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_changed_prompt_blocks(self):
        rows=records_for(self.new); rows[0]['fields']['conversation']='changed'
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_accept_with_ignored_correction_blocks(self):
        rows=records_for(self.new)
        rows[0]['responses'][0]['values']['corrected_answer']={'value':'Yeni cevap'}
        with self.assertRaises(ValueError): approved_targets(rows,self.new)
    def test_rewrite_preserves_input_and_uses_correction(self):
        rows=records_for(self.new)
        rows[0]['responses'][0]['values'].update(decision={'value':'rewrite'},
            corrected_answer={'value':'  Düzeltilmiş cevap.  '})
        result=approved_targets(rows,self.new)[REMOVED[0]]
        self.assertEqual(result['messages'],self.new[0]['messages'])
        self.assertEqual(result['desired_answer'],'Düzeltilmiş cevap.')
    def test_draft_preflight_is_not_trainable(self):
        report=json.loads((HERE/'training-preflight-draft-v1/report.json').read_text(encoding='utf-8'))
        self.assertNotEqual(report['status'],'local-preflight-passed')
        config=json.loads((HERE/'config.yaml').read_text(encoding='utf-8'))
        self.assertTrue(config['dataset']['review_required'])
        self.assertEqual(config['dataset']['hashes']['train-reviewed.jsonl'],
                         'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH')
    def test_validation_bytes_and_tokens_unchanged(self):
        path=HERE/'data-draft-v1/validation-reviewed.jsonl'
        self.assertEqual(sha(path.read_bytes()),SOURCE_HASHES['validation-reviewed.jsonl'])
        self.assertEqual(load_rows(HERE/'training-preflight-draft-v1/validation-tokenized.jsonl'),
                         load_rows(A/'training-preflight-v1/validation-tokenized.jsonl'))

if __name__=='__main__':
    unittest.main()
