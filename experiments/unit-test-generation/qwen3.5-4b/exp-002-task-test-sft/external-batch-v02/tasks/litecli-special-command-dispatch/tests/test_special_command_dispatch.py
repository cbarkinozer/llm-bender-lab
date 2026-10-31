import pytest
from litecli.packages.special import main as special


def test_parse_verbosity_and_argument():
    assert special.parse_special_command('demo+  two words ') == ('demo', special.Verbosity.VERBOSE, 'two words')
    assert special.parse_special_command('demo-') == ('demo', special.Verbosity.SUCCINCT, '')
    assert special.parse_special_command('demo') == ('demo', special.Verbosity.NORMAL, '')


def test_dispatch_and_unknown(monkeypatch):
    monkeypatch.setattr(special, 'COMMANDS', {})
    calls = []
    def handler(**kwargs):
        calls.append(kwargs)
        return [('done',)]
    special.register_special_command(handler, 'demo', '', 'Demo')
    cursor = object()
    assert special.execute(cursor, 'DEMO+ value') == [('done',)]
    assert calls == [{'cur': cursor, 'arg': 'value', 'verbose': True}]
    with pytest.raises(special.CommandNotFound):
        special.execute(cursor, 'missing-command')
