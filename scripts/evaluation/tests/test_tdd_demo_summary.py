import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from summarize_tdd_demo_review import aggregate_human, aggregate_static, review_rows
from publish_tdd_threeway_argilla import payload


def test_pairwise_ties_are_not_counted_as_wins_or_retains():
    reviews = [dict(ranks=dict(base=1, arm_A=2, arm_B=2),
                    assessments=dict(base='repair', arm_A='reject', arm_B='reject')),
               dict(ranks=dict(base=2, arm_A=1, arm_B=1),
                    assessments=dict(base='reject', arm_A='reject', arm_B='reject'))]
    result = aggregate_human(reviews)
    assert result['pairwise']['arm_A_vs_arm_B'] == dict(first_preferred=0, tied=2, second_preferred=0)
    assert result['models']['base']['sole_best'] == 1
    assert result['models']['arm_A']['tied_best'] == 1
    assert result['models']['arm_A']['assessments'] == {'reject': 2}


def test_failed_outputs_never_become_smell_free_test_suites():
    records = []
    for model in ('base', 'arm_A', 'arm_B'):
        for analysis in [dict(status='unparseable', test_functions=0, sites=[], smells={}),
                         dict(status='parseable', test_functions=0, sites=[], smells={'x': dict(flagged=False)})]:
            records.append(dict(model=model, analysis=analysis))
    result = aggregate_static(records, ['x'])
    assert result['base']['files_with_recognized_test_functions'] == 0
    assert result['base']['unparseable'] == 1
    assert result['base']['parseable_without_test_functions'] == 1
    assert result['base']['flagged_files_by_smell']['x'] == 0


def test_primary_only_gate_accepts_skipped_other_reviews_but_rejects_mismatched_content():
    item = dict(case_id='case', requirement='R', candidates=dict(X='pass', Y='pass', Z='pass'))
    receipt = dict(datasets={'primary': dict(index=[dict(record_id='r', key='case')])})
    values = dict(ranking=dict(value=[dict(value='X', rank=1), dict(value='Y', rank=2), dict(value='Z', rank=2)]),
                  evidence=dict(value='All unusable; X is less incomplete'))
    values.update({'assessment_'+label: dict(value='reject') for label in ('x', 'y', 'z')})
    row = dict(external_id='r', fields=payload(item, True), responses=[dict(status='submitted', values=values)])
    snapshot = dict(total=1, items=[row])
    mapping = {'case': dict(X='base', Y='arm_A', Z='arm_B')}
    result = review_rows(snapshot, receipt, mapping, [item])
    assert result[0]['ranks'] == dict(base=1, arm_A=2, arm_B=2)
    row['fields']['requirement'] = 'Different prompt'
    with pytest.raises(ValueError, match='does not match'):
        review_rows(snapshot, receipt, mapping, [item])
