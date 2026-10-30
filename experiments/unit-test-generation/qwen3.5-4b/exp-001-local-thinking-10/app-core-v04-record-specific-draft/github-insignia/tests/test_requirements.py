"""Initial acceptance tests. Requirement mapping: docs/03-test-plan.md."""
import json
from datetime import datetime, timezone
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
    assert not any(r.url.path == "/graphql" for r in requests)


async def test_r5_graphql_window_combination_and_secret_absence(api_factory):
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


async def test_r6_cache_read_restart_and_manual_refresh(tmp_path, api_factory):
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
    assert "Authorization" not in path.read_text()


@pytest.mark.parametrize("endpoint", ["/users/cbarkinozer", "/users/cbarkinozer/repos", "/repos/cbarkinozer/alpha/languages", "/graphql"])
async def test_r7_failed_refresh_preserves_complete_snapshot(tmp_path, api_factory, endpoint):
    api, _ = api_factory(token="secret")
    path = tmp_path / "snapshot.json"
    service = DashboardService(api, path, clock=lambda: NOW)
    old = (await service.refresh())["snapshot"]
    original_bytes = path.read_bytes()
    broken, _ = api_factory(token="secret", failure=lambda r: r.url.path == endpoint)
    service.api = broken
    failed = await service.refresh()
    assert failed["error"]
    assert failed["snapshot"] == old
    assert path.read_bytes() == original_bytes
    assert "secret" not in failed["error"]


@pytest.mark.parametrize("failure", ["graphql-error", "timeout", "unauthorized"])
async def test_r7_graphql_errors_and_timeout_are_failures(api_factory, failure):
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


async def test_r8_cache_write_failure_preserves_memory_and_disk(tmp_path, api_factory, monkeypatch):
    api, _ = api_factory()
    service = DashboardService(api, tmp_path / "snapshot.json", clock=lambda: NOW)
    old = (await service.refresh())["snapshot"]
    def fail(data):
        raise OSError("disk full")
    monkeypatch.setattr(service, "_save", fail)
    result = await service.refresh()
    assert result["error"]
    assert result["snapshot"] == old


async def test_r9_fastapi_and_mcp_share_service(tmp_path, api_factory):
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
