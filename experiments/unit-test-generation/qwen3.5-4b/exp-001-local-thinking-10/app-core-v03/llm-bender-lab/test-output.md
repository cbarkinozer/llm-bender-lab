File: tests/test_core.py
```python
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
```

File: tests/test_workflow.py
```python
"""Proposed orchestration acceptance tests; all training/evaluation is fake."""
import json
from unittest.mock import Mock
import pytest


def config():
    return {'model_revision':'base-v1', 'data_revision':'data-v1', 'code_revision':'code-v1',
            'seed':7, 'generation':{'temperature':0, 'max_new_tokens':128}}


def rows():
    return [{'split':split, 'id':split, 'messages':[{'role':'user','content':prompt},
              {'role':'assistant','reasoning_content':'Add the quantities.', 'content':'5'}]}
            for split,prompt in [('train','Add 2 and 3'),('test','Add 1 and 4')]]


def trainer(run_dir, resolved, train_rows):
    adapter = run_dir/'adapter.bin'
    adapter.write_bytes(b'fixture-adapter')
    return adapter


def test_smoke_run_preserves_config_adapter_and_matched_evaluations(tmp_path):
    from experiment_workflow import run_experiment
    seen = []
    def evaluate(model, heldout, settings):
        seen.append((model, heldout, settings.copy()))
        return {'accuracy':.5 if model == 'base-v1' else .75, 'other':None}
    result = run_experiment(tmp_path, 'one', config(), rows(), trainer=trainer, evaluator=evaluate)
    run = tmp_path/'one'
    assert result['status'] == 'completed'
    assert (run/'adapter.bin').read_bytes() == b'fixture-adapter'
    assert json.loads((run/'resolved.json').read_text()) == config()
    assert seen[0][1:] == seen[1][1:]
    assert seen[0][2] == config()['generation']
    assert result['comparison'] == {'accuracy':{'before':.5,'after':.75,'delta':.25},
                                     'other':{'before':None,'after':None,'delta':None}}
    assert 'accuracy' in (run/'summary.md').read_text()


def test_run_directories_are_distinct_and_never_overwritten(tmp_path):
    from experiment_workflow import run_experiment
    evaluate = lambda *args: {'accuracy':0.0}
    run_experiment(tmp_path, 'one', config(), rows(), trainer=trainer, evaluator=evaluate)
    before = {p.name:p.read_bytes() for p in (tmp_path/'one').iterdir() if p.is_file()}
    with pytest.raises(FileExistsError):
        run_experiment(tmp_path, 'one', config(), rows(), trainer=trainer, evaluator=evaluate)
    run_experiment(tmp_path, 'two', config(), rows(), trainer=trainer, evaluator=evaluate)
    assert {p.name:p.read_bytes() for p in (tmp_path/'one').iterdir() if p.is_file()} == before
    assert (tmp_path/'two'/'adapter.bin').is_file()


def test_invalid_preflight_never_invokes_trainer(tmp_path):
    from experiment_workflow import run_experiment
    data = rows()
    data[-1]['messages'][0]['content'] = data[0]['messages'][0]['content']
    train = Mock()
    with pytest.raises(ValueError):
        run_experiment(tmp_path, 'bad', config(), data, trainer=train, evaluator=Mock())
    train.assert_not_called()


def test_failure_is_recorded_without_success_or_credential_leak(tmp_path):
    from experiment_workflow import run_experiment
    cfg = config() | {'api_key':'fixture-secret'}
    train = Mock(side_effect=RuntimeError('backend failed fixture-secret'))
    result = run_experiment(tmp_path, 'failure', cfg, rows(), trainer=train, evaluator=Mock())
    assert result['status'] == 'failed'
    assert json.loads((tmp_path/'failure'/'status.json').read_text())['status'] == 'failed'
    assert 'backend failed' in (tmp_path/'failure'/'run.log').read_text()
    assert 'fixture-secret' not in ''.join(p.read_text() for p in (tmp_path/'failure').iterdir() if p.is_file())
    assert not (tmp_path/'failure'/'summary.md').exists()
```
