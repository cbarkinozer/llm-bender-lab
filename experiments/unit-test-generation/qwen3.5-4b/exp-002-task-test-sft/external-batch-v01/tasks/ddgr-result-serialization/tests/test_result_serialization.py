import json
from ddgr import Result


def test_plain_result_and_url_lookup():
    result = Result(3, 'caf\u00e9', 'https://example.test', 'summary')
    expected = {'title': 'caf\u00e9', 'url': 'https://example.test', 'abstract': 'summary'}
    assert result.jsonizable_object() == expected
    assert json.loads(json.dumps(result.jsonizable_object())) == expected
    assert result.urltable() == {'3': 'https://example.test'}


def test_optional_metadata():
    assert Result('4', 'Title', 'url', 'body', 'publisher').jsonizable_object() == {
        'title': 'Title', 'url': 'url', 'abstract': 'body', 'metadata': 'publisher'}
    assert 'metadata' not in Result(5, 'Title', 'url', 'body', '').jsonizable_object()
