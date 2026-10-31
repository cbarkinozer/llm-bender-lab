from pathlib import Path
import tldr


def test_cache_root_precedence(monkeypatch, tmp_path):
    xdg, home, fallback = (tmp_path / name for name in ('xdg', 'home', 'fallback'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(xdg))
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: fallback))
    assert tldr.get_cache_dir() == xdg / 'tldr'
    monkeypatch.delenv('XDG_CACHE_HOME')
    assert tldr.get_cache_dir() == home / '.cache' / 'tldr'
    monkeypatch.delenv('HOME')
    assert tldr.get_cache_dir() == fallback / '.cache' / 'tldr'


def test_language_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(tldr, 'get_cache_dir', lambda: tmp_path)
    for language in (None, 'en'):
        assert tldr.get_cache_file_path('git', 'linux', language) == tmp_path / 'pages/linux/git.md'
    assert tldr.get_cache_file_path('git', 'linux', 'tr') == tmp_path / 'pages.tr/linux/git.md'
