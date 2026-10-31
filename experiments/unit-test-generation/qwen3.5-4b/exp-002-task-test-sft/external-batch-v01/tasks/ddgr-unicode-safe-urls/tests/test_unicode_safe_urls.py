from ddgr import make_safe_url


def test_ascii_url_unchanged():
    url = 'https://example.test:8443/path?q=one&x=2#part'
    assert make_safe_url(url) == url


def test_unicode_domain_path_and_query():
    assert make_safe_url('https://m\u00fcnich.example/caf\u00e9?q=two words&x=\u00e7#r\u00e9sum\u00e9') == (
        'https://xn--mnich-kva.example/caf%C3%A9?q=two%20words&x=%C3%A7#r%C3%A9sum%C3%A9')


def test_credentials_and_port():
    assert make_safe_url('https://user name:p\u00e4ss@example.test:8443/a b') == (
        'https://user%20name:p%C3%A4ss@example.test:8443/a%20b')
