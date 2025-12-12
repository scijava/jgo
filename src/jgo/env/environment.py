"""
Environment class for jgo.

An environment is a materialized directory containing JAR files ready for
execution.
"""

from __future__ import annotations

import json
from pathlib import Path

from .bytecode import detect_environment_java_version
from .lockfile import LockFile
from .spec import EnvironmentSpec


class Environment:
    """
    A materialized Maven environment - a directory containing JARs.
    """

    def __init__(self, path: Path):
        self.path = path
        self._manifest = None

    @property
    def spec_path(self) -> Path:
        """Path to jgo.toml file in this environment."""
        return self.path / "jgo.toml"

    @property
    def lock_path(self) -> Path:
        """Path to jgo.lock.toml file in this environment."""
        return self.path / "jgo.lock.toml"

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

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
        if self.lock_path.exists():
            return LockFile.load(self.lock_path)
        return None

    @property
    def manifest(self) -> dict:
        """Load manifest.json with metadata about this environment."""
        if self._manifest is None:
            if self.manifest_path.exists():
                with open(self.manifest_path) as f:
                    self._manifest = json.load(f)
            else:
                self._manifest = {}
        return self._manifest

    def save_manifest(self):
        """Save manifest.json."""
        with open(self.manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2)

    @property
    def classpath(self) -> list[Path]:
        """List of JAR files in this environment."""
        jars_dir = self.path / "jars"
        if not jars_dir.exists():
            return []
        return sorted(jars_dir.glob("*.jar"))

    @property
    def main_class(self) -> str | None:
        """Main class for this environment (if detected/specified)."""
        return self.manifest.get("main_class")

    def set_main_class(self, main_class: str):
        """Set the main class for this environment."""
        # Ensure the environment directory exists
        self.path.mkdir(parents=True, exist_ok=True)

        # Store in manifest only
        self._manifest = self.manifest  # Load manifest if not already loaded
        self._manifest["main_class"] = main_class
        self.save_manifest()

    @property
    def min_java_version(self) -> int | None:
        """
        Minimum Java version required by this environment.

        Scans bytecode of JAR files to detect the highest class file version,
        then rounds up to the nearest LTS version (8, 11, 17, 21).

        The result is cached in manifest.json to avoid re-scanning.

        Returns:
            Minimum Java version (e.g., 8, 11, 17, 21), or None if no JARs found
        """
        # Check cache first
        cached_version = self.manifest.get("min_java_version")
        if cached_version is not None:
            return cached_version

        # Detect from bytecode
        jars_dir = self.path / "jars"
        detected_version = detect_environment_java_version(jars_dir)

        # Cache the result
        if detected_version is not None:
            self._manifest = self.manifest  # Load manifest if not already loaded
            self._manifest["min_java_version"] = detected_version
            # Only save if environment directory exists
            if self.path.exists():
                self.save_manifest()

        return detected_version
