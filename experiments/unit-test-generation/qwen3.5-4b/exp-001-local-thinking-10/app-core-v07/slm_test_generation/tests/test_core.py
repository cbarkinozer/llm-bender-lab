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
