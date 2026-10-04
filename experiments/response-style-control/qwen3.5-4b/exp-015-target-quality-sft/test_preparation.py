import copy
import importlib.util
import json
import unittest
from prepare_pair import HERE,ROOT,F,C,DRAFT,PREFLIGHT,drafts,config,load,HASHES,sha

spec=importlib.util.spec_from_file_location('shared_reviewed_trainer',ROOT/'exp-009-minimal-edit/train_reviewed.py')
trainer=importlib.util.module_from_spec(spec); spec.loader.exec_module(trainer)

class PreparationTests(unittest.TestCase):
    def test_exact_prompts_ids_order(self):
        parent,e,f,val,new,controls,audit=drafts()
        self.assertEqual(len(e),80); self.assertEqual(len(f),104)
        self.assertEqual(e,f[:80]); self.assertEqual(len(new),24)
        self.assertEqual([r['messages'] for r in e],[r['messages'] for r in parent])
        self.assertEqual([r['id'] for r in e],[r['id'] for r in parent])
        self.assertEqual(sum(r['intervention']=='repair' for r in audit),9)

    def test_split_groups(self):
        parent,e,f,val,new,controls,audit=drafts()
        self.assertFalse({r['scenario_group_id'] for r in f} & {r['scenario_group_id'] for r in val+controls})
        self.assertTrue(all(r['evaluation_only'] and r['split']=='control' for r in controls))
        self.assertTrue(all(not r['evaluation_only'] and r['split']=='train' for r in f))

    def test_40_step_config_and_review_block(self):
        for arm,count in [('E',80),('F',104)]:
            c=config(arm)
            with self.assertRaises(ValueError): trainer.training_plan(c,'full')
            c['dataset']['review_required']=False
            plan=trainer.training_plan(c,'full')
            self.assertEqual(plan['max_steps'],40); self.assertEqual(plan['counts']['train'],count)
            self.assertEqual(plan['step_kwargs'],dict(save_steps=10,eval_steps=10))
            self.assertEqual(plan['eval_strategy'],'steps')

    def test_old_config_defaults(self):
        c=json.loads((C/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
        p=trainer.training_plan(c,'full')
        self.assertEqual(p['max_steps'],-1)
        self.assertEqual(p['counts'],dict(train=80,validation=20))
        self.assertEqual(p['save_strategy'],'epoch'); self.assertEqual(p['eval_strategy'],'epoch')
        self.assertEqual(p['step_kwargs'],{})

    def test_invalid_budget_counts(self):
        c=config('F'); c['dataset']['review_required']=False
        for steps in (0,1.5,True,-2):
            broken=copy.deepcopy(c); broken['training']['max_steps']=steps
            with self.assertRaises(ValueError): trainer.training_plan(broken,'full')
        c['dataset']['train_rows']=0
        with self.assertRaises(ValueError): trainer.training_plan(c,'full')

    def test_actual_tokens_and_masks(self):
        a=load(HERE/PREFLIGHT/'train-tokenized.jsonl')
        b=load(F/PREFLIGHT/'train-tokenized.jsonl')
        self.assertEqual(a,b[:80]); self.assertEqual(len(b),104)
        for row in a+b:
            self.assertTrue(all(x==-100 for x in row['labels'][:row['prompt_tokens']]))
            self.assertGreater(row['target_tokens'],1)
            self.assertLessEqual(len(row['input_ids']),1024)
        self.assertEqual(load(HERE/PREFLIGHT/'validation-tokenized.jsonl'),load(C/'training-preflight-v1/validation-tokenized.jsonl'))

    def test_historical_csv_inventories_checked(self):
        report=json.loads((HERE/DRAFT/'leakage-report.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(report['historical_entries_scanned'],348+3500+24)
        self.assertEqual(report['exact_matches'],[]); self.assertEqual(report['near_flags'],[])

    def test_parent_files_preserved(self):
        for name,expected in HASHES.items():
            self.assertEqual(sha((C/'data-reviewed-v1'/name).read_bytes()),expected)

    def test_pending_export_refused(self):
        from export_review import resolve
        from import_review import payload
        row=load(HERE/DRAFT/'review-candidates.jsonl')[0]
        snapshot=dict(total=1,items=[dict(external_id=row['id'],fields=payload(row),responses=[])])
        with self.assertRaises(ValueError): resolve([row],snapshot)

    def test_reject_or_empty_rewrite_refused(self):
        from export_review import resolve
        from import_review import payload
        row=load(HERE/DRAFT/'review-candidates.jsonl')[0]
        for decision in ('reject','rewrite'):
            snap=dict(total=1,items=[dict(external_id=row['id'],fields=payload(row),responses=[
                dict(status='submitted',values={'decision':{'value':decision}})])])
            with self.assertRaises(ValueError): resolve([row],snap)

    def test_source_fields_must_match(self):
        from export_review import resolve
        from import_review import payload
        row=load(HERE/DRAFT/'review-candidates.jsonl')[0]
        fields=payload(row); fields['conversation']='unexpected edited question'
        snap=dict(total=1,items=[dict(external_id=row['id'],fields=fields,responses=[])])
        with self.assertRaises(AssertionError): resolve([row],snap)

    def test_accept_and_rewrite_preserve_source(self):
        from export_review import resolve
        from import_review import payload
        row=load(HERE/DRAFT/'review-candidates.jsonl')[0]
        for decision in ('accept','rewrite'):
            response=dict(id='test-only-response',status='submitted',updated_at='test-timestamp',
                values={'decision':{'value':decision},'corrected_answer':{'value':'Corrected fixture answer'}})
            snap=dict(total=1,items=[dict(external_id=row['id'],fields=payload(row),responses=[response])])
            answer=resolve([row],snap)[0]
            self.assertEqual(answer['messages'],row['messages'])
            self.assertEqual(answer['desired_answer'],row['desired_answer'] if decision=='accept' else 'Corrected fixture answer')
            self.assertEqual(row['review_decision'],'pending')

if __name__=='__main__': unittest.main()
