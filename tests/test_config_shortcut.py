#!/usr/bin/env python3
"""
Tests for `jgo config shortcut` command.

Tests adding, removing, listing, and showing shortcuts via CLI.
"""

import configparser
import tempfile
from pathlib import Path

from jgo.cli._args import ParsedArgs
from jgo.cli._commands import config_shortcut as config_shortcut


class TestConfigShortcut:
    """Test jgo config shortcut command."""

    def test_list_shortcuts_empty(self):
        """Test listing shortcuts when none are configured."""
        args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
        config = {"shortcuts": {}}

        result = config_shortcut.execute(args, config, list_all=True)
        assert result == 0

    def test_list_shortcuts_with_data(self):
        """Test listing shortcuts when some are configured."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            # Create config file with shortcuts
            parser = configparser.ConfigParser()
            parser.add_section("shortcuts")
            parser.set("shortcuts", "repl", "org.scijava:scijava-common@ScriptREPL")
            parser.set("shortcuts", "groovy", "org.scijava:scripting-groovy@GroovySh")

            with open(config_file, "w") as f:
                parser.write(f)

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
            config = {
                "shortcuts": {
                    "repl": "org.scijava:scijava-common@ScriptREPL",
                    "groovy": "org.scijava:scripting-groovy@GroovySh",
                }
            }

            result = config_shortcut.execute(args, config, list_all=True)
            assert result == 0

    def test_show_shortcut(self):
        """Test showing a specific shortcut."""
        args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
        config = {"shortcuts": {"repl": "org.scijava:scijava-common@ScriptREPL"}}

        result = config_shortcut.execute(args, config, name="repl")
        assert result == 0

    def test_show_shortcut_not_found(self):
        """Test showing a shortcut that doesn't exist."""
        args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
        config = {"shortcuts": {}}

        result = config_shortcut.execute(args, config, name="nonexistent")
        assert result == 1

    def test_add_shortcut(self):
        """Test adding a new shortcut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
            config = {"shortcuts": {}}

            result = config_shortcut.execute(
                args,
                config,
                name="repl",
                endpoint="org.scijava:scijava-common@ScriptREPL",
                config_file=config_file,
            )
            assert result == 0

            # Verify shortcut was added
            parser = configparser.ConfigParser()
            parser.read(config_file)
            assert parser.has_section("shortcuts")
            assert (
                parser.get("shortcuts", "repl")
                == "org.scijava:scijava-common@ScriptREPL"
            )

    def test_update_shortcut(self):
        """Test updating an existing shortcut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            # Create config file with existing shortcut
            parser = configparser.ConfigParser()
            parser.add_section("shortcuts")
            parser.set("shortcuts", "repl", "org.scijava:scijava-common@OldClass")

            with open(config_file, "w") as f:
                parser.write(f)

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
            config = {"shortcuts": {"repl": "org.scijava:scijava-common@OldClass"}}

            result = config_shortcut.execute(
                args,
                config,
                name="repl",
                endpoint="org.scijava:scijava-common@ScriptREPL",
                config_file=config_file,
            )
            assert result == 0

            # Verify shortcut was updated
            parser = configparser.ConfigParser()
            parser.read(config_file)
            assert (
                parser.get("shortcuts", "repl")
                == "org.scijava:scijava-common@ScriptREPL"
            )

    def test_remove_shortcut(self):
        """Test removing a shortcut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            # Create config file with shortcuts
            parser = configparser.ConfigParser()
            parser.add_section("shortcuts")
            parser.set("shortcuts", "repl", "org.scijava:scijava-common@ScriptREPL")
            parser.set("shortcuts", "groovy", "org.scijava:scripting-groovy@GroovySh")

            with open(config_file, "w") as f:
                parser.write(f)

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
            config = {
                "shortcuts": {
                    "repl": "org.scijava:scijava-common@ScriptREPL",
                    "groovy": "org.scijava:scripting-groovy@GroovySh",
                }
            }

            result = config_shortcut.execute(
                args, config, remove_name="repl", config_file=config_file
            )
            assert result == 0

            # Verify shortcut was removed
            parser = configparser.ConfigParser()
            parser.read(config_file)
            assert not parser.has_option("shortcuts", "repl")
            # Other shortcut should still be there
            assert parser.has_option("shortcuts", "groovy")

    def test_remove_shortcut_not_found(self):
        """Test removing a shortcut that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            # Create empty config file
            parser = configparser.ConfigParser()
            parser.add_section("shortcuts")

            with open(config_file, "w") as f:
                parser.write(f)

            # Mock Path.home() to use temp directory
            import unittest.mock

            with unittest.mock.patch("pathlib.Path.home", return_value=Path(tmp_dir)):
                args = ParsedArgs(
                    command="config", verbose=0, quiet=False, dry_run=False
                )
                config = {"shortcuts": {}}

                result = config_shortcut.execute(
                    args, config, remove_name="nonexistent"
                )
                assert result == 1

    def test_add_shortcut_dry_run(self):
        """Test adding a shortcut in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=True)
            config = {"shortcuts": {}}

            result = config_shortcut.execute(
                args,
                config,
                name="repl",
                endpoint="org.scijava:scijava-common@ScriptREPL",
                config_file=config_file,
            )
            assert result == 0

            # Verify shortcut was NOT added (dry run)
            assert not config_file.exists()

    def test_remove_last_shortcut_removes_section(self):
        """Test that removing the last shortcut removes the [shortcuts] section."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "config"

            # Create config file with one shortcut
            parser = configparser.ConfigParser()
            parser.add_section("shortcuts")
            parser.set("shortcuts", "repl", "org.scijava:scijava-common@ScriptREPL")

            with open(config_file, "w") as f:
                parser.write(f)

            args = ParsedArgs(command="config", verbose=0, quiet=False, dry_run=False)
            config = {"shortcuts": {"repl": "org.scijava:scijava-common@ScriptREPL"}}

            result = config_shortcut.execute(
                args, config, remove_name="repl", config_file=config_file
            )
            assert result == 0

            # Verify section was removed
            parser = configparser.ConfigParser()
            parser.read(config_file)
            assert not parser.has_section("shortcuts")
