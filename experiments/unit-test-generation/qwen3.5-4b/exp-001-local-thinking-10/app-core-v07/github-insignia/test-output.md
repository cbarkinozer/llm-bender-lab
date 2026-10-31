File: tests/conftest.py
```python
from datetime import datetime, timezone
import httpx
import pytest

NOW = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)


def repo(name="alpha", stars=5, **extra):
    return {"id": name, "name": name, "full_name": f"cbarkinozer/{name}",
            "owner": {"login": "cbarkinozer"}, "private": False, "fork": False,
            "stargazers_count": stars, "forks_count": 1, "language": "Python",
            "pushed_at": "2026-10-01T00:00:00Z", "html_url": f"https://github.com/cbarkinozer/{name}",
            "description": "A useful project", "archived": False, **extra}


@pytest.fixture
def api_factory():
    def make(failure=None, token=None):
        requests = []
        def handler(request):
            requests.append(request)
            path = request.url.path
            if failure and failure(request):
                return httpx.Response(503, json={"message": "upstream unavailable"})
            if path == "/users/cbarkinozer":
                return httpx.Response(200, json={"login": "cbarkinozer", "name": "Barkin", "bio": "AI Engineer", "avatar_url": "https://avatars.githubusercontent.com/u/1", "html_url": "https://github.com/cbarkinozer", "followers": 9, "following": 3})
            if path.endswith("/repos"):
                if request.url.params.get("page") == "2":
                    return httpx.Response(200, json=[repo("beta", 9, pushed_at="2026-09-01T00:00:00Z")])
                return httpx.Response(200, json=[repo(), repo("fork", 99, fork=True), repo("private", 88, private=True), repo("other", 77, owner={"login": "other"})], headers={"Link": '<https://api.github.com/users/cbarkinozer/repos?per_page=100&page=2>; rel="next"'})
            if path.endswith("/languages"):
                return httpx.Response(200, json={"Python": 300, "Rust": 100})
            if path == "/graphql":
                import json
                variables = json.loads(request.content)["variables"]
                day = variables["start"][:10]
                return httpx.Response(200, json={"data": {"user": {"contributionsCollection": {
                    "totalCommitContributions": 3, "totalPullRequestContributions": 2,
                    "totalIssueContributions": 1, "restrictedContributionsCount": 4,
                    "contributionCalendar": {"totalContributions": 10, "weeks": [{"contributionDays": [{"date": day, "contributionCount": 10}]}]}
                }}}})
            raise AssertionError(f"Unexpected request: {request.url}")
        from insignia.github import GitHubClient
        return GitHubClient(token=token, transport=httpx.MockTransport(handler)), requests
    return make
```

