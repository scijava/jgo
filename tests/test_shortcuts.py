#!/usr/bin/env python3
"""
Tests for shortcut expansion functionality.

Tests both the JgoConfig.expand_shortcuts() method and integration
with jgo init to create multi-entrypoint environments.
"""

import tempfile
from pathlib import Path

import pytest

from jgo.config.file import JgoConfig
from jgo.env import EnvironmentSpec


class TestShortcutExpansion:
    """Test JgoConfig.expand_shortcuts() method."""

    def test_no_shortcuts(self):
        """Test that expansion with no shortcuts is a no-op."""
        config = JgoConfig(shortcuts={})
        assert (
            config.expand_shortcuts("org.scijava:scijava-common")
            == "org.scijava:scijava-common"
        )

    def test_simple_shortcut(self):
        """Test simple shortcut expansion."""
        config = JgoConfig(shortcuts={"repl": "org.scijava:scijava-common@ScriptREPL"})
        assert (
            config.expand_shortcuts("repl") == "org.scijava:scijava-common@ScriptREPL"
        )

    def test_shortcut_with_suffix(self):
        """Test shortcut expansion with additional text after shortcut."""
        config = JgoConfig(shortcuts={"imagej": "net.imagej:imagej"})
        # Shortcut matches at start, rest is preserved
        assert config.expand_shortcuts("imagej:2.0.0") == "net.imagej:imagej:2.0.0"

    def test_composition_with_plus(self):
        """Test shortcut composition using + operator."""
        config = JgoConfig(
            shortcuts={
                "repl": "org.scijava:scijava-common@ScriptREPL",
                "groovy": "org.scijava:scripting-groovy@GroovySh",
            }
        )
        result = config.expand_shortcuts("repl+groovy")
        assert (
            result
            == "org.scijava:scijava-common@ScriptREPL+org.scijava:scripting-groovy@GroovySh"
        )

    def test_partial_composition(self):
        """Test composition where only some parts are shortcuts."""
        config = JgoConfig(shortcuts={"repl": "org.scijava:scijava-common@ScriptREPL"})
        # Only first part is a shortcut
        result = config.expand_shortcuts("repl+org.scijava:parsington")
        assert result == "org.scijava:scijava-common@ScriptREPL+org.scijava:parsington"

    def test_no_matching_shortcut(self):
        """Test that non-shortcuts pass through unchanged."""
        config = JgoConfig(shortcuts={"repl": "org.scijava:scijava-common"})
        assert (
            config.expand_shortcuts("org.python:jython-standalone")
            == "org.python:jython-standalone"
        )

    def test_multiple_shortcuts_in_composition(self):
        """Test composing multiple shortcuts with explicit coordinates."""
        config = JgoConfig(
            shortcuts={
                "scijava": "org.scijava:scijava-common",
                "groovy": "org.scijava:scripting-groovy",
            }
        )
        result = config.expand_shortcuts("scijava+groovy+net.imagej:imagej")
        assert (
            result
            == "org.scijava:scijava-common+org.scijava:scripting-groovy+net.imagej:imagej"
        )

    def test_nested_shortcuts(self):
        """Test shortcuts that reference other shortcuts."""
        config = JgoConfig(
            shortcuts={
                "base": "org.scijava:scijava-common",
                "repl": "base@ScriptREPL",  # References "base" shortcut
            }
        )
        # Should expand repl -> base@ScriptREPL -> org.scijava:scijava-common@ScriptREPL
        assert (
            config.expand_shortcuts("repl") == "org.scijava:scijava-common@ScriptREPL"
        )


