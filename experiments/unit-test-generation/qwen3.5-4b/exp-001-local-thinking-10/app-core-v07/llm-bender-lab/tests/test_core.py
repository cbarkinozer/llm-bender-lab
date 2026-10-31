'Acceptance checks for observable application behavior.'
from unittest.mock import Mock
import pytest


@pytest.mark.parametrize('defect', ['missing-content','wrong-role','unknown-split'])
def test_malformed_data_fails_before_backend(tmp_path, defect, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    data=experiment_rows
    if defect == 'missing-content':
        data[0]['messages'][1]['content']=' '
    elif defect == 'wrong-role':
        data[0]['messages'][1]['role']='user'
    else:
        data[0]['split']='unrecognized'
    trainer=Mock()
    with pytest.raises(ValueError):
        run_experiment(tmp_path,'bad',experiment_config,data,trainer=trainer,evaluator=Mock())
    trainer.assert_not_called()
