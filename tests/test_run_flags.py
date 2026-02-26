"""
Tests for --global, --local, and --main-class flags in jgo run.

Covers:
  - execute() routing: --global bypasses jgo.toml even when it exists
  - execute() routing: jgo.toml without endpoint → spec mode
  - --local flag: a positional click mis-assigns as endpoint → moved to app_args
  - --main-class priority: CLI override wins over spec's configured main class
"""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from jgo.cli._args import ParsedArgs
from jgo.cli._commands.run import _run_spec, execute

# Minimal jgo.toml for tests that need spec mode
_SPEC_TOML = """\
[environment]
name = "test"

[dependencies]
coordinates = ["org.python:jython-standalone:2.7.4"]

[entrypoints]
main = "org.python.util.jython"
default = "main"
"""


# ---------------------------------------------------------------------------
# execute() routing
# ---------------------------------------------------------------------------


class TestExecuteRouting:
    """execute() should route to _run_spec or _run_endpoint based on flags/state."""

    def test_endpoint_no_jgo_toml_goes_to_endpoint_mode(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = ParsedArgs(
            endpoint="org.python:jython-standalone:2.7.4", ignore_config=True
        )
        with patch("jgo.cli._commands.run._run_endpoint", return_value=0) as ep:
            with patch("jgo.cli._commands.run._run_spec") as sp:
                execute(args, {})
        ep.assert_called_once()
        sp.assert_not_called()

    def test_jgo_toml_no_endpoint_goes_to_spec_mode(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "jgo.toml").write_text(_SPEC_TOML)
        args = ParsedArgs(endpoint=None, ignore_config=True)
        with patch("jgo.cli._commands.run._run_endpoint") as ep:
            with patch("jgo.cli._commands.run._run_spec", return_value=0) as sp:
                execute(args, {})
        sp.assert_called_once()
        ep.assert_not_called()

    def test_global_bypasses_jgo_toml_with_endpoint(self, tmp_path, monkeypatch):
        """--global routes to endpoint mode even when jgo.toml exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "jgo.toml").write_text(_SPEC_TOML)
        args = ParsedArgs(
            endpoint="org.python:jython-standalone:2.7.4",
            force_global=True,
            ignore_config=True,
        )
        with patch("jgo.cli._commands.run._run_endpoint", return_value=0) as ep:
            with patch("jgo.cli._commands.run._run_spec") as sp:
                execute(args, {})
        ep.assert_called_once()
        sp.assert_not_called()

    def test_global_bypasses_jgo_toml_without_endpoint(self, tmp_path, monkeypatch):
        """--global routes to endpoint mode even with no endpoint (will error there)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "jgo.toml").write_text(_SPEC_TOML)
        args = ParsedArgs(endpoint=None, force_global=True, ignore_config=True)
        with patch("jgo.cli._commands.run._run_endpoint", return_value=1) as ep:
            with patch("jgo.cli._commands.run._run_spec") as sp:
                execute(args, {})
        ep.assert_called_once()
        sp.assert_not_called()


# ---------------------------------------------------------------------------
# --local flag: CLI callback behaviour
# ---------------------------------------------------------------------------


class TestLocalFlag:
    """--local forces spec mode; any positional captured as endpoint → app_args."""

    def _invoke(self, tmp_path, args: list[str]):
        """Invoke the jgo CLI via CliRunner from tmp_path."""
        from jgo.cli._parser import cli

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("jgo.toml").write_text(_SPEC_TOML)
            result = runner.invoke(cli, args, catch_exceptions=False)
        return result

    def test_local_moves_positional_to_app_args(self, tmp_path) -> None:
        """
        Simulate `jgo run --local --main-class Foo -- script.groovy`:
        click consumes '--' and puts 'script.groovy' in the endpoint slot;
        --local should move it back to app_args.
        """
        with patch("jgo.cli._commands.run._run_spec", return_value=0) as mock_spec:
            result = self._invoke(
                tmp_path,
                [
                    "--ignore-config",
                    "run",
                    "--local",
                    "--main-class",
                    "org.python.util.jython",
                    "script.groovy",
                ],
            )

        assert result.exit_code == 0
        passed_args: ParsedArgs = mock_spec.call_args[0][0]
        assert passed_args.endpoint is None, "endpoint should be cleared by --local"
        assert "script.groovy" in passed_args.app_args
        assert passed_args.main_class == "org.python.util.jython"

    def test_local_with_explicit_dash_dash(self, tmp_path) -> None:
        """
        `jgo run --local -- script.groovy` (no --main-class):
        endpoint should be None, app_args should contain script.groovy.
        """
        with patch("jgo.cli._commands.run._run_spec", return_value=0) as mock_spec:
            result = self._invoke(
                tmp_path,
                ["--ignore-config", "run", "--local", "--", "script.groovy"],
            )

        assert result.exit_code == 0
        passed_args: ParsedArgs = mock_spec.call_args[0][0]
        assert passed_args.endpoint is None
        assert "script.groovy" in passed_args.app_args

    def test_local_no_extra_args(self, tmp_path):
        """--local with no positional args still runs in spec mode."""
        with patch("jgo.cli._commands.run._run_spec", return_value=0) as mock_spec:
            result = self._invoke(
                tmp_path,
                ["--ignore-config", "run", "--local"],
            )

        assert result.exit_code == 0
        mock_spec.assert_called_once()


# ---------------------------------------------------------------------------
# --main-class priority in spec mode
# ---------------------------------------------------------------------------


class TestMainClassPriorityInSpecMode:
    """CLI --main-class should override the spec's configured main class."""

    def test_main_class_overrides_spec_entrypoint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "jgo.toml").write_text(_SPEC_TOML)

        args = ParsedArgs(
            endpoint=None,
            main_class="org.python.util.PyConsole",  # CLI override
            ignore_config=True,
        )

        mock_runner = MagicMock()
        mock_runner.run.return_value = CompletedProcess([], 0)

        mock_env = MagicMock()
        # Spec's configured class — should be overridden
        mock_env.get_main_class.return_value = "org.python.util.jython"

        with patch(
            "jgo.cli._commands.run.create_java_runner", return_value=mock_runner
        ):
            with patch(
                "jgo.cli._commands.run.create_environment_builder"
            ) as mock_builder_factory:
                mock_builder = MagicMock()
                mock_builder.from_spec.return_value = mock_env
                mock_builder_factory.return_value = mock_builder

                _run_spec(args, {})

        call_kwargs = mock_runner.run.call_args[1]
        assert call_kwargs["main_class"] == "org.python.util.PyConsole", (
            "--main-class CLI override should take priority over spec's configured class"
        )

    def test_spec_entrypoint_used_when_no_main_class_flag(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "jgo.toml").write_text(_SPEC_TOML)

        args = ParsedArgs(
            endpoint=None,
            main_class=None,  # No CLI override
            ignore_config=True,
        )

        mock_runner = MagicMock()
        mock_runner.run.return_value = CompletedProcess([], 0)

        mock_env = MagicMock()
        mock_env.get_main_class.return_value = "org.python.util.jython"

        with patch(
            "jgo.cli._commands.run.create_java_runner", return_value=mock_runner
        ):
            with patch(
                "jgo.cli._commands.run.create_environment_builder"
            ) as mock_builder_factory:
                mock_builder = MagicMock()
                mock_builder.from_spec.return_value = mock_env
                mock_builder_factory.return_value = mock_builder

                _run_spec(args, {})

        call_kwargs = mock_runner.run.call_args[1]
        assert call_kwargs["main_class"] == "org.python.util.jython"
