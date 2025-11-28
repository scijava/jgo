import unittest
from pathlib import Path
from jgo.jgo import m2_home, m2_repo, m2_path


class TestMavenPaths(unittest.TestCase):
    def test_m2_home(self):
        assert m2_home() == Path.home() / ".m2"

    def test_m2_repo(self):
        assert m2_repo() == Path.home() / ".m2" / "repository"

    def test_m2_path(self):
        assert m2_path() == Path.home() / ".m2"
