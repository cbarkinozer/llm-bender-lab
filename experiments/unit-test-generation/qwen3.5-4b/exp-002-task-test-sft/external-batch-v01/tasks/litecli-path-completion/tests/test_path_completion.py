import os
from litecli.packages.filepaths import parse_path, complete_path, suggest_path


def test_path_parsing_and_matching():
    path = os.path.join('folder', 'draft')
    assert parse_path(path) == ('folder', 'draft', -5)
    assert parse_path('') == ('', '', 0)
    assert complete_path('draft.txt', 'dra') == 'draft.txt'
    assert complete_path('draft.txt', 'other') is None
    assert complete_path('draft.txt', '~') == os.path.join('~', 'draft.txt')


def test_directory_and_partial_path(tmp_path):
    (tmp_path / 'alpha.txt').write_text('a', encoding='utf-8')
    (tmp_path / 'beta').mkdir()
    assert set(suggest_path(str(tmp_path))) == {'alpha.txt', 'beta'}
    assert set(suggest_path(str(tmp_path / 'alp'))) == {'alpha.txt', 'beta'}
