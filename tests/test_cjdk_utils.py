"""
Tests for the cjdk utility functions (jgo.util.cjdk).
"""

import shutil
from pathlib import Path
import pytest

from jgo.util.cjdk import ensure_maven_available, fetch_maven


# Helper to check if cjdk is available
def _has_cjdk():
    try:
        import cjdk  # noqa: F401

        return True
    except ImportError:
        return False


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
            assert mvn_path.name == "mvn" or mvn_path.name == "mvn.cmd"

    @pytest.mark.skipif(not _has_cjdk(), reason="cjdk not installed")
    def test_fetches_maven_when_missing(self, monkeypatch):
        """Test that it fetches Maven using cjdk when not on PATH."""
        # Mock shutil.which to return None (simulating Maven not being on PATH)
        monkeypatch.setattr(shutil, "which", lambda x: None)

        mvn_path = ensure_maven_available()
        assert mvn_path is not None
        assert isinstance(mvn_path, Path)
        assert mvn_path.exists()
        assert mvn_path.name == "mvn" or mvn_path.name == "mvn.cmd"

    def test_raises_error_without_cjdk(self, monkeypatch):
        """Test that it raises RuntimeError when Maven is missing and cjdk is not installed."""
        # Mock shutil.which to return None (simulating Maven not being on PATH)
        monkeypatch.setattr(shutil, "which", lambda x: None)

        # Mock the import to simulate cjdk not being installed
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "cjdk":
                raise ImportError("No module named 'cjdk'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(RuntimeError) as exc_info:
            ensure_maven_available()

        assert "Maven not found" in str(exc_info.value)
        assert "cjdk" in str(exc_info.value)


class TestFetchMaven:
    """Tests for fetch_maven function."""

    @pytest.mark.skipif(not _has_cjdk(), reason="cjdk not installed")
    def test_fetch_maven_with_defaults(self):
        """Test that fetch_maven works with default URL and SHA."""
        mvn_path = fetch_maven()
        assert mvn_path is not None
        assert isinstance(mvn_path, Path)
        assert mvn_path.exists()
        assert mvn_path.name == "mvn" or mvn_path.name == "mvn.cmd"

    def test_fetch_maven_without_cjdk(self, monkeypatch):
        """Test that fetch_maven raises ImportError when cjdk is not installed."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "cjdk":
                raise ImportError("No module named 'cjdk'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(ImportError) as exc_info:
            fetch_maven()

        assert "cjdk is required" in str(exc_info.value)

    def test_fetch_maven_invalid_sha(self):
        """Test that fetch_maven raises ValueError for invalid SHA length."""
        with pytest.raises(ValueError) as exc_info:
            fetch_maven(
                url="https://example.com/maven.tar.gz",
                sha="invalid",  # Too short
            )

        assert "invalid SHA length" in str(exc_info.value)
