import pytest
from litecli.packages.parseutils import is_destructive


@pytest.mark.parametrize('sql', ['', 'SELECT 1', "SELECT 'delete from users'", '-- delete\nSELECT 2'])
def test_safe_statements(sql):
    assert is_destructive(sql) is False


@pytest.mark.parametrize('sql', ['DROP TABLE users', '-- comment\ndElEtE FROM users',
                                    'SELECT 1; ALTER TABLE users ADD COLUMN age INT', 'TRUNCATE users'])
def test_destructive_statements(sql):
    assert is_destructive(sql) is True
