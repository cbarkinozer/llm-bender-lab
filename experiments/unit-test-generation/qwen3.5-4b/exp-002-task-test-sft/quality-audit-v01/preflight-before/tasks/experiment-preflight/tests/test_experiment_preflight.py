import pytest


def config():
    return {'model_revision':'base-v1', 'data_revision':'data-v1', 'code_revision':'code-v1',
            'seed':7, 'generation':{'temperature':0, 'max_new_tokens':128}}


def rows():
    return [{'split':split, 'id':split, 'messages':[{'role':'user','content':prompt},
              {'role':'assistant','reasoning_content':'Add the quantities.', 'content':'5'}]}
            for split,prompt in [('train','Add 2 and 3'),('test','Add 1 and 4')]]


@pytest.fixture
def experiment_config(): return config()


@pytest.fixture
def experiment_rows(): return rows()


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


from unittest.mock import Mock
import pytest


def test_invalid_preflight_never_invokes_trainer(tmp_path, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    data = experiment_rows
    data[-1]['messages'][0]['content'] = data[0]['messages'][0]['content']
    train = Mock()
    with pytest.raises(ValueError):
        run_experiment(tmp_path, 'bad', experiment_config, data, trainer=train, evaluator=Mock())
    train.assert_not_called()
