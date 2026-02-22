"""
Tests for the Maven utility functions (jgo.util.maven).
"""

import shutil
from pathlib import Path

import pytest

from jgo.util.mvn import ensure_maven_available, fetch_maven


class TestEnsureMavenAvailable:
    """Tests for ensure_maven_available function."""

    def test_finds_system_maven(self):
        """Test that it finds Maven when it's on the system PATH."""
        # This test will pass if Maven is already installed on the system
        if shutil.which("mvn"):
            mvn_path = ensure_maven_available()
            assert mvn_path is not None
            assert isinstance(mvn_path, Path)
            assert mvn_path.exists()
            # Handle both Unix (mvn) and Windows (mvn.cmd or mvn.CMD)
            assert mvn_path.stem.lower() == "mvn"

    def test_fetches_maven_when_missing(self, monkeypatch):
        """Test that it fetches Maven when not on PATH."""
        # Mock shutil.which to return None (simulating Maven not being on PATH)
        monkeypatch.setattr(shutil, "which", lambda x: None)

        mvn_path = ensure_maven_available()
        assert mvn_path is not None
        assert isinstance(mvn_path, Path)
        assert mvn_path.exists()
        # Handle both Unix (mvn) and Windows (mvn.cmd or mvn.CMD)
        assert mvn_path.stem.lower() == "mvn"


class TestFetchMaven:
    """Tests for fetch_maven function."""

    def test_fetch_maven_with_defaults(self):
        """Test that fetch_maven works with default URL and SHA."""
        mvn_path = fetch_maven()
        assert mvn_path is not None
        assert isinstance(mvn_path, Path)
        assert mvn_path.exists()
        # Handle both Unix (mvn) and Windows (mvn.cmd or mvn.CMD)
        assert mvn_path.stem.lower() == "mvn"

    def test_fetch_maven_invalid_sha(self):
        """Test that fetch_maven raises ValueError for invalid SHA length."""
        with pytest.raises(ValueError) as exc_info:
            fetch_maven(
                url="https://example.com/maven.tar.gz",
                sha="invalid",  # Too short
            )

        assert "invalid SHA length" in str(exc_info.value)
