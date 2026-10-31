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


import json
from unittest.mock import Mock


def test_failure_is_recorded_without_success_or_credential_leak(tmp_path, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    cfg = experiment_config | {'api_key':'fixture-secret'}
    train = Mock(side_effect=RuntimeError('backend failed fixture-secret'))
    result = run_experiment(tmp_path, 'failure', cfg, experiment_rows, trainer=train, evaluator=Mock())
    assert result['status'] == 'failed'
    assert 'fixture-secret' not in result['error']
    assert json.loads((tmp_path/'failure'/'status.json').read_text())['status'] == 'failed'
    assert 'backend failed' in (tmp_path/'failure'/'run.log').read_text()
    assert 'fixture-secret' not in ''.join(p.read_text() for p in (tmp_path/'failure').iterdir() if p.is_file())
    assert not (tmp_path/'failure'/'summary.md').exists()
