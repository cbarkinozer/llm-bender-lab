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
