import pytest
import tldr


@pytest.mark.parametrize('language,suffix', [(None, ''), ('en', ''), ('tr', '.tr')])
def test_page_url_language(monkeypatch, language, suffix):
    monkeypatch.setattr(tldr, 'PAGES_SOURCE_LOCATION', 'https://pages.example/pages')
    assert tldr.get_page_url('git status', 'linux', None, language) == (
        'https://pages.example/pages' + suffix + '/linux/git%20status.md')


def test_custom_root_and_unicode():
    assert tldr.get_page_url('caf\u00e9', 'common', 'https://offline.example/docs', 'fr') == (
        'https://offline.example/docs.fr/common/caf%C3%A9.md')
