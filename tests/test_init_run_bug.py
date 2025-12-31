#!/usr/bin/env python3
"""
Regression test for bug: jgo run --main-class doesn't work after jgo init

When running `jgo init <endpoint>` followed by `jgo run --main-class <class>`,
the main class should be passed through to the runner properly.
"""

import tempfile
from pathlib import Path

import pytest

from jgo.cli.commands import run as run_cmd
from jgo.cli.parser import ParsedArgs


def test_run_with_main_class_after_init():
    """
    Test that jgo run --main-class works after jgo init.

    Reproduces the bug:
        $ jgo init org.scijava:scijava-common
        $ jgo run --main-class org.scijava.script.ScriptREPL
        RuntimeError: No main class specified.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Change to temp directory to simulate project mode
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Initialize environment
            init_args = ParsedArgs(
                endpoint="org.scijava:scijava-common",
                command="init",
                verbose=0,
                quiet=False,
                ignore_config=True,
                file=tmp_path / "jgo.toml",
            )

            from jgo.cli.commands import init as init_cmd

            result = init_cmd.execute(init_args, {})
            assert result == 0

            # Verify jgo.toml was created
            assert (tmp_path / "jgo.toml").exists()

            # Step 2: Build the environment first (to avoid needing Java runtime)
            # This simulates what happens when you run jgo without --print-classpath
            from jgo.env import EnvironmentBuilder, EnvironmentSpec
            from jgo.maven import MavenContext, PythonResolver

            spec = EnvironmentSpec.load(tmp_path / "jgo.toml")
            context = MavenContext(
                resolver=PythonResolver(),
                repo_cache=tmp_path / ".m2" / "repository",
            )
            builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")
            # Build environment (we don't need to use it, just ensure it's created)
            builder.from_spec(spec, update=False)

            # Step 3: Now test that runner.run() gets the main_class
            # Mock the runner to check if main_class is passed correctly
            from unittest.mock import Mock, patch

            from jgo.exec import JavaRunner

            mock_runner = Mock(spec=JavaRunner)

            # Patch create_java_runner to return our mock
            with patch("jgo.cli.context.create_java_runner", return_value=mock_runner):
                run_args = ParsedArgs(
                    endpoint=None,  # No endpoint - should use jgo.toml
                    command="run",
                    verbose=0,
                    quiet=False,
                    ignore_config=True,
                    main_class="org.scijava.script.ScriptREPL",
                    app_args=[],
                    jvm_args=[],
                    classpath_append=[],
                    update=False,
                    entrypoint=None,
                    resolver="python",
                    repo_cache=tmp_path / ".m2" / "repository",
                    cache_dir=tmp_path / ".jgo",  # Use temp directory for cache
                )

                # Mock the run method to return success
                from subprocess import CompletedProcess

                mock_runner.run.return_value = CompletedProcess([], 0)

                result = run_cmd._run_spec(run_args, {})

                # Verify that runner.run() was called with main_class parameter
                mock_runner.run.assert_called_once()
                call_kwargs = mock_runner.run.call_args[1]

                # The bug: main_class is NOT passed to runner.run() in spec mode
                # After fix: main_class should be passed as a keyword argument
                if "main_class" not in call_kwargs:
                    pytest.fail(
                        "Bug confirmed: main_class not passed to runner.run() in spec mode. "
                        f"Called with: {call_kwargs}"
                    )

                # Verify the correct main class was passed
                assert call_kwargs["main_class"] == "org.scijava.script.ScriptREPL"
                assert result == 0

        finally:
            os.chdir(original_cwd)


def test_run_endpoint_with_main_class():
    """
    Test that jgo run --main-class works with direct endpoint (baseline test).

    This should work both before and after the fix.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        run_args = ParsedArgs(
            endpoint="org.scijava:scijava-common",
            command="run",
            verbose=0,
            quiet=False,
            ignore_config=True,
            main_class="org.scijava.script.ScriptREPL",
            app_args=[],
            jvm_args=[],
            classpath_append=[],
            update=False,
            entrypoint=None,
            resolver="python",
            repo_cache=tmp_path / ".m2" / "repository",
            cache_dir=tmp_path / ".jgo",  # Use temp directory for cache
        )

        # This should work (baseline)
        try:
            run_cmd._run_endpoint(run_args, {})
            # Success - endpoint mode passes main_class correctly
        except RuntimeError as e:
            if "No main class specified" in str(e):
                pytest.fail(f"Endpoint mode broken: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
