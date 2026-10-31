import pytest
from litecli.sqlexecute import SQLExecute, OperationalError


def test_bound_unicode_rows_and_headers(tmp_path):
    db = SQLExecute(str(tmp_path / 'demo.sqlite'))
    try:
        list(db.run('CREATE TABLE messages(id INTEGER, body TEXT)'))
        db.conn.execute('INSERT INTO messages VALUES (?, ?)', (2, '\u00e7ay'))
        db.conn.execute('INSERT INTO messages VALUES (?, ?)', (1, "O'Reilly"))
        title, rows, headers, status = list(db.run('SELECT body AS message FROM messages ORDER BY id'))[0]
        assert title is None
        assert rows == [("O'Reilly",), ('\u00e7ay',)]
        assert headers == ['message']
        assert status == '2 rows in set'
    finally:
        db.conn.close()


def test_empty_and_invalid_sql(tmp_path):
    db = SQLExecute(str(tmp_path / 'errors.sqlite'))
    try:
        assert list(db.run('  ')) == [(None, None, None, None)]
        with pytest.raises(OperationalError):
            list(db.run('SELECT FROM'))
    finally:
        db.conn.close()
