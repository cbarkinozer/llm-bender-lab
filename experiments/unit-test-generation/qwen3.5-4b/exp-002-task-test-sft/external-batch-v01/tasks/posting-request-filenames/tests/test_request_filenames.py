import os
import pytest
from posting.files import is_valid_filename, get_unique_request_filename


@pytest.mark.parametrize('name', ['', '   ', 'CON.txt', '.hidden', 'end.', 'a..b', 'a' * 256, 'dir' + os.path.sep + 'file'])
def test_invalid_names(name):
    assert is_valid_filename(name) is False


def test_valid_names_and_collision_sequence(tmp_path):
    assert is_valid_filename('request-1.posting.yaml') is True
    name = 'request.posting.yaml'
    assert get_unique_request_filename(name, tmp_path) == name
    (tmp_path / name).touch()
    assert get_unique_request_filename(name, tmp_path) == 'request-01.posting.yaml'
    (tmp_path / 'request-01.posting.yaml').touch()
    assert get_unique_request_filename(name, tmp_path) == 'request-02.posting.yaml'
    assert {p.name for p in tmp_path.iterdir()} == {name, 'request-01.posting.yaml'}
