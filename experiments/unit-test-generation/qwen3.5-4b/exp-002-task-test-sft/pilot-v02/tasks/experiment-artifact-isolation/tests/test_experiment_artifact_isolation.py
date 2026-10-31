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


import pytest


def trainer(run_dir, resolved, train_rows):
    adapter = run_dir/'adapter.bin'
    adapter.write_bytes(b'fixture-adapter')
    return adapter


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