File: tests/test_requirements.py
```python
'Acceptance checks for observable application behavior.'
import json
import copy
from datetime import datetime, timezone, timedelta
import httpx
import pytest
from conftest import NOW, repo
from insignia.metrics import repository_metrics, top_repositories, date_window, query_windows
from insignia.service import DashboardService
from insignia.github import GitHubClient, GitHubError


def test_r1_filter_calculation_and_byte_shares():
    items = [repo(), repo("beta", 9, archived=True), repo("fork", 100, fork=True), repo("secret", 200, private=True), repo("other", 300, owner={"login": "other"})]
    result = repository_metrics(items, {"alpha": {"Python": 300, "Rust": 100}, "beta": {"Rust": 400}}, "cbarkinozer")
    assert result["stars"] == 14
    assert result["repository_count"] == 2
    assert result["languages"] == [{"name": "Rust", "bytes": 500, "percent": 62.5}, {"name": "Python", "bytes": 300, "percent": 37.5}]


def test_r1_empty_language_data_is_not_a_fabricated_percentage():
    assert repository_metrics([], {}, "cbarkinozer")["languages"] == []


def test_r2_sort_stars_activity_ties_and_invalid_sort():
    items = [repo("zeta", 9, pushed_at="2026-01-01T00:00:00Z"), repo("alpha", 9), repo("beta", 2, pushed_at=None)]
    assert [r["name"] for r in top_repositories(items, "stars", 2)] == ["alpha", "zeta"]
    assert [r["name"] for r in top_repositories(items, "activity", 3)] == ["alpha", "zeta", "beta"]
    with pytest.raises(ValueError):
        top_repositories(items, "invalid", 6)


def test_r3_utc_leap_date_and_year_splitting():
    start, end = date_window(datetime.fromisoformat("2024-02-29T01:00:00+03:00"))
    assert start.isoformat() == "2023-02-28T00:00:00+00:00"
    assert end.isoformat() == "2024-02-28T22:00:00+00:00"
    leap_start, _ = date_window(datetime(2024, 2, 29, 12, tzinfo=timezone.utc))
    assert leap_start.day == 28
    windows = query_windows(*date_window(NOW))
    assert len(windows) == 2
    assert windows[0][1].isoformat() == "2025-12-31T23:59:59+00:00"
    assert windows[1][0].isoformat() == "2026-01-01T00:00:00+00:00"


async def test_r4_pagination_and_filter_before_language_requests(api_factory):
    api, requests = api_factory()
    data = await api.fetch("cbarkinozer", NOW)
    assert data["metrics"]["stars"] == 14
    assert data["metrics"]["repository_count"] == 2
    assert len([r for r in requests if r.url.path.endswith("/repos")]) == 2
    assert len([r for r in requests if r.url.path.endswith("/languages")]) == 2
    assert data["activity"] is None
    assert data["activity_unavailable_reason"]
    assert data["profile"]["login"] == "cbarkinozer"
    assert data["profile"]["location"] is None
    assert all(data["scope"][key] for key in ("repositories", "languages", "activity"))
    assert not any(r.url.path == "/graphql" for r in requests)


async def test_r3_graphql_window_combination_and_secret_absence(api_factory):
    api, requests = api_factory(token="secret-fixture-token")
    data = await api.fetch("cbarkinozer", NOW)
    assert data["activity"]["commits"] == 6
    assert data["activity"]["pull_requests"] == 4
    assert data["activity"]["issues"] == 2
    assert data["activity"]["total"] == 20
    assert data["activity"]["restricted"] == 8
    assert len(data["activity"]["days"]) == 2
    assert "secret-fixture-token" not in json.dumps(data)
    assert all(r.headers["Authorization"] == "Bearer secret-fixture-token" for r in requests)


async def test_r5_cache_read_restart_and_manual_refresh(tmp_path, api_factory):
    api, requests = api_factory()
    path = tmp_path / "snapshot.json"
    service = DashboardService(api, path, clock=lambda: NOW)
    assert service.read()["snapshot"] is None
    assert requests == []
    result = await service.refresh()
    assert result["error"] is None
    before = len(requests)
    assert service.read()["snapshot"]["fetched_at"] == NOW.isoformat()
    restarted = DashboardService(api, path, clock=lambda: NOW)
    assert restarted.read() == service.read()
    assert len(requests) == before


@pytest.mark.parametrize("endpoint", ["/users/cbarkinozer", "/users/cbarkinozer/repos", "/repos/cbarkinozer/alpha/languages", "/graphql"])
async def test_r5_failed_refresh_preserves_complete_snapshot(tmp_path, api_factory, endpoint):
    api, _ = api_factory(token="secret")
    path = tmp_path / "snapshot.json"
    service = DashboardService(api, path, clock=lambda: NOW)
    old = copy.deepcopy((await service.refresh())["snapshot"])
    original_bytes = path.read_bytes()
    service.clock = lambda: NOW + timedelta(hours=1)
    broken, _ = api_factory(token="secret", failure=lambda r: r.url.path == endpoint)
    service.api = broken
    failed = await service.refresh()
    assert failed["error"]
    assert failed["snapshot"] == old
    assert path.read_bytes() == original_bytes
    assert "secret" not in failed["error"]


@pytest.mark.parametrize("failure", ["graphql-error", "timeout", "unauthorized"])
async def test_r4_graphql_errors_and_timeout_are_failures(api_factory, failure):
    api, requests = api_factory(token="secret")
    handler = api.transport.handler

    def fail_at_graphql(request):
        if request.url.path != "/graphql":
            return handler(request)
        requests.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("secret upstream text", request=request)
        if failure == "unauthorized":
            return httpx.Response(401, json={})
        return httpx.Response(200, json={"errors": [{"message": "secret upstream text"}]})

    api.transport = httpx.MockTransport(fail_at_graphql)
    expected = {"graphql-error": "GraphQL", "timeout": "Could not reach GitHub", "unauthorized": "rejected"}
    with pytest.raises(GitHubError, match=expected[failure]) as error:
        await api.fetch("cbarkinozer", NOW)
    assert requests[-1].url.path == "/graphql"
    assert "secret" not in str(error.value)


async def test_r5_cache_write_failure_preserves_memory_and_disk(tmp_path, api_factory, monkeypatch):
    api, _ = api_factory()
    service = DashboardService(api, tmp_path / "snapshot.json", clock=lambda: NOW)
    old = copy.deepcopy((await service.refresh())["snapshot"])
    original_bytes = service.cache_path.read_bytes()
    service.clock = lambda: NOW + timedelta(hours=1)
    def fail(data):
        raise OSError("disk full")
    monkeypatch.setattr(service, "_save", fail)
    result = await service.refresh()
    assert result["error"]
    assert result["snapshot"] == old
    assert service.read()["snapshot"] == old
    assert service.cache_path.read_bytes() == original_bytes


async def test_r6_fastapi_and_mcp_share_service(tmp_path, api_factory):
    from fastapi.testclient import TestClient
    from fastmcp import Client
    from insignia.app import create_app
    api, requests = api_factory()
    service = DashboardService(api, tmp_path / "snapshot.json", clock=lambda: NOW)
    app = create_app(service)
    with TestClient(app) as web:
        assert web.get("/").status_code == 200
        assert web.get("/api/dashboard").json()["snapshot"] is None
        assert requests == []
        assert web.post("/api/refresh").json()["snapshot"]["metrics"]["stars"] == 14
        assert web.get("/api/dashboard").json()["snapshot"] == service.read()["snapshot"]
    async with Client(app.state.mcp) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == {"refresh_data", "activity_summary", "top_repositories"}
        result = await client.call_tool("top_repositories", {"sort": "stars", "limit": 1})
        assert result.data[0]["name"] == "beta"
        summary = await client.call_tool("activity_summary", {})
        assert summary.data["activity"] is None


async def test_r5_successful_refresh_replaces_snapshot_and_timestamp(tmp_path, api_factory):
    api, _ = api_factory()
    service = DashboardService(api, tmp_path/'snapshot.json', clock=lambda: NOW)
    old = copy.deepcopy((await service.refresh())['snapshot'])
    service.clock = lambda: NOW + timedelta(hours=1)
    handler = api.transport.handler
    def changed(request):
        response = handler(request)
        if request.url.path.endswith('/repos') and request.url.params.get('page') != '2':
            payload = response.json()
            payload[0]['stargazers_count'] = 25
            return httpx.Response(200,json=payload,headers=response.headers)
        return response
    service.api = GitHubClient(transport=httpx.MockTransport(changed))
    result = await service.refresh()
    assert result['error'] is None
    assert result['snapshot']['fetched_at'] == (NOW + timedelta(hours=1)).isoformat()
    assert result['snapshot']['metrics']['stars'] == 34
    assert old['metrics']['stars'] == 14
    assert json.loads(service.cache_path.read_text()) == result['snapshot']
```

