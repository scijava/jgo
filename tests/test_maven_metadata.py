"""
Tests for jgo.maven.metadata utility functions.
"""

from datetime import datetime, timezone

from jgo.maven import MavenContext
from jgo.maven._metadata import ts2dt


def test_ts2dt_with_dot():
    """Test the ts2dt function with dot separator."""
    ts = "20210702.144917"
    result = ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 17, tzinfo=timezone.utc)


def test_ts2dt_without_dot():
    """Test the ts2dt function without dot separator."""
    ts = "20210702144918"
    result = ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 18, tzinfo=timezone.utc)


def test_ts2dt_invalid():
    """Test the ts2dt function with invalid timestamp."""
    try:
        ts2dt("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid timestamp" in str(e)


def test_release_version_resolution(m2_repo):
    """
    Regression test: RELEASE version token must resolve to a concrete version
    by fetching maven-metadata.xml from remote repositories.

    This guards against a failure observed downstream on Windows with Java 21,
    where org.openjdk.nashorn:nashorn-core was added without a pinned version.
    If metadata fetching fails silently, resolved_version raises RuntimeError
    instead of returning a concrete version.
    """
    context = MavenContext(repo_cache=m2_repo)
    project = context.project("org.openjdk.nashorn", "nashorn-core")
    component = project.at_version("RELEASE")

    resolved = component.resolved_version

    assert resolved != "RELEASE", (
        "RELEASE should have been resolved to a concrete version"
    )
    assert resolved, "Resolved version should be non-empty"


class _FakeResponse:
    def __init__(self, status_code=200, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload

    def json(self):
        return self._payload


def _remote_artifact(tmp_path):
    context = MavenContext(
        repo_cache=tmp_path,
        local_repos=[],
        remote_repos={"test": "https://repo.example.invalid/maven"},
    )
    return context.project("org.example", "foo").at_version("1.0").artifact()


def test_last_modified_is_utc_aware(tmp_path, monkeypatch):
    """
    Regression test: last_modified() must be UTC-aware, like lastUpdated,
    so that callers can compare the two without a naive/aware TypeError.
    """
    headers = {"Last-Modified": "Wed, 21 Oct 2026 07:28:00 GMT"}
    monkeypatch.setattr(
        "jgo.util.http.head", lambda *a, **kw: _FakeResponse(headers=headers)
    )
    result = _remote_artifact(tmp_path).last_modified()
    assert result == datetime(2026, 10, 21, 7, 28, tzinfo=timezone.utc)
    assert result > ts2dt("20261021000000")  # naive/aware mix would raise


def test_last_modified_nexus_converts_offset_to_utc(tmp_path, monkeypatch):
    """A Nexus 3 lastModified with a non-UTC offset is converted, not discarded."""
    monkeypatch.setattr(
        "jgo.util.http.head",
        lambda *a, **kw: _FakeResponse(headers={"Server": "Nexus/3.70.0"}),
    )
    payload = {"items": [{"assets": [{"lastModified": "2026-10-21T02:28:00-05:00"}]}]}
    monkeypatch.setattr(
        "jgo.util.http.get", lambda *a, **kw: _FakeResponse(payload=payload)
    )
    result = _remote_artifact(tmp_path).last_modified()
    assert result == datetime(2026, 10, 21, 7, 28, tzinfo=timezone.utc)
