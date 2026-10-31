import pytest
import tldr


@pytest.mark.parametrize('locale,expected', [('tr_TR.UTF-8', 'tr'), ('pt', 'pt_PT'),
                                             ('pt_BR.UTF-8', 'pt_BR'), ('zh_TW', 'zh_TW')])
def test_language_codes(locale, expected):
    assert tldr.get_language_code(locale) == expected


def test_language_priority(monkeypatch):
    monkeypatch.setenv('LANG', 'de_DE.UTF-8')
    monkeypatch.setenv('LANGUAGE', 'fr:de')
    monkeypatch.setenv('TLDR_LANGUAGE', 'pt_BR')
    assert tldr.get_language_list() == ['pt_BR', 'fr', 'de', 'en']
    monkeypatch.setenv('LANG', 'C')
    assert tldr.get_language_list() == ['pt_BR', 'en']
    monkeypatch.delenv('TLDR_LANGUAGE')
    assert tldr.get_language_list() == ['en']
