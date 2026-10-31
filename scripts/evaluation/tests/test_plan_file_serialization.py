import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import active_paths, rows
from serialize_plan_files import ancestors, conflicts, serialize


def task(id,path,deps=()):return dict(id=id,implementation_files=[path],depends_on=list(deps))


class SerializationTests(unittest.TestCase):
    def test_preserves_reverse_list_order_dependencies_and_parallel_independent_files(self):
        tasks=[task('later','shared.py',['first']),task('independent','other.py'),task('first','shared.py')]
        self.assertFalse(conflicts(tasks))
        self.assertEqual(serialize(tasks),[])
        self.assertEqual(tasks[1]['depends_on'],[])

    def test_detects_sibling_conflict_and_orders_without_cycle(self):
        tasks=[task('base','base.py'),task('left','same.py',['base']),task('right','same.py',['base']),task('other','other.py')]
        self.assertEqual(len(conflicts(tasks)),1)
        self.assertTrue(serialize(tasks));self.assertFalse(conflicts(tasks))
        self.assertIn('left',ancestors(tasks)['right'])
        self.assertEqual(tasks[-1]['depends_on'],[])

    def test_transitive_order_and_normalized_paths(self):
        tasks=[task('a','src\\same.py'),task('b','other.py',['a']),task('c','src/./same.py',['b'])]
        self.assertFalse(conflicts(tasks));self.assertEqual(serialize(tasks),[])

    def test_rejects_unknown_dependencies_and_cycles(self):
        for tasks in ([task('a','x.py',['missing'])],[task('a','x.py',['b']),task('b','y.py',['a'])]):
            with self.assertRaises(ValueError):serialize(tasks)

    def test_active_plans_children_and_preview_all_have_serialized_graphs(self):
        paths=active_paths();plans=rows(paths['planning'])
        children=rows(paths['planning'].parent/'materialized-child-inputs.jsonl')
        projected=rows(paths['preview']/'planning-train-preview.jsonl')
        for row in plans:
            plan=json.loads(row['messages'][-1]['content'])
            self.assertFalse(conflicts(plan['tasks']),row['record_id'])
            for t in plan['tasks']:
                child=next(c for c in children if c['plan_id']==row['record_id'] and c['task_id']==t['id'])
                self.assertEqual(child['depends_on'],t['depends_on'])
        self.assertEqual([r['messages'] for r in projected],[r['messages'] for r in plans if r['candidate_split']=='train'])

    def test_inventory_preserves_evaluation_family_roles(self):
        paths=active_paths();actual={}
        for path in (paths['tests'],paths['planning'],paths['reliability']):
            for r in rows(path):
                self.assertEqual(actual.setdefault(r['source_group'],r['candidate_split']),r['candidate_split'])
        config=paths['config']
        self.assertEqual(config['source_families'],sorted(actual))
        self.assertEqual(config['training_source_families'],sorted(k for k,v in actual.items() if v=='train'))
        self.assertEqual(config['source_families_by_split']['development'],['darrenburns/posting'])
        self.assertEqual(config['source_families_by_split']['holdout'],['jarun/ddgr'])


if __name__=='__main__':unittest.main()
