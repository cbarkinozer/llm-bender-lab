"""Proposed pipeline boundary; fixtures never use the frozen benchmark."""
import json
import pytest


def task(identifier, source):
    return {'id': identifier, 'source': source, 'sut_names': ['sut'], 'context': 'B', 'dependency': 'L1'}


@pytest.mark.parametrize('source,outcome', [
    ('def test_ok():\n    assert sut() == 42', 'passed'),
    ('def test_wrong():\n    assert sut() == 43', 'runtime_failure'),
    ('def test_(:', 'collection_error'),
    ('def test_wait():\n    while True: pass', 'timeout')])
def test_runner_retains_raw_text_and_distinct_outcomes(tmp_path, source, outcome):
    from benchmark_workflow import run_task
    row = task('fresh', source)
    result = run_task(row, root=tmp_path, sut_source='def sut(): return 42', timeout_seconds=0.5)
    assert result['outcome'] == outcome
    assert result['task_id'] == 'fresh'
    assert result['context'] == 'B'
    assert result['dependency'] == 'L1'
    assert (tmp_path/'fresh'/'generation.txt').read_text() == source
    assert result['useful_success'] is (outcome == 'passed')


def test_passing_empty_or_skipped_suite_is_not_useful(tmp_path):
    from benchmark_workflow import run_task
    row = task('skipped', 'import pytest\n@pytest.mark.skip(reason="fixture")\ndef test_skip():\n    assert sut() == 42')
    result = run_task(row, root=tmp_path, sut_source='def sut(): return 42', timeout_seconds=1)
    assert result['useful_success'] is False
    assert result['reached_oracles'] == []


def test_aggregation_keeps_eligible_denominator_and_missingness():
    from benchmark_workflow import summarize
    result = summarize(eligible_ids=['a','b','c','d'], observations=[
        {'task_id':'a','useful_success':True}, {'task_id':'b','useful_success':False}])
    assert result == {'eligible':4, 'observed':2, 'missing':2, 'successful':1,
                      'success_rate':0.25}
    assert summarize(eligible_ids=[], observations=[])['success_rate'] is None
    with pytest.raises(ValueError):
        summarize(eligible_ids=['a'], observations=[{'task_id':'outside','useful_success':True}])


def test_mutation_denominators_are_named_and_not_interchanged():
    from benchmark_workflow import mutation_summary
    assert mutation_summary(eligible=4, valid=2, killed=1) == {
        'unconditional':0.25, 'conditional':0.5, 'eligible':4, 'valid':2, 'killed':1}
    assert mutation_summary(eligible=0, valid=0, killed=0) == {
        'unconditional':None, 'conditional':None, 'eligible':0, 'valid':0, 'killed':0}
    with pytest.raises(ValueError):
        mutation_summary(eligible=2, valid=1, killed=2)


def test_manifest_roundtrip(tmp_path):
    from benchmark_workflow import save_manifest, load_manifest
    manifest = {'task_ids':['fresh'], 'model_revision':'m1', 'data_revision':'d1',
                'code_revision':'c1', 'seed':7, 'timeout_seconds':1,
                'network_disabled':True, 'context':'B', 'dependency':'L1'}
    path = tmp_path/'manifest.json'
    save_manifest(path, manifest)
    assert load_manifest(path) == manifest
    assert json.loads(path.read_text()) == manifest


def test_valid_docstring_and_future_import_survive_instrumentation(tmp_path):
    from benchmark_workflow import run_task
    source = ('"""Generated checks."""\nfrom __future__ import annotations\n'
              'def test_value():\n    assert __doc__ == "Generated checks."\n    assert sut() == 42\n')
    compile(source, '<valid-original-module>', 'exec')
    result = run_task(task('header',source), root=tmp_path,
                      sut_source='def sut(): return 42', timeout_seconds=1)
    assert result['outcome'] == 'passed'
    assert result['useful_success'] is True
    assert (tmp_path/'header'/'generation.txt').read_text() == source
