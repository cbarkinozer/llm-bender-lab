## Decisions and unresolved questions

These are assistant-proposed design choices for this demo, not recorded human answers.

- Do not include old authored evaluation rows in training; test preprocessing with fresh fixtures.
- Keep a replaceable backend in the requested app; do not call actual GPU training from core tests.
- Preserve baseline/candidate generation settings and distinguish percentage points from relative percent.

Unresolved/nonessential choices:
- Real training backend selection remains open; the demo only fixes its callable boundary.

## Proposed interface agreement

Proposed `experiment_workflow.run_experiment(root,name,config,rows,trainer=...,evaluator=...)` is a complete orchestration boundary. No Occam-specific category count or 80/20 split is assumed.
- Config: model_revision,data_revision,code_revision strings, seed int, generation mapping (temperature,max_new_tokens). Credential fields api_key/token/password/secret are excluded from saved config, logs and results; external secret values are redacted from backend errors. Manifest secret filtering is limited to this declared top-level schema; arbitrary nested secrets require a future schema decision.
- Rows: `{id,split:"train"|"test",messages:[{role:"user",content},{role:"assistant",reasoning_content?,content}]}`. Both splits required; nonempty text; reject malformed roles, unknown split and normalized duplicate prompts before trainer invocation. This minimal conversation schema is an explicitly proposed demo choice, not a general conversational-data standard.
- Run IDs are simple directory names. Create root/name exclusively, rejecting existing run with FileExistsError; never overwrite previous artifacts. resolved.json holds effective nonsecret config and all revision identities/seed/settings. status.json states running/completed/failed. trainer(run_dir,resolved_config,training_rows) returns an existing adapter file inside run_dir; evaluator(model_or_adapter,heldout_rows,generation_settings) returns metric-name -> float or None. Call baseline then adapter with identical held-out rows and settings; no real training dependency imported in this workflow.
- Success returns `{status:"completed",comparison:{metric:{before,after,delta}}}` and writes summary.md, run.log, status.json. delta=after-before, None if either unavailable; zero is an actual zero. Failure returns `{status:"failed",error}`, retains sanitized run.log/status.json, and never writes a success summary.
Dependencies: Python standard library and pytest. Tests supply trainer/evaluator fakes; setup commands and connecting a real backend remain manual checks.

Declared application import inventory (checked against test AST):
- `experiment_workflow.run_experiment`

## Requirement-to-test map

R1: Reject malformed conversations and held-out overlap before training.
- `tests/test_core.py::test_malformed_data_fails_before_backend`
- `tests/test_workflow.py::test_invalid_preflight_never_invokes_trainer`

R2: Resolve and preserve effective config and identities.
- `tests/test_workflow.py::test_smoke_run_preserves_config_adapter_and_matched_evaluations`

R3: Keep runs isolated and preserve previous artifacts.
- `tests/test_workflow.py::test_run_directories_are_distinct_and_never_overwritten`

R4: Coordinate a smoke run and adapter artifact.
- `tests/test_workflow.py::test_smoke_run_preserves_config_adapter_and_matched_evaluations`

R5: Keep evidence when a run fails.
- `tests/test_workflow.py::test_failure_is_recorded_without_success_or_credential_leak`

R6: Compare matched baseline/candidate and omit credentials.
- `tests/test_workflow.py::test_smoke_run_preserves_config_adapter_and_matched_evaluations`
- `tests/test_workflow.py::test_failure_is_recorded_without_success_or_credential_leak`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2, M3, M4

## Complete test files

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

## Manual checks

M1: Real adapter loading and one GPU/CPU backend smoke require separate hardware validation.
M2: Inspect the summary for clear scope, limits and artifact recovery instructions.
M3: Check prepare/run/compare commands and real trainer integration separately; tests supply an offline backend only.
M4: Check .gitignore/publishing policy for credentials and large weights; backend persistence tests do not certify Git hygiene.
