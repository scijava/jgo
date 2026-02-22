"""Tests for output formatting functions."""

from __future__ import annotations

from jgo.cli._output import print_dry_run


class TestMessageFunctions:
    """Test message output functions."""

    def test_print_dry_run(self, capsys):
        """Test dry-run message with prefix."""
        print_dry_run("Would delete 5 files")
        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out
        assert "Would delete 5 files" in captured.out
        assert captured.err == ""
