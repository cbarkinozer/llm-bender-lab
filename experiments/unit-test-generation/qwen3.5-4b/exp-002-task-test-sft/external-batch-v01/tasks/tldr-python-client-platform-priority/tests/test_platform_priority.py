import pytest
import tldr


@pytest.mark.parametrize('system,expected', [('darwin', 'osx'), ('win32', 'windows'),
                                             ('linux2', 'linux'), ('unknown-os', 'linux')])
def test_platform_mapping(monkeypatch, system, expected):
    monkeypatch.setattr(tldr.sys, 'platform', system)
    assert tldr.get_platform() == expected


def test_active_platform_first(monkeypatch):
    monkeypatch.setattr(tldr, 'get_platform', lambda: 'windows')
    platforms = tldr.get_platform_list()
    assert platforms[0] == 'windows'
    assert len(platforms) == len(set(platforms))
    assert set(platforms) == {'common', 'android', 'osx', 'freebsd', 'linux', 'netbsd', 'openbsd', 'sunos', 'windows'}
