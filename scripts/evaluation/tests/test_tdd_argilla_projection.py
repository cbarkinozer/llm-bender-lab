import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from publish_tdd_threeway_argilla import payload


def test_review_projection_excludes_identity_scores_and_saved_judgments():
    item=dict(requirement='Requirement',candidates={'X':'assert True','Y':'assert False','Z':'pass'},
              model_identity='base',execution='all fail',judgment={'ranking':'X'})
    fields=payload(item,True)
    assert set(fields)=={'requirement','candidate_x','candidate_y','candidate_z'}
    assert fields['candidate_x']=='```python\nassert True\n```'
    assert 'model_identity' not in str(fields) and 'all fail' not in str(fields)


def test_unknown_labels_or_reasoning_fail_closed():
    with pytest.raises(ValueError):payload(dict(requirement='R',candidates={'base':'answer'}),True)
    with pytest.raises(ValueError):payload(dict(requirement='R',candidates={'X':'secret</think>','Y':'b','Z':'c'}),True)
