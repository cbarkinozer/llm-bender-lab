import os
from datetime import datetime
import tldr


def test_cache_age_boundary_and_missing(monkeypatch, tmp_path):
    now = datetime(2026, 1, 15, 12)
    class Clock(datetime):
        @classmethod
        def now(cls):
            return now
    cache = tmp_path / 'git.md'
    monkeypatch.setattr(tldr, 'datetime', Clock)
    monkeypatch.setattr(tldr, 'MAX_CACHE_AGE', 24)
    monkeypatch.setattr(tldr, 'get_cache_file_path', lambda *args: cache)
    assert tldr.have_recent_cache('git', 'linux', 'en') is False
    cache.write_bytes(b'page')
    for hours, expected in [(1, True), (24, True), (25, False)]:
        timestamp = now.timestamp() - hours * 3600
        os.utime(cache, (timestamp, timestamp))
        assert tldr.have_recent_cache('git', 'linux', 'en') is expected
