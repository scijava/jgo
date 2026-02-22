#!/usr/bin/env python3
"""
Test for bug: jgo add fails after jgo init with @MainClass

When running `jgo init <endpoint>@MainClass` followed by `jgo add <dependency>`,
the sync should work without trying to resolve the main class as part of the coordinate.

Reproduces the bug:
    $ jgo init org.scijava:scijava-common@ScriptREPL
    $ jgo add org.scijava:scripting-groovy
    Error: Failed to build environment: Could not resolve RELEASE version for org.scijava:scijava-common@ScriptREPL
"""

import tempfile
from pathlib import Path

import pytest

from jgo.cli._args import ParsedArgs


def test_init_with_main_class_then_add():
    """
    Test that jgo add works after jgo init with @MainClass in the endpoint.

    This verifies that the main class is properly separated from the coordinate
    during init, so subsequent operations don't try to resolve it as part of
    the Maven coordinate.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Change to temp directory to simulate project mode
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Initialize environment with @MainClass
            init_args = ParsedArgs(
                endpoint="org.scijava:scijava-common:2.97.1@ScriptREPL",
                command="init",
                verbose=0,
                quiet=False,
                ignore_config=True,
                file=tmp_path / "jgo.toml",
            )

            from jgo.cli.commands import _init as init_cmd

            result = init_cmd.execute(init_args, {})
            assert result == 0

            # Verify jgo.toml was created
            assert (tmp_path / "jgo.toml").exists()

            # Verify the coordinate and entrypoint are correct
            from jgo.env import EnvironmentSpec

            spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

            # The coordinate should NOT include @ScriptREPL
            assert spec.coordinates == ["org.scijava:scijava-common:2.97.1"]

            # The main class should be in entrypoints
            assert "main" in spec.entrypoints
            assert spec.entrypoints["main"] == "ScriptREPL"
            assert spec.default_entrypoint == "main"

            # Step 2: Add another dependency
            add_args = ParsedArgs(
                command="add",
                verbose=0,
                quiet=False,
                ignore_config=True,
                file=tmp_path / "jgo.toml",
                repo_cache=tmp_path / ".m2" / "repository",
                dry_run=False,
            )
            add_args.coordinates = ["org.scijava:scripting-groovy"]
            add_args.no_sync = True  # Don't sync for this test (would need Maven)

            from jgo.cli.commands import _add as add_cmd

            result = add_cmd.execute(add_args, {})
            assert result == 0

            # Verify both coordinates are in the spec
            spec = EnvironmentSpec.load(tmp_path / "jgo.toml")
            assert len(spec.coordinates) == 2
            assert "org.scijava:scijava-common:2.97.1" in spec.coordinates
            assert "org.scijava:scripting-groovy" in spec.coordinates

            # Entrypoint should still be there
            assert spec.entrypoints["main"] == "ScriptREPL"

        finally:
            os.chdir(original_cwd)


def test_init_without_main_class():
    """
    Test that jgo init without @MainClass creates a coordinate reference entrypoint.

    New behavior: jgo init org.scijava:scijava-common creates an entrypoint
    with coordinate reference for inference at build time.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Initialize environment without @MainClass
            init_args = ParsedArgs(
                endpoint="org.scijava:scijava-common:2.97.1",
                command="init",
                verbose=0,
                quiet=False,
                ignore_config=True,
                file=tmp_path / "jgo.toml",
            )

            from jgo.cli.commands import _init as init_cmd

            result = init_cmd.execute(init_args, {})
            assert result == 0

            # Verify the spec
            from jgo.env import EnvironmentSpec

            spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

            # Should have coordinate
            assert spec.coordinates == ["org.scijava:scijava-common:2.97.1"]

            # Should have entrypoint with coordinate reference (new behavior)
            assert spec.entrypoints == {"main": "org.scijava:scijava-common:2.97.1"}
            assert spec.default_entrypoint == "main"

        finally:
            os.chdir(original_cwd)


