from repo_context.core import parse_github_url


def test_branch_and_subdirectory_are_separated():
    assert parse_github_url('https://github.com/owner/project/tree/main/src/pkg/') == ('https://github.com/owner/project.git', 'main', 'src/pkg')


from repo_context.core import parse_github_url

def test_nondefault_branch_and_nested_directory():
    assert parse_github_url('https://github.com/owner/project/tree/dev/lib/pkg/') == ('https://github.com/owner/project.git','dev','lib/pkg')
