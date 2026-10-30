"""Post-implementation edge cases; see docs/04-revisions.md."""
import json
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
    old = (await service.refresh())["snapshot"]
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
        assert web.post("/api/refresh", headers={"Origin": "https://external.example"}).status_code == 403
        assert web.get("/api/dashboard", headers={"Host": "external.example"}).status_code == 400
        response = web.post("/mcp/", headers={"Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}})
        assert response.status_code == 200
        assert '"serverInfo"' in response.text


@pytest.mark.parametrize('defect', [
    'missing-reason', 'profile', 'metrics', 'repositories', 'scope',
    'window', 'fetched-at', 'language-percent', 'activity-days', 'activity-count',
])
async def test_structurally_invalid_cache_is_rejected(tmp_path, api_factory, defect):
    api, _ = api_factory(token='fixture-token')
    saved = await api.fetch('cbarkinozer', NOW)
    if defect == 'missing-reason':
        del saved['activity_unavailable_reason']
    elif defect == 'profile':
        saved['profile'] = {}
    elif defect == 'metrics':
        saved['metrics']['stars'] = 'many'
    elif defect == 'repositories':
        saved['repositories'][0]['stargazers_count'] = None
    elif defect == 'scope':
        saved['scope'] = []
    elif defect == 'window':
        saved['window']['start'] = 'not a date'
    elif defect == 'fetched-at':
        saved['fetched_at'] = '2026-10-30T12:00:00'  # Missing timezone.
    elif defect == 'language-percent':
        saved['metrics']['languages'][0]['percent'] = float('nan')
    elif defect == 'activity-days':
        saved['activity']['days'][0]['date'] = '2026-02-30'
    else:
        saved['activity']['commits'] = -1
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
    assert restored.read() == expected
    assert restored.summary()['activity'] == expected['snapshot']['activity']
    assert restored.top('stars', 1)[0]['name'] == 'beta'
    assert requests == []
