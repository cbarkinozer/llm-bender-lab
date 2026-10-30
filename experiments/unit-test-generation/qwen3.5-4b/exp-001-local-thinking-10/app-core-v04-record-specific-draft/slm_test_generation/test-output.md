File: tests/conftest.py
```python
"""Only these authored fixtures may run outside the isolated executor."""
from functools import partial
import pytest


@pytest.fixture
def local_runner():
    from benchmark_workflow import LocalPytestExecutor, run_task
    return partial(run_task, executor=LocalPytestExecutor())
```

File: tests/test_core.py
```python
"""Oracle classification, instrumentation and runtime gates."""
import json
import pytest
from oracle_analysis import OracleClass, classify_oracles, instrument_oracles, gate_outcomes


@pytest.mark.parametrize('source,kind', [('assert True', OracleClass.TRIVIAL), ('result = sut()\nassert result is not None', OracleClass.WEAK), ('result = sut()\nassert result == 42', OracleClass.STRONG), ('result = sut()\nassert helper(result)', OracleClass.UNKNOWN)])
def test_oracle_strength_is_explicit(source, kind):
    sites = classify_oracles(source, sut_names={'sut'})
    assert [s.oracle_class for s in sites] == [kind]


def reached(path):
    return {json.loads(line)['oracle_id'] for line in path.read_text().splitlines()} if path.exists() else set()


def run_fixture(source, tmp_path, monkeypatch):
    target = tmp_path / 'events.jsonl'
    monkeypatch.setenv('ORACLE_EXECUTION_FILE', str(target))
    instrumented, sites = instrument_oracles(source, sut_names={'sut'})
    namespace = {'sut': lambda: 42}
    exec(compile(instrumented, '<trusted-audit-fixture>', 'exec'), namespace)
    return namespace, sites, target


def test_uncalled_assertion_is_not_runtime_evidence(tmp_path, monkeypatch):
    _, sites, target = run_fixture('def test_never_called():\n    assert sut() == 42\n', tmp_path, monkeypatch)
    assert gate_outcomes(True, sites, reached(target)) == {'execution_success': True, 'executed_nontrivial_gate': False, 'executed_strong_gate': False}


def test_reached_strong_oracle_satisfies_gate(tmp_path, monkeypatch):
    namespace, sites, target = run_fixture('def test_value():\n    assert sut() == 42\n', tmp_path, monkeypatch)
    namespace['test_value']()
    assert gate_outcomes(True, sites, reached(target)) == {'execution_success': True, 'executed_nontrivial_gate': True, 'executed_strong_gate': True}


def test_trivial_pass_is_not_meaningful_success(tmp_path, monkeypatch):
    namespace, sites, target = run_fixture('def test_constant():\n    assert True\n', tmp_path, monkeypatch)
    namespace['test_constant']()
    assert gate_outcomes(True, sites, reached(target))['executed_nontrivial_gate'] is False


def test_wrong_exact_assertion_is_strong_but_not_success(tmp_path, monkeypatch):
    namespace, sites, target = run_fixture('def test_wrong():\n    assert sut() == 43\n', tmp_path, monkeypatch)
    with pytest.raises(AssertionError):
        namespace['test_wrong']()
    assert sites[0].oracle_class is OracleClass.STRONG
    assert gate_outcomes(False, sites, reached(target)) == {'execution_success': False, 'executed_nontrivial_gate': False, 'executed_strong_gate': False}


@pytest.mark.parametrize('body,expected', [
    ('@pytest.mark.skip(reason="fixture")\ndef test_case():\n    assert sut() == 42', (True,False,False)),
    ('def test_case():\n    if sut() == 0:\n        assert sut() == 42', (True,False,False)),
    ('def test_case():\n    assert sut() == 43', (False,False,False)),
    ('def test_case():\n    assert sut() == 42', (True,True,True))])
def test_pytest_execution_controls_reachability_and_success(tmp_path, monkeypatch, body, expected):
    import os
    import subprocess
    import sys
    source = 'import pytest\ndef sut(): return 42\n' + body + '\n'
    target = tmp_path/'events.jsonl'
    instrumented, sites = instrument_oracles(source, sut_names={'sut'})
    (tmp_path/'test_fixture.py').write_text(instrumented)
    env = dict(os.environ, ORACLE_EXECUTION_FILE=str(target), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    env.pop('PYTEST_ADDOPTS', None)
    result = subprocess.run([sys.executable,'-m','pytest','-q',str(tmp_path/'test_fixture.py')],
                            cwd=tmp_path,env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode in (0,1), result.stdout + result.stderr
    gates = gate_outcomes(result.returncode == 0, sites, reached(target))
    assert (gates['execution_success'], gates['executed_nontrivial_gate'],
            gates['executed_strong_gate']) == expected
```

