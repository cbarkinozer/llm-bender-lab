"""Generic experiment preflight contracts, independent of Occam's 80/20 recipe."""
from unittest.mock import Mock
import pytest
from test_workflow import config, rows


@pytest.mark.parametrize('defect', ['missing-content','wrong-role','unknown-split'])
def test_malformed_data_fails_before_backend(tmp_path, defect):
    from experiment_workflow import run_experiment
    data=rows()
    if defect == 'missing-content':
        data[0]['messages'][1]['content']=' '
    elif defect == 'wrong-role':
        data[0]['messages'][1]['role']='user'
    else:
        data[0]['split']='unrecognized'
    trainer=Mock()
    with pytest.raises(ValueError):
        run_experiment(tmp_path,'bad',config(),data,trainer=trainer,evaluator=Mock())
    trainer.assert_not_called()
