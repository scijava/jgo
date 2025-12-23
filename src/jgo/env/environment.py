"""
Environment class for jgo.

An environment is a materialized directory containing JAR files ready for
execution.
"""

from __future__ import annotations

from pathlib import Path

from .bytecode import detect_environment_java_version
from .lockfile import LockFile
from .spec import EnvironmentSpec


class Environment:
    """
    A materialized Maven environment - a directory containing JARs.

    Environment metadata is stored in jgo.lock.toml (entrypoints, min_java_version,
    link_strategy, resolved dependencies with checksums).
    """

    def __init__(self, path: Path):
        self.path = path
        self._lockfile = None
        self._runtime_main_class = None  # Runtime override, not persisted

    @property
    def spec_path(self) -> Path:
        """Path to jgo.toml file in this environment."""
        return self.path / "jgo.toml"

    @property
    def lock_path(self) -> Path:
        """Path to jgo.lock.toml file in this environment."""
        return self.path / "jgo.lock.toml"

    @property
    def spec(self) -> EnvironmentSpec | None:
        """
        Load the environment specification (jgo.toml) if it exists.

        Returns:
            EnvironmentSpec instance, or None if jgo.toml doesn't exist
        """
        if self.spec_path.exists():
            return EnvironmentSpec.load(self.spec_path)
        return None

    @property
    def lockfile(self) -> LockFile | None:
        """
        Load the lock file (jgo.lock.toml) if it exists.

        Returns:
            LockFile instance, or None if jgo.lock.toml doesn't exist
        """
        if self._lockfile is None and self.lock_path.exists():
            self._lockfile = LockFile.load(self.lock_path)
        return self._lockfile

    @property
    def classpath(self) -> list[Path]:
        """List of JAR files in this environment."""
        jars_dir = self.path / "jars"
        if not jars_dir.exists():
            return []
        return sorted(jars_dir.glob("*.jar"))

    @property
    def main_class(self) -> str | None:
        """
        Main class for this environment (if detected/specified).

        Returns runtime override if set, otherwise reads from lockfile's default entrypoint.
        """
        # Runtime override takes precedence
        if self._runtime_main_class:
            return self._runtime_main_class

        if self.lockfile:
            default_ep = self.lockfile.default_entrypoint
            if default_ep and default_ep in self.lockfile.entrypoints:
                return self.lockfile.entrypoints[default_ep]
            # If no default, use first entrypoint
            if self.lockfile.entrypoints:
                return next(iter(self.lockfile.entrypoints.values()))
        return None

    def get_main_class(self, entrypoint: str | None = None) -> str | None:
        """
        Get main class for a specific entrypoint.

        Args:
            entrypoint: Entrypoint name, or None for default

        Returns:
            Main class string, or None if not found
        """
        if self.lockfile:
            if entrypoint:
                return self.lockfile.entrypoints.get(entrypoint)
            # Use default entrypoint
            default_ep = self.lockfile.default_entrypoint
            if default_ep and default_ep in self.lockfile.entrypoints:
                return self.lockfile.entrypoints[default_ep]
            # If no default, use first entrypoint
            if self.lockfile.entrypoints:
                return next(iter(self.lockfile.entrypoints.values()))
        return None

    @property
    def min_java_version(self) -> int | None:
        """
        Minimum Java version required by this environment.

        Reads from lockfile, or detects from bytecode if not cached.

        Returns:
            Minimum Java version (e.g., 8, 11, 17, 21), or None if no JARs found
        """
        # Try lockfile first
        if self.lockfile and self.lockfile.min_java_version is not None:
            return self.lockfile.min_java_version

        # Detect from bytecode (not cached - lockfile should have it)
        jars_dir = self.path / "jars"
        return detect_environment_java_version(jars_dir)

    @property
    def link_strategy(self) -> str | None:
        """Link strategy used to create this environment."""
        if self.lockfile:
            return self.lockfile.link_strategy
        return None
