import os
import unittest
from pathlib import Path
from unittest.mock import patch

from jgo.jgo import m2_home, m2_path, m2_repo


class TestMavenPaths(unittest.TestCase):
    def test_m2_home(self):
        """Test m2_home() returns correct default path."""
        # Mock environment to ensure no M2_HOME is set
        with patch.dict(os.environ, {}, clear=False):
            # Remove M2_HOME if it exists
            os.environ.pop("M2_HOME", None)
            assert m2_home() == Path.home() / ".m2"

    def test_m2_repo(self):
        """Test m2_repo() returns correct default path."""
        # Mock environment to ensure no M2_HOME or M2_REPO is set
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("M2_HOME", None)
            os.environ.pop("M2_REPO", None)
            assert m2_repo() == Path.home() / ".m2" / "repository"

    def test_m2_path(self):
        """Test deprecated m2_path() function."""
        # Mock environment to ensure no M2_REPO is set
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("M2_REPO", None)
            assert m2_path() == Path.home() / ".m2"