File: tests/test_snapshot_contract.py
```python
'Acceptance checks for observable application behavior.'
import json
import copy
from datetime import timedelta
import httpx
import pytest
from conftest import NOW
from insignia.github import GitHubClient, GitHubError
from insignia.service import DashboardService


async def test_actual_transport_timeout_is_sanitized():
    def timeout(request):
        raise httpx.ReadTimeout("secret-token could occur in exception text", request=request)
    api = GitHubClient(token="secret-token", transport=httpx.MockTransport(timeout))
    with pytest.raises(GitHubError, match="Could not reach GitHub") as error:
        await api.fetch("cbarkinozer", NOW)
    assert "secret-token" not in str(error.value)


async def test_graphql_http_200_errors_preserve_previous_snapshot(tmp_path, api_factory):
    api, requests = api_factory(token="secret-token")
    service = DashboardService(api, tmp_path / "snapshot.json", clock=lambda: NOW)
    old = copy.deepcopy((await service.refresh())["snapshot"])
    service.clock = lambda: NOW + timedelta(hours=1)
    handler = api.transport.handler
    def broken(request):
        if request.url.path == "/graphql":
            return httpx.Response(200, json={"errors": [{"message": "secret-token internal"}]})
        return handler(request)
    service.api = GitHubClient(token="secret-token", transport=httpx.MockTransport(broken))
    result = await service.refresh()
    assert result["snapshot"] == old
    assert "GraphQL" in result["error"]
    assert "secret-token" not in json.dumps(result)


async def test_real_zero_activity_stays_zero(api_factory):
    api, _ = api_factory(token="test")
    handler = api.transport.handler
    def zero(request):
        response = handler(request)
        if request.url.path == "/graphql":
            body = response.json()
            c = body["data"]["user"]["contributionsCollection"]
            for key in ["totalCommitContributions", "totalPullRequestContributions", "totalIssueContributions", "restrictedContributionsCount"]:
                c[key] = 0
            c["contributionCalendar"] = {"totalContributions": 0, "weeks": []}
            return httpx.Response(200, json=body)
        return response
    api.transport = httpx.MockTransport(zero)
    result = await api.fetch("cbarkinozer", NOW)
    assert result["activity"]["total"] == 0
    assert result["activity"]["commits"] == 0
    assert result["activity_unavailable_reason"] is None


async def test_pagination_cannot_forward_credentials_to_another_host(api_factory):
    api, _ = api_factory(token="test")
    handler = api.transport.handler
    seen = []
    def malicious(request):
        seen.append(request.url.host)
        if request.url.path.endswith("/repos"):
            return httpx.Response(200, json=[], headers={"Link": '<https://evil.example/repos>; rel="next"'})
        return handler(request)
    api.transport = httpx.MockTransport(malicious)
    with pytest.raises(GitHubError, match="unsafe pagination"):
        await api.fetch("cbarkinozer", NOW)
    assert set(seen) == {"api.github.com"}


@pytest.mark.parametrize("payload", ["not json", "{}", '[]'])
def test_corrupt_cache_is_unavailable(tmp_path, api_factory, payload):
    path = tmp_path / "snapshot.json"
    path.write_text(payload)
    api, requests = api_factory()
    result = DashboardService(api, path).read()
    assert result["snapshot"] is None
    assert result["error"]
    assert not requests


async def test_missing_graphql_totals_does_not_turn_into_zero(api_factory):
    api, _ = api_factory(token="test")
    handler = api.transport.handler
    def incomplete(request):
        if request.url.path == "/graphql":
            return httpx.Response(200, json={"data": {"user": {"contributionsCollection": {}}}})
        return handler(request)
    api.transport = httpx.MockTransport(incomplete)
    with pytest.raises(GitHubError, match="incomplete"):
        await api.fetch("cbarkinozer", NOW)


async def test_http_mcp_transport_and_refresh_tool(tmp_path, api_factory):
    from insignia.app import create_app
    from fastmcp import Client
    from fastapi.testclient import TestClient
    api, requests = api_factory()
    service = DashboardService(api, tmp_path / "snapshot.json", clock=lambda: NOW)
    app = create_app(service)
    async with Client(app.state.mcp) as client:
        result = await client.call_tool("refresh_data", {})
        assert result.data["snapshot"]["metrics"]["stars"] == 14
        result = await client.call_tool("activity_summary", {})
        assert result.data["fetched_at"] == NOW.isoformat()
    with TestClient(app) as web:
        response = web.post("/mcp/", headers={"Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}})
        assert response.status_code == 200
        assert '"serverInfo"' in response.text


@pytest.mark.parametrize('defect,mutate', [
    ('missing-reason', lambda s:s.pop('activity_unavailable_reason')),
    ('profile', lambda s:s.update(profile={})),
    ('metrics', lambda s:s['metrics'].update(stars='many')),
    ('repositories', lambda s:s['repositories'][0].update(stargazers_count=None)),
    ('scope', lambda s:s.update(scope=[])),
    ('window', lambda s:s['window'].update(start='not a date')),
    ('fetched-at', lambda s:s.update(fetched_at='2026-10-30T12:00:00')),
    ('language-percent', lambda s:s['metrics']['languages'][0].update(percent=float('nan'))),
    ('activity-days', lambda s:s['activity']['days'][0].update(date='2026-02-30')),
    ('activity-count', lambda s:s['activity'].update(commits=-1)),
], ids=lambda value:value if isinstance(value,str) else None)
async def test_structurally_invalid_cache_is_rejected(tmp_path, api_factory, defect, mutate):
    api, _ = api_factory(token='fixture-token')
    saved = await api.fetch('cbarkinozer', NOW)
    mutate(saved)
    path = tmp_path / 'snapshot.json'
    original = json.dumps(saved)
    path.write_text(original)
    api, requests = api_factory()
    service = DashboardService(api, path)
    assert service.read()['snapshot'] is None
    assert service.read()['error']
    assert service.summary() == service.read()
    assert service.top() is None
    assert path.read_text() == original
    assert requests == []
    assert (await service.refresh())['error'] is None
    assert service.summary()['activity'] is None


async def test_authenticated_snapshot_survives_restart(tmp_path, api_factory):
    api, requests = api_factory(token='fixture-token')
    path = tmp_path / 'snapshot.json'
    service = DashboardService(api, path, clock=lambda: NOW)
    expected = await service.refresh()
    requests.clear()
    restored = DashboardService(api, path)
    assert "fixture-token" not in path.read_text()
    assert restored.read() == expected
    assert restored.summary()['activity'] == expected['snapshot']['activity']
    assert restored.top('stars', 1)[0]['name'] == 'beta'
    assert requests == []

def test_http_local_origin_and_host_guards(tmp_path, api_factory):
    from fastapi.testclient import TestClient
    from insignia.app import create_app
    api, _ = api_factory()
    service = DashboardService(api, tmp_path/'snapshot.json', clock=lambda: NOW)
    with TestClient(create_app(service)) as web:
        assert web.post('/api/refresh', headers={'Origin':'https://external.example'}).status_code == 403
        assert web.get('/api/dashboard', headers={'Host':'external.example'}).status_code == 400

```

File: pytest.ini
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```
