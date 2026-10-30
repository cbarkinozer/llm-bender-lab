"""The shareable example must include the evidence reviewers need for Q5."""
import unittest
from scripts.evaluation.export_tdd_review_example import build_text


class ExportTests(unittest.TestCase):
    def test_exports_kills_per_requirement_and_leaves_ratings_blank(self):
        row={'record_id':'example-v1','messages':[{'content':'system'},{'content':'request'},{'content':'tests'}],
             'teacher_reasoning':'rationale','source':{'repo':'example','revision':'abc'},
             'split':'train','leakage_group':'example','tokens':{'full_sequence':100},
             'validation':{'reference_pass':True,'stability':[{'seed':17}],
                 'fault_coverage_by_core_requirement':{'R1':['bad-tie'],'R5':['bad-read']},
                 'faults':[{'fault':'bad-tie','killed':True,'failing_tests':['test_tie']},
                           {'fault':'bad-read','killed':True,'failing_tests':['test_read']}]}}
        form=[{'title':'Q7. Decision','options':['approve','revise'],'kind':'single-choice','required':True}]
        text=build_text(row,form,'guidelines')
        evidence=text.split('TARGETED KILLS BY CORE REQUIREMENT')[1].split('ANNOTATION FORM')[0]
        for token in ['R1:','R5:','bad-tie — DETECTED','bad-read — DETECTED','test_tie','test_read']:
            self.assertIn(token,evidence)
        self.assertIn('Options: approve | revise',text)
        self.assertIn('Answer: ______________________________',text)
        self.assertNotIn('Answer: approve',text)

    def test_missing_kill_evidence_is_rejected(self):
        row={'record_id':'example','messages':[{'content':'s'},{'content':'u'},{'content':'a'}],
             'teacher_reasoning':'r','source':{'repo':'r','revision':'c'},'split':'train','leakage_group':'r',
             'tokens':{'full_sequence':1},'validation':{'reference_pass':True,'stability':[],
                 'fault_coverage_by_core_requirement':{'R1':[]},'faults':[]}}
        with self.assertRaisesRegex(AssertionError,'R1'):
            build_text(row,[],'guidelines')

if __name__=='__main__':unittest.main()
