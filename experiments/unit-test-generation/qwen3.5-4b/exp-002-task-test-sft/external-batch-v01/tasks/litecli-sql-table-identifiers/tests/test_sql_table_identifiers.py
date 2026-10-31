from litecli.packages.parseutils import extract_tables


def test_empty_and_columns_only():
    assert extract_tables('') == []
    assert extract_tables('SELECT 1 AS answer') == []


def test_qualified_join_and_aliases():
    assert extract_tables('SELECT u.id FROM main.users u JOIN orders o ON u.id=o.user_id') == [
        ('main', 'users', 'u'), (None, 'orders', 'o')]


def test_nested_select():
    assert extract_tables('SELECT * FROM (SELECT id FROM users) nested') == [(None, 'users', None)]
