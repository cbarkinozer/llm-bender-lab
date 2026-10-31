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
