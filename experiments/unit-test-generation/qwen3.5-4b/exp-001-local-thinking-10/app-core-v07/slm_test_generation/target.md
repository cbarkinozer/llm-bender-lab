## Decisions and unresolved questions

Proposed decisions:

- All eligible task IDs form the success-rate denominator; missing observations remain visible.
- Mutation rates are killed/eligible and killed/valid, with unavailable values for zero denominators.
- Usefulness requires a successful suite and a reached weak or strong oracle; a strong but wrong assertion still fails.
- Trusted unit fixtures explicitly inject a local executor; untrusted generated outputs use the default bounded Docker executor.

Unresolved/nonessential choices:
- Semantic-correctness adjudication policy and final table layout remain open; UNKNOWN does not qualify as strong.

## Proposed interface agreement

Proposed public modules: `oracle_analysis` and `benchmark_workflow`.
- `OracleClass` enum: TRIVIAL=constant independent assertions, WEAK=SUT-derived coarse nullity/type/truthiness, STRONG=specific value/exception/state comparison, UNKNOWN=unresolved helper behavior. Here `assert True` is TRIVIAL; `result=sut(); assert result is not None` is WEAK; `assert sut()==42` is STRONG; `assert helper(result)` is UNKNOWN. "Unresolved" maps to UNKNOWN. Strength is independent of correctness.
- `classify_oracles(source,sut_names=())` -> list of sites exposing `.oracle_id` and `.oracle_class`. `instrument_oracles(source,sut_names=())` -> `(instrumented_source,sites)` preserving assertion behavior. A reached check appends JSONL `{oracle_id:string}` to the file named by ORACLE_EXECUTION_FILE. Declared code is trusted only in unit microfixtures; generated suites run in Docker.
- `gate_outcomes(suite_passed,sites,executed_ids)` returns exactly `{execution_success,executed_nontrivial_gate,executed_strong_gate}` booleans: suite success; success AND reached WEAK/STRONG; success AND reached STRONG, respectively. Merely classified/skipped/untaken checks do not count.
- `run_task(task,root=...,sut_source=...,timeout_seconds=...)` consumes task `{id,source,sut_names,context,dependency}`; creates root/id exclusively; writes exact generation.txt. Runs collected pytest in Docker, no network, bounded time/memory/processes, only task directory mounted. Use a pinned Python+pytest image. SUT fixture exports sut(). Returns `{task_id,context,dependency,outcome,returncode,stdout,stderr,useful_success,reached_oracles}`. outcome is passed/runtime_failure/collection_error/timeout; useful_success requires passed AND reached nontrivial oracle. All-skipped has outcome passed; no tests collected has collection_error; both have no reached_oracles and never useful_success. All-skipped has outcome passed but never useful_success. Infrastructure failure raises RuntimeError, not suite failure. Nonpositive timeout/unsafe task IDs raise ValueError. No inference/backend downloads or frozen benchmark writes.
- `summarize(eligible_ids=...,observations=...)` consumes observations `{task_id,useful_success}`; returns `{eligible,observed,missing,successful,success_rate}`; all eligible IDs in denominator; None rate when empty; unknown/duplicate IDs raise ValueError.
- `mutation_summary(eligible=...,valid=...,killed=...)` requires 0<=killed<=valid<=eligible; returns same counts plus unconditional=killed/eligible and conditional=killed/valid; zero denominators -> None; invalid counts -> ValueError.
- `save_manifest(path,dict)` / `load_manifest(path)` preserve task_ids,model_revision,data_revision,code_revision,seed,timeout_seconds,network_disabled,context,dependency as JSON. Table/command documentation and sandbox live isolation have dedicated manual/live checks.
Dependencies: Python, pytest and Docker with a configured pinned image.

- run_task also accepts executor=None. The default executor uses the configured Docker image. Trusted unit fixtures inject local_executor(run_directory, timeout_seconds); it executes supervisor.py locally and must write execution.json. It is not an isolation boundary for untrusted outputs. timeout_seconds bounds pytest only; Docker startup has a separate 15-second allowance. run_task instruments a copy, retaining unmodified generation.txt. reached_oracles is a sorted unique list of oracle_id strings.


Public imports:
- `benchmark_workflow.load_manifest`
- `benchmark_workflow.mutation_summary`
- `benchmark_workflow.run_task`
- `benchmark_workflow.save_manifest`
- `benchmark_workflow.summarize`
- `oracle_analysis.OracleClass`
- `oracle_analysis.classify_oracles`
- `oracle_analysis.gate_outcomes`
- `oracle_analysis.instrument_oracles`

## Requirement-to-test map

R1: Keep raw generations and distinct execution outcomes.
- `tests/test_core.py::test_pytest_execution_controls_reachability_and_success`
- `tests/test_workflow.py::test_runner_retains_raw_text_and_distinct_outcomes`
- `tests/test_workflow.py::test_passing_empty_or_skipped_suite_is_not_useful`
- `tests/test_workflow.py::test_valid_docstring_and_future_import_survive_instrumentation`

R2: Require a runtime-reached meaningful oracle for non-trivial success.
- `tests/test_core.py::test_uncalled_assertion_is_not_runtime_evidence`
- `tests/test_core.py::test_reached_strong_oracle_satisfies_gate`
- `tests/test_core.py::test_trivial_pass_is_not_meaningful_success`
- `tests/test_core.py::test_wrong_exact_assertion_is_strong_but_not_success`
- `tests/test_core.py::test_pytest_execution_controls_reachability_and_success`
- `tests/test_workflow.py::test_runner_retains_raw_text_and_distinct_outcomes`
- `tests/test_workflow.py::test_passing_empty_or_skipped_suite_is_not_useful`
- `tests/test_workflow.py::test_valid_docstring_and_future_import_survive_instrumentation`

