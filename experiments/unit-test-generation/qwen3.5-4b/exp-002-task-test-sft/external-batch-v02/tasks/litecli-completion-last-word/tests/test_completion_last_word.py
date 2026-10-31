import pytest
from litecli.packages.parseutils import last_word


@pytest.mark.parametrize('text,expected', [('', ''), ('abc ', ''), ('abc\t', ''),
                                           ('select user_id', 'user_id'), ('select $name', 'name')])
def test_default_tokens(text, expected):
    assert last_word(text) == expected


def test_punctuation_mode():
    assert last_word('select $name', include='most_punctuations') == '$name'
    assert last_word('table.column', include='most_punctuations') == 'column'
