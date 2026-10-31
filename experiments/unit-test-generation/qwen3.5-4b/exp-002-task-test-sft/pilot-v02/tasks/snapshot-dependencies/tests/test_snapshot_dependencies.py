from repo_context.core import analyze_dependencies


def test_requirements_are_included_in_dependency_context(tmp_path):
    (tmp_path / 'requirements.txt').write_text('fastapi==0.115.0\npytest==8.4.2\n')
    stack, details = analyze_dependencies(tmp_path)
    assert stack == 'Python'
    assert 'requirements.txt' in details
    assert 'fastapi==0.115.0' in details and 'pytest==8.4.2' in details


def test_pyproject_dependencies_are_listed(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies = ["httpx>=0.28", "pytest>=8"]\n')
    stack, details=analyze_dependencies(tmp_path)
    assert stack == 'Python'
    assert 'pyproject.toml' in details
    assert 'httpx>=0.28' in details and 'pytest>=8' in details
