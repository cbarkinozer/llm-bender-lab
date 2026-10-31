from posting.urls import extract_query_pairs, merge_url_query_into_params


def test_query_pairs_and_literal_dollars():
    assert extract_query_pairs('https://example.test/?a=1&a=&b=two+words') == [('a', '1'), ('a', ''), ('b', 'two words')]
    assert extract_query_pairs('https://example.test/?cost=%24x', escape_dollars=True) == [('cost', '$$x')]


def test_merge_by_occurrence_and_preserve_disabled_rows():
    params = [('a', '', False), ('a', 'override', True), ('tail', 'keep', False)]
    url, merged = merge_url_query_into_params('https://example.test/path?a=one&a=two&b=#frag', params)
    assert url == 'https://example.test/path#frag'
    assert merged == [('a', 'one', False), ('a', 'override', True), ('b', '', True), ('tail', 'keep', False)]
    assert params == [('a', '', False), ('a', 'override', True), ('tail', 'keep', False)]
