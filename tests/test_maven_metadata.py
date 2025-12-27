"""
Tests for jgo.maven.metadata utility functions.
"""

from datetime import datetime

from jgo.maven.metadata import ts2dt


def test_ts2dt_with_dot():
    """Test the ts2dt function with dot separator."""
    ts = "20210702.144917"
    result = ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 17)


def test_ts2dt_without_dot():
    """Test the ts2dt function without dot separator."""
    ts = "20210702144918"
    result = ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 18)


def test_ts2dt_invalid():
    """Test the ts2dt function with invalid timestamp."""
    try:
        ts2dt("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid timestamp" in str(e)
