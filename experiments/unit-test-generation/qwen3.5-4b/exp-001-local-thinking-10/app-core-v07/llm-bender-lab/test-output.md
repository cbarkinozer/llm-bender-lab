File: tests/conftest.py
```python
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
```

File: tests/test_core.py
```python
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
```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
import json
from unittest.mock import Mock
import pytest
def trainer(run_dir, resolved, train_rows):
    adapter = run_dir/'adapter.bin'
    adapter.write_bytes(b'fixture-adapter')
    return adapter


def test_smoke_run_preserves_config_adapter_and_matched_evaluations(tmp_path, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    seen = []
    def evaluate(model, heldout, settings):
        seen.append((model, heldout, settings.copy()))
        return {'accuracy':.5 if model == 'base-v1' else .75, 'other':None}
    trained = []
    def train(run_dir, resolved, train_rows):
        trained.extend(train_rows)
        return trainer(run_dir, resolved, train_rows)
    result = run_experiment(tmp_path, 'one', experiment_config, experiment_rows, trainer=train, evaluator=evaluate)
    run = tmp_path/'one'
    assert result['status'] == 'completed'
    assert (run/'adapter.bin').read_bytes() == b'fixture-adapter'
    assert json.loads((run/'resolved.json').read_text()) == experiment_config
    assert trained == [experiment_rows[0]]
    assert seen[0][1] == seen[1][1] == [experiment_rows[1]]
    assert seen[0][0] == experiment_config['model_revision']
    assert seen[1][0] == str(run/'adapter.bin')
    assert json.loads((run/'status.json').read_text())['status'] == 'completed'
    assert seen[0][1:] == seen[1][1:]
    assert seen[0][2] == experiment_config['generation']
    assert result['comparison'] == {'accuracy':{'before':.5,'after':.75,'delta':.25},
                                     'other':{'before':None,'after':None,'delta':None}}
    assert 'accuracy' in (run/'summary.md').read_text()


def test_run_directories_are_distinct_and_never_overwritten(tmp_path, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    evaluate = lambda *args: {'accuracy':0.0}
    run_experiment(tmp_path, 'one', experiment_config, experiment_rows, trainer=trainer, evaluator=evaluate)
    before = {p.name:p.read_bytes() for p in (tmp_path/'one').iterdir() if p.is_file()}
    with pytest.raises(FileExistsError):
        run_experiment(tmp_path, 'one', experiment_config, experiment_rows, trainer=trainer, evaluator=evaluate)
    result = run_experiment(tmp_path, 'two', experiment_config, experiment_rows, trainer=trainer, evaluator=evaluate)
    assert result['comparison']['accuracy'] == {'before':0.0, 'after':0.0, 'delta':0.0}
    assert {p.name:p.read_bytes() for p in (tmp_path/'one').iterdir() if p.is_file()} == before
    assert (tmp_path/'two'/'adapter.bin').is_file()


def test_invalid_preflight_never_invokes_trainer(tmp_path, experiment_config, experiment_rows):
    from experiment_workflow import run_experiment
    data = experiment_rows
    data[-1]['messages'][0]['content'] = data[0]['messages'][0]['content']
    train = Mock()
    with pytest.raises(ValueError):
        run_experiment(tmp_path, 'bad', experiment_config, data, trainer=train, evaluator=Mock())
    train.assert_not_called()


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
```
