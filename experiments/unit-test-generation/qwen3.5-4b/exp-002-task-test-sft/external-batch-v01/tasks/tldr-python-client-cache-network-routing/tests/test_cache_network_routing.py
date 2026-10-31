from io import BytesIO
import pytest
import tldr


def test_fresh_cache_avoids_network(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: True)
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: b'cached\npage')
    def unexpected(*args, **kwargs):
        pytest.fail('Fresh cache must avoid network')
    monkeypatch.setattr(tldr, 'urlopen', unexpected)
    assert tldr.get_page_for_platform('git', 'linux', None, 'en') == [b'cached', b'page']


def test_download_then_cache_and_failure_fallback(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: False)
    writes, requests = [], []
    def download(request, **kwargs):
        requests.append((request.full_url, kwargs['timeout']))
        return BytesIO(b'fresh\npage')
    monkeypatch.setattr(tldr, 'urlopen', download)
    monkeypatch.setattr(tldr, 'store_page_to_cache', lambda *args: writes.append(args))
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: b'stale')
    assert tldr.get_page_for_platform('git', 'linux', 'https://pages.example', 'en') == [b'fresh', b'page']
    assert requests == [('https://pages.example/linux/git.md', 10)]
    assert writes == [(b'fresh\npage', 'git', 'linux', 'en')]
    def failed(*args, **kwargs):
        raise OSError('offline')
    monkeypatch.setattr(tldr, 'urlopen', failed)
    assert tldr.get_page_for_platform('git', 'linux', None, 'en') == [b'stale']
    assert len(writes) == 1
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: None)
    with pytest.raises(OSError, match='offline'):
        tldr.get_page_for_platform('git', 'linux', None, 'en')


def test_cache_only_miss(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: False)
    def unexpected(*args, **kwargs):
        pytest.fail('Cache-only mode must avoid network')
    monkeypatch.setattr(tldr, 'urlopen', unexpected)
    with pytest.raises(tldr.CacheNotExist):
        tldr.get_page_for_platform('git', 'linux', None, 'en', only_use_cache=True)
