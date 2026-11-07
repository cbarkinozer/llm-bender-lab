import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publish_tdd_taxonomy_argilla import analyze, make_rows, require_complete


def test_oracle_strength_is_separate_from_correctness_and_never_executes(tmp_path):
    marker = tmp_path/'must-not-exist'
    code = (f"open({str(marker)!r}, 'w').write('bad')\n"
            "from posting.urls import substitute_path_params\n"
            "def test_contract():\n"
            "    result = substitute_path_params('/x/:id', {'id': '1'})\n"
            "    assert True\n"
            "    assert result is not None\n"
            "    assert result == 'wrong expectation'\n")
    result = analyze(code)
    assert not marker.exists()
    assert [s['oracle_class'] for s in result['sites']] == ['TRIVIAL', 'WEAK', 'STRONG']
    assert result['runtime_reached'] == 'not_measured'


def test_administrative_statuses_are_not_weak_or_unknown():
    assert analyze('[No complete Python output]')['status'] == 'unparseable'
    result = analyze('def test_empty():\n    pass\n')
    assert result['status'] == 'no_oracle' and result['sites'] == []


def test_smells_have_positive_and_negative_controls():
    clean = analyze('def test_value():\n    assert value() == "expected"\n')
    bad = analyze('def test_value():\n    assert True\n    assert False\n')
    assert not clean['smells']['trivial_assertion']['flagged']
    assert bad['smells']['trivial_assertion']['flagged']
    assert bad['smells']['assertion_roulette']['evidence'][0]['lineno'] == 1
    assert len(bad['smells']) == 11


def test_independent_payload_does_not_expose_predictions_or_identities():
    item = dict(case_id='case', requirement='R', candidates=dict(X='assert True', Y='pass', Z='broken!'),
                model_identity='secret', judgment={'winner': 'X'})
    oracles, smells, automatic = make_rows([item])
    assert len(smells) == 3 and len(oracles) == 3
    for row in oracles + smells:
        assert set(row['fields']) <= {'requirement', 'candidate', 'target'}
        assert 'secret' not in str(row) and 'oracle_class' not in str(row['fields'])
    assert automatic[0]['analysis']['sites'][0]['oracle_class'] == 'TRIVIAL'


def test_predictions_cannot_be_revealed_before_all_independent_submissions():
    with pytest.raises(ValueError): require_complete(dict(total=1, items=[dict(responses=[])]))
    with pytest.raises(ValueError): require_complete(dict(total=1, items=[dict(responses=[dict(status='draft')])]))
    with pytest.raises(ValueError): require_complete(dict(total=2, items=[dict(responses=[dict(status='submitted')])]))
    require_complete(dict(total=1, items=[dict(responses=[dict(status='submitted')])]))
