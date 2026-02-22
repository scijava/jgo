"""
Environment class for jgo.

An environment is a materialized directory containing JAR files ready for
execution.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from ._bytecode import detect_environment_java_version
from ._jar import detect_module_info
from ._lockfile import LockFile
from ._spec import EnvironmentSpec


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
        # Need to scan BOTH jars/ and modules/ directories
        jars_version = detect_environment_java_version(self.path / "jars")
        modules_version = detect_environment_java_version(self.path / "modules")

        return max(jars_version or 0, modules_version or 0) or None

    @property
    def link_strategy(self) -> str | None:
        """Link strategy used to create this environment."""
        if self.lockfile:
            return self.lockfile.link_strategy
        return None

    @property
    def jars_dir(self) -> Path:
        """Directory containing class-path JARs."""
        return self.path / "jars"

    @property
    def modules_dir(self) -> Path:
        """Directory containing module-path JARs."""
        return self.path / "modules"

    @property
    def all_jars(self) -> list[Path]:
        """All JAR files in this environment (both jars/ and modules/)."""
        jars = []
        if self.jars_dir.exists():
            jars.extend(sorted(self.jars_dir.glob("*.jar")))
        if self.modules_dir.exists():
            jars.extend(sorted(self.modules_dir.glob("*.jar")))
        return jars

    @property
    def class_path_jars(self) -> list[Path]:
        """JARs in the jars/ directory (class-path)."""
        if not self.jars_dir.exists():
            return []
        return sorted(self.jars_dir.glob("*.jar"))

    @property
    def module_path_jars(self) -> list[Path]:
        """JARs in the modules/ directory (module-path)."""
        if not self.modules_dir.exists():
            return []
        return sorted(self.modules_dir.glob("*.jar"))

    @property
    def has_modules(self) -> bool:
        """True if environment has any modular JARs."""
        return self.modules_dir.exists() and any(self.modules_dir.glob("*.jar"))

    @property
    def has_classpath(self) -> bool:
        """True if environment has any classpath JARs."""
        return self.jars_dir.exists() and any(self.jars_dir.glob("*.jar"))

    def get_module_for_main_class(self, main_class: str) -> tuple[str | None, bool]:
        """
        Find the module containing a main class.

        Args:
            main_class: Fully qualified class name

        Returns:
            (module_name, is_modular) - module_name is None if not in modular JAR
        """
        # Convert class name to internal path
        class_path = main_class.replace(".", "/") + ".class"

        for jar in self.module_path_jars:
            try:
                with zipfile.ZipFile(jar) as zf:
                    if class_path in zf.namelist():
                        # Found it - get module name from lockfile or detect
                        lockfile = self.lockfile
                        if lockfile:
                            for dep in lockfile.dependencies:
                                if jar.name.startswith(
                                    f"{dep.artifactId}-{dep.version}"
                                ):
                                    if dep.module_name:
                                        return dep.module_name, True
                        # Fallback: detect module name
                        info = detect_module_info(jar)
                        return info.module_name, True
            except (zipfile.BadZipFile, IOError):
                continue

        return None, False