R3: Keep oracle strength separate from correctness.
- `tests/test_core.py::test_oracle_strength_is_explicit`
- `tests/test_core.py::test_wrong_exact_assertion_is_strong_but_not_success`
- `tests/test_core.py::test_pytest_execution_controls_reachability_and_success`

R4: Use correct aggregation denominators and preserve missingness.
- `tests/test_workflow.py::test_aggregation_keeps_eligible_denominator_and_missingness`
- `tests/test_workflow.py::test_duplicate_observation_ids_are_rejected`

R5: Keep mutation denominators explicit.
- `tests/test_workflow.py::test_mutation_denominators_are_named_and_not_interchanged`

R6: Preserve reproducibility and sandbox restrictions.
- `tests/test_workflow.py::test_runner_retains_raw_text_and_distinct_outcomes`
- `tests/test_workflow.py::test_manifest_roundtrip`
- `tests/test_workflow.py::test_unsafe_task_id_never_writes_outside_root`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2, M3

## Complete test files

File: tests/conftest.py
```python
import os
import subprocess
import sys
import pytest

@pytest.fixture
def local_executor():
    # Trusted authored microfixtures only. Generated suites use the Docker default.
    def execute(run_directory, timeout_seconds):
        env=dict(os.environ, SUITE_TIMEOUT=str(timeout_seconds),
                 ORACLE_EXECUTION_FILE=str(run_directory/'events.jsonl'),
                 PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
        env.pop('PYTEST_ADDOPTS',None)
        subprocess.run([sys.executable,'supervisor.py'], cwd=run_directory, env=env,
                       check=True, capture_output=True, text=True, timeout=timeout_seconds+10)
    return execute
```

File: tests/test_core.py
```python
'Acceptance checks for observable application behavior.'
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
    assert (gates['execution_success'], gates['executed_nontrivial_gate'], gates['executed_strong_gate']) == expected
```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
import json
import pytest


def task(identifier, source):
    return {'id': identifier, 'source': source, 'sut_names': ['sut'], 'context': 'B', 'dependency': 'L1'}


@pytest.mark.parametrize('source,outcome', [
    ('def test_ok():\n    assert sut() == 42', 'passed'),
    ('def test_wrong():\n    assert sut() == 43', 'runtime_failure'),
    ('def test_(:', 'collection_error'),
    ('def test_wait():\n    while True: pass', 'timeout')])
def test_runner_retains_raw_text_and_distinct_outcomes(tmp_path, source, outcome, local_executor):
    from benchmark_workflow import run_task
    row = task('fresh', source)
    result = run_task(row, root=tmp_path, sut_source='def sut(): return 42', timeout_seconds=.5 if outcome=='timeout' else 5, executor=local_executor)
    assert result['outcome'] == outcome
    assert result['task_id'] == 'fresh'
    assert result['context'] == 'B'
    assert result['dependency'] == 'L1'
    assert (tmp_path/'fresh'/'generation.txt').read_text() == source
    assert result['useful_success'] is (outcome == 'passed')


@pytest.mark.parametrize('source,outcome', [('import pytest\n@pytest.mark.skip(reason="fixture")\ndef test_skip():\n    assert sut() == 42', 'passed'), ('# no tests', 'collection_error')])
def test_passing_empty_or_skipped_suite_is_not_useful(tmp_path, source, outcome, local_executor):
    from benchmark_workflow import run_task
    row = task('skipped', source)
    result = run_task(row, root=tmp_path, sut_source='def sut(): return 42', timeout_seconds=5, executor=local_executor)
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


def test_valid_docstring_and_future_import_survive_instrumentation(tmp_path, local_executor):
    from benchmark_workflow import run_task
    source = ('"""Generated checks."""\nfrom __future__ import annotations\n'
              'def test_value():\n    assert __doc__ == "Generated checks."\n    assert sut() == 42\n')
    compile(source, '<valid-original-module>', 'exec')
    result = run_task(task('header',source), root=tmp_path,
                      sut_source='def sut(): return 42', timeout_seconds=5, executor=local_executor)
    assert result['outcome'] == 'passed'
    assert result['useful_success'] is True
    assert (tmp_path/'header'/'generation.txt').read_text() == source

def test_unsafe_task_id_never_writes_outside_root(tmp_path, local_executor):
    from benchmark_workflow import run_task
    root=tmp_path/'runs'
    with pytest.raises(ValueError):
        run_task(task('../escape','def test_ok(): pass'),root=root,
                 sut_source='def sut(): return 42',timeout_seconds=5,executor=local_executor)
    assert not root.exists()
    assert not (tmp_path/'escape').exists()

def test_duplicate_observation_ids_are_rejected():
    from benchmark_workflow import summarize
    observation={'task_id':'a','useful_success':True}
    with pytest.raises(ValueError):
        summarize(eligible_ids=['a'], observations=[observation, observation])

```

## Manual checks

M1: Reproduce a small report from saved raw records and inspect table labels.
M2: Probe the configured execution environment for actual network denial and process/memory limits.
M3: Run documented fixture commands; verify they launch no inference and preserve the frozen benchmark.
