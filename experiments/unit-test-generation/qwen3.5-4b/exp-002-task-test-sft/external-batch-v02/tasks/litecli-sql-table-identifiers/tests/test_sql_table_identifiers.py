from litecli.packages.parseutils import extract_tables


def test_empty_and_columns_only():
    assert extract_tables('') == []
    assert extract_tables('SELECT 1 AS answer') == []


def test_qualified_join_and_aliases():
    assert extract_tables('SELECT u.id FROM main.users u JOIN orders o ON u.id=o.user_id') == [
        ('main', 'users', 'u'), (None, 'orders', 'o')]


def test_insert_target_excludes_columns():
    assert [(schema, table) for schema, table, alias in extract_tables(
        'INSERT INTO users (id, name) VALUES (1, 2)')] == [(None, 'users')]
