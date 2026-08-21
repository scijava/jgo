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
