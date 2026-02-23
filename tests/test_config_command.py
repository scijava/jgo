#!/usr/bin/env python3
"""
Unit tests for config CLI command.
"""

import configparser
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from jgo.cli._args import ParsedArgs
from jgo.cli._commands import config as config_cmd


def test_config_list_jgorc():
    """Test listing config from .jgorc file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".jgorc"

        # Create a sample .jgorc file
        parser = configparser.ConfigParser()
        parser.add_section("settings")
        parser.set("settings", "cache_dir", "~/.cache/jgo")
        parser.set("settings", "links", "auto")
        parser.add_section("repositories")
        parser.set("repositories", "central", "https://repo.maven.apache.org/maven2")

        with open(config_file, "w") as f:
            parser.write(f)

        # Test listing
        args = ParsedArgs(verbose=0, dry_run=False)
        exit_code = config_cmd.execute(
            args,
            {},
            key=None,
            value=None,
            unset=None,
            list_all=True,
            global_config=True,
            local_config=False,
        )

        # Temporarily patch the config file location
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(tmpdir)
            exit_code = config_cmd._list_jgorc(config_file, args)

        assert exit_code == 0


def test_config_get_value():
    """Test getting a specific config value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".jgorc"

        # Create a sample .jgorc file
        parser = configparser.ConfigParser()
        parser.add_section("settings")
        parser.set("settings", "cache_dir", "~/.cache/jgo")

        with open(config_file, "w") as f:
            parser.write(f)

        # Test getting value
        args = ParsedArgs(verbose=0, dry_run=False)
        exit_code = config_cmd._get_jgorc(config_file, "settings", "cache_dir", args)

        assert exit_code == 0


def test_config_set_value():
    """Test setting a config value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".jgorc"

        # Test setting value
        args = ParsedArgs(verbose=0, dry_run=False)
        exit_code = config_cmd._set_jgorc(
            config_file, "settings", "cache_dir", "~/.jgo", args
        )

        assert exit_code == 0

        # Verify value was set
        parser = configparser.ConfigParser()
        parser.read(config_file)
        assert parser.get("settings", "cache_dir") == "~/.jgo"


def test_config_unset_value():
    """Test unsetting a config value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".jgorc"

        # Create a sample .jgorc file
        parser = configparser.ConfigParser()
        parser.add_section("settings")
        parser.set("settings", "cache_dir", "~/.cache/jgo")
        parser.set("settings", "links", "auto")

        with open(config_file, "w") as f:
            parser.write(f)

        # Test unsetting value
        args = ParsedArgs(verbose=0, dry_run=False)
        exit_code = config_cmd._unset_jgorc(config_file, "settings", "cache_dir", args)

        assert exit_code == 0

        # Verify value was unset
        parser = configparser.ConfigParser()
        parser.read(config_file)
        assert not parser.has_option("settings", "cache_dir")
        assert parser.has_option("settings", "links")


def test_config_parse_value():
    """Test parsing values to correct types."""
    # Test bool
    assert config_cmd._parse_value("true") is True
    assert config_cmd._parse_value("True") is True
    assert config_cmd._parse_value("false") is False
    assert config_cmd._parse_value("False") is False

    # Test int
    assert config_cmd._parse_value("42") == 42
    assert config_cmd._parse_value("-10") == -10

    # Test float
    assert config_cmd._parse_value("3.14") == 3.14
    assert config_cmd._parse_value("-2.5") == -2.5

    # Test string
    assert config_cmd._parse_value("hello") == "hello"
    assert config_cmd._parse_value("auto") == "auto"


def test_config_toml_operations():
    """Test config operations on TOML files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "jgo.toml"

        # Create a sample jgo.toml file
        data = {
            "settings": {"cache_dir": ".jgo", "links": "auto"},
            "repositories": {"central": "https://repo.maven.apache.org/maven2"},
        }

        with open(config_file, "wb") as f:
            tomli_w.dump(data, f)

        # Test getting value
        args = ParsedArgs(verbose=0, dry_run=False)
        exit_code = config_cmd._get_toml(config_file, "settings", "cache_dir", args)
        assert exit_code == 0

        # Test setting value
        exit_code = config_cmd._set_toml(
            config_file, "settings", "cache_dir", ".cache/jgo", args
        )
        assert exit_code == 0

        # Verify value was set
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        assert data["settings"]["cache_dir"] == ".cache/jgo"


def test_config_integration_global_and_local_conflict():
    """Test that using both --global and --local returns error."""
    args = ParsedArgs(verbose=0, dry_run=False)

    exit_code = config_cmd.execute(
        args,
        {},
        key="cache_dir",
        value="~/.jgo",
        unset=None,
        list_all=False,
        global_config=True,
        local_config=True,
    )

    assert exit_code == 1
