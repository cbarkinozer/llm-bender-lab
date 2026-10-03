"""CPU tests: no fabricated approval, no silent source changes, same C/D data."""
import copy
import json
import unittest
from prepare_next_pair import HERE, D, candidates, assemble, original, make_config, SOURCE_HASHES, sha, PARENT
from export_review import approved_targets, apply_postreview_qa
from import_review import payload


def records():
    return [dict(external_id=r['id'],fields=payload(r),responses=[dict(id='test-only',
        status='submitted',updated_at='test-only',values={'decision':{'value':'accept'}})]) for r in candidates()]


class PreparationTests(unittest.TestCase):
    def qa_fixture(self):
        rs=records()
        rs[4]['responses'][0]['values']={'decision':{'value':'rewrite'},
            'corrected_answer':{'value':'Kabloyu deneyin; görüntü gelirse sorun kablodadır.'}}
        rows=approved_targets(rs,candidates())
        from prepare_next_pair import jsonl
        approval=dict(source='user-conversation',decision='apply-two-scoped-postreview-corrections',
            reviewed_candidates_sha256=sha(jsonl(rows)),user_message='test-only authority',approval_date='test-only',
            authorized_changes=[{'id':'tc-005'},{'id':'tc-010'}])
        return rows,approval

    def test_two_qa_edits_preserve_review_provenance_and_others(self):
        rows,approval=self.qa_fixture()
        updated,changes=apply_postreview_qa(rows,approval)
        self.assertEqual({r['id'] for r in changes},{'tc-005','tc-010'})
        for old,new in zip(rows,updated):
            self.assertEqual(old['review_decision'],new['review_decision'])
            self.assertEqual(old['review_response_id'],new['review_response_id'])
            if old['id'] not in ('tc-005','tc-010'): self.assertEqual(old,new)
        self.assertNotIn("'Doktora'",updated[9]['messages'][0]['content'])
        self.assertEqual(updated[9]['desired_answer'],rows[9]['desired_answer'])
        self.assertIn('bağlantısı güçlü bir şüpheli',updated[4]['desired_answer'])

    def test_qa_rejects_mismatched_hash_or_scope(self):
        rows,approval=self.qa_fixture()
        approval['reviewed_candidates_sha256']='wrong'
        with self.assertRaises(ValueError): apply_postreview_qa(rows,approval)
        rows,approval=self.qa_fixture(); approval['authorized_changes'].append({'id':'tc-001'})
        with self.assertRaises(ValueError): apply_postreview_qa(rows,approval)

    def test_namesake_modules_resolve_here(self):
        import export_review
        import import_review
        from pathlib import Path
        self.assertEqual(Path(export_review.__file__).parent, HERE)
        self.assertEqual(Path(import_review.__file__).parent, HERE)

    def test_original_hashes_unchanged(self):
        for name, expected in SOURCE_HASHES.items():
            self.assertEqual(sha((PARENT/'reviewed-v2'/name).read_bytes()), expected)

    def test_68_retained_and_all_higher_level_rows_preserved(self):
        train, val = assemble(candidates())
        old, oldval = original()
        retained = [r for r in train if r['id'].startswith('me-')]
        self.assertEqual(len(retained), 68)
        self.assertEqual(val, oldval)
        self.assertTrue(all(r in old for r in retained))
        self.assertTrue(all(r in retained for r in old if int(r['id'].split('-')[1]) > 40))

    def test_two_recipes_change_only_duration(self):
        c, d = make_config(HERE.name), make_config(D.name)
        self.assertEqual(c['dataset'], d['dataset'])
        self.assertEqual(c['model'], d['model'])
        self.assertEqual(c['inference'], d['inference'])
        ct, dt = copy.deepcopy(c['training']), copy.deepcopy(d['training'])
        self.assertEqual((ct.pop('epochs'),dt.pop('epochs')), (4,6))
        self.assertEqual((ct.pop('expected_optimizer_steps'),dt.pop('expected_optimizer_steps')), (40,60))
        self.assertEqual(ct, dt)

    def test_draft_blocked_without_hash(self):
        for name in (HERE.name,D.name):
            c=make_config(name)
            self.assertEqual(c['status'], 'blocked-human-review')
            self.assertTrue(c['dataset']['review_required'])
            self.assertEqual(c['dataset']['hashes']['train-reviewed.jsonl'], 'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH')

    def test_accept_preserves_targets(self):
        approved=approved_targets(records(), candidates())
        self.assertEqual([r['desired_answer'] for r in approved], [r['desired_answer'] for r in candidates()])
        self.assertTrue(all(r['review_provenance']=='argilla-submitted' for r in approved))

    def test_pending_and_rejected_fail(self):
        for mode in ('pending','reject'):
            rs=records()
            if mode=='pending': rs[0]['responses']=[]
            else: rs[0]['responses'][0]['values']['decision']['value']='reject'
            with self.assertRaises(ValueError): approved_targets(rs,candidates())

    def test_rewrite_requires_nonempty_target(self):
        rs=records(); values=rs[0]['responses'][0]['values']
        values['decision']['value']='rewrite'
        with self.assertRaises(ValueError): approved_targets(rs,candidates())
        values['corrected_answer']={'value':'A reviewed replacement'}
        self.assertEqual(approved_targets(rs,candidates())[0]['desired_answer'], 'A reviewed replacement')

    def test_changed_fields_or_duplicate_ids_fail(self):
        rs=records(); rs[0]['fields']['proposed_answer']='Changed target'
        with self.assertRaises(ValueError): approved_targets(rs,candidates())
        rs=records(); rs[-1]=copy.deepcopy(rs[0])
        with self.assertRaises(ValueError): approved_targets(rs,candidates())

    def test_correction_with_accept_fails(self):
        rs=records(); rs[0]['responses'][0]['values']['corrected_answer']={'value':'A different target'}
        with self.assertRaises(ValueError): approved_targets(rs,candidates())


if __name__=='__main__':
    unittest.main()
