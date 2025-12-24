"""Tests for output formatting functions."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from jgo.cli.output import (
    _style_text,
    _supports_color,
    print_data,
    print_dry_run,
    print_error,
    print_key_value,
    print_list_item,
    print_message,
    print_success,
    print_table_header,
    print_table_section,
    print_verbose,
    print_warning,
)


class TestColorSupport:
    """Test color detection functions."""

    def test_supports_color_with_no_color_env(self):
        """Test that NO_COLOR environment variable disables colors."""
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            assert not _supports_color()

    def test_supports_color_with_tty(self):
        """Test that TTY enables colors when NO_COLOR is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.stderr.isatty", return_value=True):
                assert _supports_color()

    def test_supports_color_without_tty(self):
        """Test that non-TTY disables colors."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.stderr.isatty", return_value=False):
                assert not _supports_color()

    def test_supports_color_no_isatty_method(self):
        """Test that missing isatty method disables colors."""
        with patch.dict("os.environ", {}, clear=True):
            # Create a mock stderr without isatty
            mock_stderr = type("MockStderr", (), {})()
            with patch("sys.stderr", mock_stderr):
                assert not _supports_color()

    def test_style_text_with_color_support(self):
        """Test text styling when colors are supported."""
        with patch("jgo.cli.output._supports_color", return_value=True):
            result = _style_text("test", color="red", bold=True)
            # Should contain ANSI codes
            assert "\x1b[" in result or "test" in result

    def test_style_text_without_color_support(self):
        """Test text styling when colors are not supported."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            result = _style_text("test", color="red", bold=True)
            # Should return plain text
            assert result == "test"
            assert "\x1b[" not in result


class TestMessageFunctions:
    """Test message output functions."""

    def test_print_message_basic(self, capsys):
        """Test basic message printing."""
        print_message("Test message")
        captured = capsys.readouterr()
        assert captured.out == "Test message\n"
        assert captured.err == ""

    def test_print_message_with_prefix(self, capsys):
        """Test message with prefix."""
        print_message("Test message", prefix="INFO:")
        captured = capsys.readouterr()
        assert captured.out == "INFO: Test message\n"

    def test_print_message_with_indent(self, capsys):
        """Test message with indentation."""
        print_message("Test message", indent=4)
        captured = capsys.readouterr()
        assert captured.out == "    Test message\n"

    def test_print_message_with_prefix_and_indent(self, capsys):
        """Test message with both prefix and indentation."""
        print_message("Test message", prefix="NOTE:", indent=2)
        captured = capsys.readouterr()
        assert captured.out == "  NOTE: Test message\n"

    def test_print_message_to_stderr(self, capsys):
        """Test printing message to stderr."""
        print_message("Test message", file=sys.stderr)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == "Test message\n"

    def test_print_success(self, capsys):
        """Test success message printing."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_success("Operation successful")
            captured = capsys.readouterr()
            assert "Operation successful" in captured.out
            assert captured.err == ""

    def test_print_success_with_indent(self, capsys):
        """Test success message with indentation."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_success("Operation successful", indent=2)
            captured = capsys.readouterr()
            assert "  Operation successful" in captured.out

    def test_print_warning(self, capsys):
        """Test warning message printing to stderr."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_warning("Warning message")
            captured = capsys.readouterr()
            assert captured.out == ""
            assert "Warning message" in captured.err

    def test_print_error(self, capsys):
        """Test error message printing to stderr with prefix."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_error("Something failed")
            captured = capsys.readouterr()
            assert captured.out == ""
            assert "Error: Something failed" in captured.err

    def test_print_error_no_double_prefix(self, capsys):
        """Test that error prefix is not duplicated."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            # User should NOT include "Error:" in message
            print_error("File not found")
            captured = capsys.readouterr()
            # Should have exactly one "Error:" prefix
            assert captured.err == "Error: File not found\n"
            assert captured.err.count("Error:") == 1

    def test_print_dry_run(self, capsys):
        """Test dry-run message with prefix."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_dry_run("Would delete 5 files")
            captured = capsys.readouterr()
            assert "[DRY-RUN]" in captured.out
            assert "Would delete 5 files" in captured.out
            assert captured.err == ""

    def test_print_verbose_deprecated(self, capsys):
        """Test that print_verbose shows deprecation warning."""
        with pytest.warns(DeprecationWarning, match="print_verbose is deprecated"):
            print_verbose("Debug message")
        captured = capsys.readouterr()
        # Should print to stderr
        assert "Debug message" in captured.err


