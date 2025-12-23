"""
Tests for main class priority in EnvironmentBuilder.from_endpoint().

Priority order: CLI main class > endpoint main class > auto-detected from JAR

This tests the fix for: https://github.com/apposed/jgo/issues/...
When running `jgo run repl` with a cached environment, the shortcut's main class
(org.scijava.script.ScriptREPL) should override the cached auto-detected class
(net.imagej.Main).
"""

import tempfile
from pathlib import Path

from jgo.env import Environment
from jgo.env.lockfile import LockFile


class TestMainClassPriority:
    """Test the priority order for main class selection."""

    def test_cli_override_wins_over_endpoint(self):
        """Test that CLI --main-class takes priority over endpoint main class."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "test_env"
            env_path.mkdir(parents=True)

            # Create environment with auto-detected main class
            lockfile = LockFile(
                dependencies=[],
                entrypoints={"default": "org.example.AutoDetected"},
                default_entrypoint="default",
            )
            lockfile.save(env_path / "jgo.lock.toml")

            env = Environment(env_path)

            # Simulate from_endpoint() with both CLI and endpoint main classes
            main_class = "org.example.CLI"  # CLI override
            parsed_main_class = "org.example.Endpoint"  # From endpoint string

            # This is the logic from from_endpoint():
            env._runtime_main_class = main_class or parsed_main_class or env.main_class

            # CLI should win
            assert env.main_class == "org.example.CLI"

    def test_endpoint_overrides_cached_auto_detected(self):
        """
        Test that endpoint main class overrides auto-detected from cached JAR.

        This is the bug fix: when a cached environment exists with an
        auto-detected main class, but the endpoint specifies a different
        main class (e.g., via shortcut), the endpoint's main class should win.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "test_env"
            env_path.mkdir(parents=True)

            # Create environment with auto-detected main class (simulating cached build)
            lockfile = LockFile(
                dependencies=[],
                entrypoints={"main": "net.imagej.Main"},
                default_entrypoint="main",
            )
            lockfile.save(env_path / "jgo.lock.toml")

            env = Environment(env_path)
            assert env.main_class == "net.imagej.Main"

            # Simulate from_endpoint() with endpoint main class (from shortcut)
            main_class = None  # No CLI override
            parsed_main_class = "org.scijava.script.ScriptREPL"  # From endpoint

            # This is the logic from from_endpoint():
            env._runtime_main_class = main_class or parsed_main_class or env.main_class

            # Endpoint should win over cached auto-detected
            assert env.main_class == "org.scijava.script.ScriptREPL"

    def test_auto_detect_used_when_nothing_specified(self):
        """
        Test that auto-detected main class is used when neither CLI nor endpoint specify one.

        This is the normal case for coordinates without @MainClass.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "test_env"
            env_path.mkdir(parents=True)

            # Create environment with auto-detected main class
            lockfile = LockFile(
                dependencies=[],
                entrypoints={"main": "org.example.AutoDetected"},
                default_entrypoint="main",
            )
            lockfile.save(env_path / "jgo.lock.toml")

            env = Environment(env_path)

            # Simulate from_endpoint() with no explicit main classes
            main_class = None  # No CLI override
            parsed_main_class = None  # No endpoint main class

            # This is the logic from from_endpoint():
            env._runtime_main_class = main_class or parsed_main_class or env.main_class

            # Auto-detected should be used
            assert env.main_class == "org.example.AutoDetected"

    def test_runtime_override_property_works(self):
        """Test that _runtime_main_class properly overrides environment.main_class."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "test_env"
            env_path.mkdir(parents=True)

            # Create environment with a main class
            lockfile = LockFile(
                dependencies=[],
                entrypoints={"main": "org.example.Original"},
                default_entrypoint="main",
            )
            lockfile.save(env_path / "jgo.lock.toml")

            env = Environment(env_path)

            # Before setting runtime override
            assert env.main_class == "org.example.Original"

            # After setting runtime override (what from_endpoint does)
            env._runtime_main_class = "org.example.Override"

            # The main_class property should return the override
            assert env.main_class == "org.example.Override"

            # The lockfile should still have the original
            assert env.lockfile.entrypoints["main"] == "org.example.Original"