def test_init_with_old_format_main_class():
    """
    Test that jgo init handles old format :@MainClass.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Initialize with old format coord:@MainClass
            init_args = ParsedArgs(
                endpoint="org.scijava:scijava-common:2.97.1:@ScriptREPL",
                command="init",
                verbose=0,
                quiet=False,
                ignore_config=True,
                file=tmp_path / "jgo.toml",
            )

            from jgo.cli.commands import _init as init_cmd

            result = init_cmd.execute(init_args, {})
            assert result == 0

            # Verify the spec
            from jgo.env import EnvironmentSpec

            spec = EnvironmentSpec.load(tmp_path / "jgo.toml")

            # Coordinate should not have :@ScriptREPL
            assert spec.coordinates == ["org.scijava:scijava-common:2.97.1"]

            # Main class should have @ prefix (old format)
            assert spec.entrypoints["main"] == "@ScriptREPL"

        finally:
            os.chdir(original_cwd)


def test_cached_environment_uses_entrypoint():
    """
    Test that cached environments still use the entrypoint from spec.

    When an environment is already built and cached, subsequent runs should
    still properly use the main class from the entrypoint.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create a spec with an entrypoint
            from jgo.env import EnvironmentSpec

            spec = EnvironmentSpec(
                name="test-env",
                description="Test environment",
                coordinates=["org.scijava:scijava-common:2.97.1"],
                entrypoints={"main": "ScriptREPL"},
                default_entrypoint="main",
                cache_dir=".jgo",
            )

            spec_file = tmp_path / "jgo.toml"
            spec.save(spec_file)

            # Build environment the first time
            from jgo.env import EnvironmentBuilder
            from jgo.maven import MavenContext, PythonResolver

            context = MavenContext(
                resolver=PythonResolver(),
                repo_cache=tmp_path / ".m2" / "repository",
            )

            builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")

            # First build (not cached)
            env1 = builder.from_spec(spec, update=False)
            assert env1.main_class is not None
            main_class_first = env1.main_class

            # Second build (should use cache)
            env2 = builder.from_spec(spec, update=False)
            assert env2.main_class is not None
            assert env2.main_class == main_class_first

        finally:
            os.chdir(original_cwd)


def test_sync_with_multiple_classifiers():
    """
    Test that syncing with multiple dependencies having same G:A:V but different classifiers works.

    This is a regression test for a bug where artifacts with the same groupId, artifactId,
    and version but different classifiers would collide during the sync/linking phase,
    causing only one to be linked to the cache directory.

    The bug was in two places:
    1. The resolver's component_coords set used (G, A, V) tuples
    2. The builder's processed set used (G, A, V) tuples

    Both needed to include classifier and packaging: (G, A, V, C, P)

    Uses LWJGL which publishes native JARs for multiple platforms with different classifiers.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create a spec with two LWJGL native dependencies (different classifiers)
            from jgo.env import EnvironmentSpec

            spec = EnvironmentSpec(
                name="test-multi-classifier",
                description="Test multiple classifiers",
                coordinates=[
                    "org.lwjgl:lwjgl:3.3.1:natives-linux",
                    "org.lwjgl:lwjgl:3.3.1:natives-windows",
                ],
                entrypoints={"main": "org.lwjgl:lwjgl:3.3.1:natives-linux"},
                default_entrypoint="main",
                cache_dir=".jgo",
            )

            spec_file = tmp_path / "jgo.toml"
            spec.save(spec_file)

            # Build environment
            from jgo.env import EnvironmentBuilder
            from jgo.maven import MavenContext, PythonResolver

            context = MavenContext(
                resolver=PythonResolver(),
                repo_cache=tmp_path / ".m2" / "repository",
            )

            builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")
            env = builder.from_spec(spec, update=False)
            assert env is not None

            # Verify lockfile has both dependencies
            from jgo.env._lockfile import LockFile

            lock = LockFile.load(tmp_path / ".jgo" / "jgo.lock.toml")
            locked_coords = {
                (dep.groupId, dep.artifactId, dep.version, dep.classifier)
                for dep in lock.dependencies
            }
            assert ("org.lwjgl", "lwjgl", "3.3.1", "natives-linux") in locked_coords, (
                "natives-linux not in lockfile"
            )
            assert (
                "org.lwjgl",
                "lwjgl",
                "3.3.1",
                "natives-windows",
            ) in locked_coords, "natives-windows not in lockfile"

            # Verify both JARs are present in the cache directory
            cache_dir = tmp_path / ".jgo"
            jar_files = list(cache_dir.rglob("lwjgl-3.3.1-natives-*.jar"))
            assert len(jar_files) == 2, (
                f"Expected 2 JAR files, found {len(jar_files)}: {jar_files}. "
                "This indicates a classifier collision bug."
            )

            # Verify specific filenames
            jar_names = {jar.name for jar in jar_files}
            assert "lwjgl-3.3.1-natives-linux.jar" in jar_names
            assert "lwjgl-3.3.1-natives-windows.jar" in jar_names

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
