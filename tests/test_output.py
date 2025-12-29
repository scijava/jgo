"""Tests for output formatting functions."""

from __future__ import annotations

import sys

from jgo.cli.output import (
    print_dry_run,
    print_key_value,
    print_list_item,
    print_message,
    print_success,
    print_table_header,
    print_table_section,
)


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
        print_success("Operation successful")
        captured = capsys.readouterr()
        assert "Operation successful" in captured.out
        assert captured.err == ""

    def test_print_success_with_indent(self, capsys):
        """Test success message with indentation."""
        print_success("Operation successful", indent=2)
        captured = capsys.readouterr()
        assert "  Operation successful" in captured.out

    def test_print_dry_run(self, capsys):
        """Test dry-run message with prefix."""
        print_dry_run("Would delete 5 files")
        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out
        assert "Would delete 5 files" in captured.out
        assert captured.err == ""

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


class TestIntegration:
    """Integration tests for output functions."""

    def test_multiple_messages_different_streams(self, capsys):
        """Test that stdout and stderr are properly separated."""
        print_message("stdout message")
        print_message("stderr message", file=sys.stderr)
        print_success("another stdout")

        captured = capsys.readouterr()

        # Check stdout contains only stdout messages
        assert "stdout message" in captured.out
        assert "another stdout" in captured.out
        assert "stderr message" not in captured.out

        # Check stderr contains only stderr messages
        assert "stderr message" in captured.err
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
