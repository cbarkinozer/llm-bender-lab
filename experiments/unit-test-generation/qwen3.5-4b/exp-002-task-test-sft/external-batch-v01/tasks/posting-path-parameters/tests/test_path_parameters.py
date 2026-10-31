from posting.urls import extract_path_param_names, substitute_path_params


def test_placeholder_names_and_negative_controls():
    url = 'https://example.test/:user/::literal/:item/:user?q=:ignored#x:ignored'
    assert extract_path_param_names(url) == ['user', 'item']
    assert extract_path_param_names('https://example.test/plain?q=:name') == []


def test_substitution_scope_and_missing_values():
    url = 'https://example.test/:user/::literal/:missing?q=:user#x:user'
    assert substitute_path_params(url, {'user': 'alice', 'literal': 'wrong'}) == (
        'https://example.test/alice/:literal/:missing?q=:user#x:user')