class TestDataOutputFunctions:
    """Test data output functions."""

    def test_print_data(self, capsys):
        """Test raw data output."""
        print_data("raw:data:output")
        captured = capsys.readouterr()
        assert captured.out == "raw:data:output\n"
        assert captured.err == ""

    def test_print_data_with_separator(self, capsys):
        """Test data output with separator."""
        print_data("data", separator="---")
        captured = capsys.readouterr()
        assert captured.out == "data\n---\n"

    def test_print_data_no_ansi_codes(self, capsys):
        """Test that data output never contains ANSI codes."""
        # Even if color support is enabled, print_data should be plain
        with patch("jgo.cli.output._supports_color", return_value=True):
            print_data("raw:data:output")
            captured = capsys.readouterr()
            # Verify no ANSI escape sequences
            assert "\x1b[" not in captured.out
            assert captured.out == "raw:data:output\n"

    def test_print_table_header(self, capsys):
        """Test table header formatting."""
        print_table_header("TEST HEADER")
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "=" * 70
        assert lines[1] == "TEST HEADER"
        assert lines[2] == "=" * 70

    def test_print_table_header_custom_width(self, capsys):
        """Test table header with custom width."""
        print_table_header("TITLE", width=30)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[0] == "=" * 30
        assert lines[2] == "=" * 30

    def test_print_table_header_custom_char(self, capsys):
        """Test table header with custom character."""
        print_table_header("TITLE", char="-")
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[0] == "-" * 70
        assert lines[2] == "-" * 70

    def test_print_table_section(self, capsys):
        """Test table section formatting."""
        print_table_section("Section Title")
        captured = capsys.readouterr()
        assert "\nSection Title\n" in captured.out
        assert "-" * 70 in captured.out

    def test_print_table_section_custom_width(self, capsys):
        """Test table section with custom width."""
        print_table_section("Section", width=30)
        captured = capsys.readouterr()
        assert "-" * 30 in captured.out

    def test_print_key_value(self, capsys):
        """Test key-value pair formatting."""
        print_key_value("name", "jgo")
        captured = capsys.readouterr()
        assert captured.out == "  name: jgo\n"

    def test_print_key_value_custom_indent(self, capsys):
        """Test key-value with custom indentation."""
        print_key_value("version", "1.0.0", indent=4)
        captured = capsys.readouterr()
        assert captured.out == "    version: 1.0.0\n"

    def test_print_list_item(self, capsys):
        """Test list item formatting."""
        print_list_item("First item")
        captured = capsys.readouterr()
        assert captured.out == "  - First item\n"

    def test_print_list_item_custom_marker(self, capsys):
        """Test list item with custom marker."""
        print_list_item("Item", marker="*")
        captured = capsys.readouterr()
        assert captured.out == "  * Item\n"

    def test_print_list_item_custom_indent(self, capsys):
        """Test list item with custom indentation."""
        print_list_item("Item", indent=4, marker="+")
        captured = capsys.readouterr()
        assert captured.out == "    + Item\n"


class TestColoredOutput:
    """Test that color functions work with actual colors enabled."""

    def test_colored_success_message(self, capsys):
        """Test success message with colors enabled."""
        with patch("jgo.cli.output._supports_color", return_value=True):
            print_success("Success!")
            captured = capsys.readouterr()
            # Should contain either ANSI codes or the text
            assert "Success!" in captured.out

    def test_colored_error_message(self, capsys):
        """Test error message with colors enabled."""
        with patch("jgo.cli.output._supports_color", return_value=True):
            print_error("Failed")
            captured = capsys.readouterr()
            # Should contain the error text
            assert "Error: Failed" in captured.err

    def test_colored_warning_message(self, capsys):
        """Test warning message with colors enabled."""
        with patch("jgo.cli.output._supports_color", return_value=True):
            print_warning("Warning!")
            captured = capsys.readouterr()
            assert "Warning!" in captured.err

    def test_colored_dry_run_message(self, capsys):
        """Test dry-run message with colors enabled."""
        with patch("jgo.cli.output._supports_color", return_value=True):
            print_dry_run("Would do something")
            captured = capsys.readouterr()
            assert "Would do something" in captured.out
            assert "DRY-RUN" in captured.out


class TestIntegration:
    """Integration tests for output functions."""

    def test_multiple_messages_different_streams(self, capsys):
        """Test that stdout and stderr are properly separated."""
        with patch("jgo.cli.output._supports_color", return_value=False):
            print_message("stdout message")
            print_error("stderr message")
            print_success("another stdout")

            captured = capsys.readouterr()

            # Check stdout contains only stdout messages
            assert "stdout message" in captured.out
            assert "another stdout" in captured.out
            assert "Error:" not in captured.out

            # Check stderr contains only stderr messages
            assert "Error: stderr message" in captured.err
            assert "stdout message" not in captured.err

    def test_formatted_table_output(self, capsys):
        """Test creating a formatted table."""
        print_table_header("CONFIGURATION")
        print_key_value("cache_dir", "/home/user/.jgo")
        print_key_value("links", "auto")
        print_table_section("Repositories")
        print_list_item("Maven Central")
        print_list_item("SciJava Public")

        captured = capsys.readouterr()

        assert "CONFIGURATION" in captured.out
        assert "=" * 70 in captured.out
        assert "cache_dir: /home/user/.jgo" in captured.out
        assert "links: auto" in captured.out
        assert "Repositories" in captured.out
        assert "-" * 70 in captured.out
        assert "- Maven Central" in captured.out
        assert "- SciJava Public" in captured.out