File: tests/test_workflow.py
```python
"""Suite execution, aggregation and reproducibility contracts."""
import json
from unittest.mock import Mock
import pytest


def task(identifier, source):
    return {'id': identifier, 'source': source, 'sut_names': ['sut'], 'context': 'B', 'dependency': 'L1'}


@pytest.mark.parametrize('source,outcome', [
    ('def test_ok():\n    assert sut() == 42', 'passed'),
    ('def test_wrong():\n    assert sut() == 43', 'runtime_failure'),
    ('def test_(:', 'collection_error')])
def test_runner_retains_raw_text_and_distinct_outcomes(tmp_path, local_runner, source, outcome):
    row = task('fresh', source)
    result = local_runner(row, root=tmp_path, sut_source='def sut(): return 42', timeout_seconds=2)
    assert result['backend'] == 'local-subprocess'
    assert result['outcome'] == outcome
    assert result['task_id'] == 'fresh'
    assert result['context'] == 'B'
    assert result['dependency'] == 'L1'
    assert (tmp_path/'fresh'/'generation.txt').read_text() == source
    assert result['useful_success'] is (outcome == 'passed')


@pytest.mark.parametrize('source,outcome', [
    ('import pytest\n@pytest.mark.skip(reason="fixture")\ndef test_skip():\n    assert sut() == 42', 'passed'),
    ('', 'collection_error'),
    ('def test_no_oracle(): pass', 'passed')])
def test_skipped_empty_and_no_oracle_suites_are_not_useful(tmp_path, local_runner, source, outcome):
    result = local_runner(task('no-oracle',source), root=tmp_path,
                          sut_source='def sut(): return 42', timeout_seconds=2)
    assert result['outcome'] == outcome
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


def test_valid_docstring_and_future_import_survive_instrumentation(tmp_path, local_runner):
    source = ('"""Generated checks."""\nfrom __future__ import annotations\n'
              'def test_value():\n    assert __doc__ == "Generated checks."\n    assert sut() == 42\n')
    compile(source, '<valid-original-module>', 'exec')
    result = local_runner(task('header',source), root=tmp_path,
                      sut_source='def sut(): return 42', timeout_seconds=2)
    assert result['outcome'] == 'passed'
    assert result['useful_success'] is True
    assert (tmp_path/'header'/'generation.txt').read_text() == source


def test_runner_preserves_timeout_report_and_forwards_budget(tmp_path):
    from benchmark_workflow import run_task
    executor=Mock(return_value={'outcome':'timeout','returncode':None,
        'stdout':'','stderr':'deadline reached','backend':'timeout-fixture'})
    result=run_task(task('deadline','def test_case(): pass'),root=tmp_path,
                    sut_source='def sut(): return 42',timeout_seconds=2,executor=executor)
    executor.assert_called_once_with(tmp_path/'deadline',2)
    assert (result['outcome'],result['returncode'],result['useful_success']) == ('timeout',None,False)
    assert result['stderr'] == 'deadline reached'


@pytest.mark.parametrize('identifier', ['../x','..','.'])
def test_unsafe_task_ids_fail_before_writes_or_execution(tmp_path, identifier):
    from benchmark_workflow import run_task
    sentinel=tmp_path/'x'
    sentinel.write_text('preserved')
    executor=Mock()
    with pytest.raises(ValueError):
        run_task(task(identifier,''),root=tmp_path/'runs',sut_source='',
                 timeout_seconds=2,executor=executor)
    executor.assert_not_called()
    assert sentinel.read_text() == 'preserved'
    assert set(tmp_path.iterdir()) == {sentinel}


@pytest.mark.parametrize('seconds', [0,-1])
def test_nonpositive_timeout_fails_before_writes(tmp_path, seconds):
    from benchmark_workflow import run_task
    executor=Mock()
    with pytest.raises(ValueError):
        run_task(task('invalid',''),root=tmp_path/'runs',sut_source='',
                 timeout_seconds=seconds,executor=executor)
    executor.assert_not_called()
    assert not (tmp_path/'runs').exists()


def test_duplicate_eligible_and_observed_ids_are_rejected():
    from benchmark_workflow import summarize
    with pytest.raises(ValueError):
        summarize(eligible_ids=['a','a'],observations=[])
    with pytest.raises(ValueError):
        summarize(eligible_ids=['a'],observations=[
            {'task_id':'a','useful_success':True},{'task_id':'a','useful_success':False}])
```