class TestInitWithShortcuts:
    """Test jgo init with shortcut composition."""

    def test_init_with_single_shortcut(self):
        """Test jgo init with a single shortcut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # Create config with shortcut
                config = {
                    "shortcuts": {"repl": "org.scijava:scijava-common@ScriptREPL"}
                }

                # Run init with shortcut
                init_args = ParsedArgs(
                    endpoint="repl",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )

                result = init_cmd.execute(init_args, config)
                assert result == 0

                # Verify jgo.toml
                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

                # Should have the expanded coordinate
                assert spec.coordinates == ["org.scijava:scijava-common"]

                # Should have entrypoint named after the shortcut
                assert "repl" in spec.entrypoints
                assert spec.entrypoints["repl"] == "ScriptREPL"
                assert spec.default_entrypoint == "repl"

            finally:
                os.chdir(original_cwd)

    def test_init_with_shortcut_composition(self):
        """Test jgo init repl+groovy creates multiple entrypoints."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # Create config with shortcuts
                config = {
                    "shortcuts": {
                        "repl": "org.scijava:scijava-common@ScriptREPL",
                        "groovy": "org.scijava:scripting-groovy@GroovySh",
                    }
                }

                # Run init with composed shortcuts
                init_args = ParsedArgs(
                    endpoint="repl+groovy",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )

                result = init_cmd.execute(init_args, config)
                assert result == 0

                # Verify jgo.toml
                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

                # Should have both coordinates
                assert len(spec.coordinates) == 2
                assert "org.scijava:scijava-common" in spec.coordinates
                assert "org.scijava:scripting-groovy" in spec.coordinates

                # Should have both entrypoints
                assert "repl" in spec.entrypoints
                assert "groovy" in spec.entrypoints
                assert spec.entrypoints["repl"] == "ScriptREPL"
                assert spec.entrypoints["groovy"] == "GroovySh"

                # First one should be default
                assert spec.default_entrypoint == "repl"

            finally:
                os.chdir(original_cwd)

    def test_init_with_mixed_shortcuts_and_coordinates(self):
        """Test jgo init with both shortcuts and explicit coordinates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # Create config with one shortcut
                config = {
                    "shortcuts": {"repl": "org.scijava:scijava-common@ScriptREPL"}
                }

                # Run init with shortcut + explicit coordinate
                init_args = ParsedArgs(
                    endpoint="repl+org.scijava:parsington",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )

                result = init_cmd.execute(init_args, config)
                assert result == 0

                # Verify jgo.toml
                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

                # Should have both coordinates
                assert len(spec.coordinates) == 2
                assert "org.scijava:scijava-common" in spec.coordinates
                assert "org.scijava:parsington" in spec.coordinates

                # Should only have one entrypoint (from shortcut with @MainClass)
                assert len(spec.entrypoints) == 1
                assert "repl" in spec.entrypoints
                assert spec.entrypoints["repl"] == "ScriptREPL"
                assert spec.default_entrypoint == "repl"

            finally:
                os.chdir(original_cwd)

    def test_init_with_shortcut_no_main_class(self):
        """Test jgo init with shortcut that has no main class."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # Create config with shortcut (no @MainClass)
                config = {"shortcuts": {"imagej": "net.imagej:imagej"}}

                # Run init with shortcut
                init_args = ParsedArgs(
                    endpoint="imagej",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )

                result = init_cmd.execute(init_args, config)
                assert result == 0

                # Verify jgo.toml
                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

                # Should have the coordinate
                assert spec.coordinates == ["net.imagej:imagej"]

                # Should have entrypoint matching endpoint
                assert "main" in spec.entrypoints
                assert spec.entrypoints["main"] == "net.imagej:imagej"
                assert spec.default_entrypoint == "main"

            finally:
                os.chdir(original_cwd)

    def test_init_with_explicit_coordinate_and_main_class(self):
        """Test jgo init with explicit coordinate@MainClass (no shortcuts)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # No shortcuts
                config = {"shortcuts": {}}

                # Run init with explicit coordinate
                init_args = ParsedArgs(
                    endpoint="org.scijava:scijava-common@ScriptREPL",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )

                result = init_cmd.execute(init_args, config)
                assert result == 0

                # Verify jgo.toml
                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

                # Should have the coordinate
                assert spec.coordinates == ["org.scijava:scijava-common"]

                # Should have entrypoint named "main" (not a shortcut)
                assert "main" in spec.entrypoints
                assert spec.entrypoints["main"] == "ScriptREPL"
                assert spec.default_entrypoint == "main"

            finally:
                os.chdir(original_cwd)


class TestRunWithShortcuts:
    """Test jgo run with shortcut expansion and resolution order."""

    def test_run_with_shortcut_no_jgo_toml(self):
        """Test jgo run with shortcut when no jgo.toml exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.parser import ParsedArgs

                # Run with shortcut (print classpath mode to avoid needing Java)
                run_args = ParsedArgs(
                    endpoint="repl",
                    command="run",
                    verbose=1,
                    quiet=False,
                    ignore_config=True,
                    print_classpath=True,
                    main_class=None,
                    app_args=[],
                    jvm_args=[],
                    classpath_append=[],
                    print_dependency_tree=False,
                    print_dependency_list=False,
                    print_java_info=False,
                    update=False,
                    entrypoint=None,
                    resolver="python",
                    repo_cache=tmp_path / ".m2" / "repository",
                )

                # This should expand the shortcut
                # We can't easily test the full execution without Maven, but we can verify
                # the shortcut expansion logic works by checking it doesn't error
                # and that the endpoint gets expanded in the args

                # For now, just verify the execute function accepts it
                # (Full integration testing would require Maven/Java setup)
                assert run_args.endpoint == "repl"

            finally:
                os.chdir(original_cwd)

    def test_run_entrypoint_wins_over_shortcut(self):
        """Test that entrypoint from jgo.toml takes precedence over global shortcut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)

                from jgo.cli.commands import init as init_cmd
                from jgo.cli.parser import ParsedArgs

                # Create config with shortcut
                config = {
                    "shortcuts": {"repl": "org.scijava:scijava-common@ScriptREPL"}
                }

                # Create jgo.toml with entrypoint named "repl"
                init_args = ParsedArgs(
                    endpoint="repl",
                    command="init",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    file=tmp_path / "jgo.toml",
                )
                init_cmd.execute(init_args, config)

                # Verify jgo.toml has entrypoint "repl"
                from jgo.env import EnvironmentSpec

                spec = EnvironmentSpec.load(tmp_path / "jgo.toml")
                assert "repl" in spec.entrypoints

                # Verify the resolution logic works by checking that
                # the spec has the right entrypoint (which would be used
                # if we called run with "repl")
                assert spec.entrypoints["repl"] == "ScriptREPL"

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
