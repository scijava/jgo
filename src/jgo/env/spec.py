"""
Environment specification (jgo.toml) parsing and generation.

This module handles reading and writing jgo.toml files which define
reproducible Java environments.
"""

from __future__ import annotations

from pathlib import Path

from ..util.serialization import FieldValidatorMixin, TOMLSerializableMixin


class EnvironmentSpec(TOMLSerializableMixin, FieldValidatorMixin):
    """
    Specification for a jgo environment from a jgo.toml file.

    Schema:
        [environment]
        name = "my-environment"
        description = "Optional description"

        [java]
        version = "17"  # Or ">=11", "11-17", or "auto" (default)
        vendor = "corretto"  # Optional (default is "zulu")

        [repositories]
        central = "https://repo.maven.apache.org/maven2"
        scijava = "https://maven.scijava.org/content/groups/public"

        [dependencies]
        coordinates = [
            "net.imagej:imagej:2.17.0",
            "org.scijava:scripting-python:0.4.2",
        ]

        # Maven-style exclusions (G:A only, not G:A:V)
        [dependencies]
        exclusions = [
            "org.scijava:scripting-jruby",
            "org.scijava:scripting-jython"
        ]

        [entrypoints]
        imagej = "net.imagej.Main"
        repl = "org.scijava.script.ScriptREPL"
        default = "imagej"  # Which entrypoint to use by default

        [settings]
        links = "hard"  # hard, soft, copy, auto
        cache_dir = ".jgo"  # Override cache directory
    """

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        java_version: str = "auto",
        java_vendor: str | None = None,
        repositories: dict[str, str] | None = None,
        coordinates: list[str] | None = None,
        exclusions: list[str] | None = None,
        entrypoints: dict[str, str] | None = None,
        default_entrypoint: str | None = None,
        link_strategy: str | None = None,
        cache_dir: str | None = None,
    ):
        self.name = name
        self.description = description
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.repositories = repositories or {}
        self.coordinates = coordinates or []
        self.exclusions = exclusions or []
        self.entrypoints = entrypoints or {}
        self.default_entrypoint = default_entrypoint
        self.link_strategy = link_strategy
        self.cache_dir = cache_dir

    @classmethod
    def _from_dict(cls, data: dict, path: Path | None = None) -> "EnvironmentSpec":
        """Create EnvironmentSpec from parsed TOML dict."""
        # [environment] section (optional)
        env_section = data.get("environment", {})
        name = env_section.get("name")
        description = env_section.get("description")

        # [java] section (optional)
        java_section = data.get("java", {})
        java_version = java_section.get("version", "auto")
        java_vendor = java_section.get("vendor")

        # [repositories] section (optional)
        repositories = data.get("repositories", {})

        # [dependencies] section (required)
        deps_section = data.get("dependencies")
        if not deps_section:
            raise ValueError(
                "Missing required [dependencies] section. "
                "Add at least one coordinate: coordinates = ['group:artifact:version']"
            )

        coordinates = deps_section.get("coordinates")
        if not coordinates:
            raise ValueError(
                "Missing required 'coordinates' in [dependencies] section. "
                "Add at least one: coordinates = ['group:artifact:version']"
            )

        if not isinstance(coordinates, list):
            raise ValueError("'coordinates' must be a list of strings")

        # Validate coordinates format
        for coord in coordinates:
            if not isinstance(coord, str):
                raise ValueError(f"Invalid coordinate (must be string): {coord}")
            parts = coord.split(":")
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid coordinate format '{coord}': "
                    "expected at least 'groupId:artifactId'"
                )

        # [dependencies.exclusions] (optional)
        exclusions = deps_section.get("exclusions", [])
        if exclusions and not isinstance(exclusions, list):
            raise ValueError("'exclusions' must be a list of strings")

        # Validate exclusions format
        for exclusion in exclusions:
            if not isinstance(exclusion, str):
                raise ValueError(f"Invalid exclusion (must be string): {exclusion}")
            # Exclusions should be G:A only (Maven spec)
            parts = exclusion.split(":")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid exclusion format '{exclusion}': "
                    "expected 'groupId:artifactId' (no version)"
                )

        # [entrypoints] section (optional)
        entrypoints_section = data.get("entrypoints", {})
        default_entrypoint = entrypoints_section.pop("default", None)
        entrypoints = entrypoints_section  # Remaining keys are entrypoint definitions

        # Validate entrypoints
        if entrypoints:
            for ep_name, main_class in entrypoints.items():
                if not isinstance(main_class, str):
                    raise ValueError(
                        f"Entrypoint '{ep_name}' must be a string (main class), "
                        f"got {type(main_class)}"
                    )

        # Validate default entrypoint exists
        if default_entrypoint and default_entrypoint not in entrypoints:
            raise ValueError(
                f"Default entrypoint '{default_entrypoint}' not found in [entrypoints]. "
                f"Available: {list(entrypoints.keys())}"
            )

        # [settings] section (optional)
        settings_section = data.get("settings", {})
        link_strategy = settings_section.get("links")
        cache_dir = settings_section.get("cache_dir")

        # Validate link strategy
        if link_strategy and link_strategy not in ("hard", "soft", "copy", "auto"):
            raise ValueError(
                f"Invalid link strategy '{link_strategy}'. "
                "Expected one of: hard, soft, copy, auto"
            )

        return cls(
            name=name,
            description=description,
            java_version=java_version,
            java_vendor=java_vendor,
            repositories=repositories,
            coordinates=coordinates,
            exclusions=exclusions,
            entrypoints=entrypoints,
            default_entrypoint=default_entrypoint,
            link_strategy=link_strategy,
            cache_dir=cache_dir,
        )

    def _to_dict(self) -> dict:
        """Convert EnvironmentSpec to dict for TOML serialization."""
        data = {}

        # [environment] section
        if self.name or self.description:
            env_section = {}
            if self.name:
                env_section["name"] = self.name
            if self.description:
                env_section["description"] = self.description
            data["environment"] = env_section

        # [java] section
        if self.java_version != "auto" or self.java_vendor:
            java_section = {}
            if self.java_version != "auto":
                java_section["version"] = self.java_version
            if self.java_vendor:
                java_section["vendor"] = self.java_vendor
            data["java"] = java_section

        # [repositories] section
        if self.repositories:
            data["repositories"] = self.repositories

        # [dependencies] section (required)
        deps_section = {"coordinates": self.coordinates}
        if self.exclusions:
            deps_section["exclusions"] = self.exclusions
        data["dependencies"] = deps_section

        # [entrypoints] section
        if self.entrypoints or self.default_entrypoint:
            entrypoints_section = dict(self.entrypoints)
            # Only set default if not already in entrypoints
            if self.default_entrypoint and "default" not in entrypoints_section:
                entrypoints_section["default"] = self.default_entrypoint
            data["entrypoints"] = entrypoints_section

        # [settings] section
        settings_section = {}
        if self.link_strategy:
            settings_section["links"] = self.link_strategy
        if self.cache_dir:
            # Convert Path to string for TOML serialization
            settings_section["cache_dir"] = str(self.cache_dir)
        if settings_section:
            data["settings"] = settings_section

        return data

    def get_main_class(self, entrypoint_name: str | None = None) -> str | None:
        """
        Get the main class for a given entrypoint.

        Args:
            entrypoint_name: Name of the entrypoint to use. If None, uses default.

        Returns:
            Main class string, or None if no entrypoints defined

        Raises:
            ValueError: If the specified entrypoint doesn't exist
        """
        if not self.entrypoints:
            return None

        # Use default if no name specified
        if entrypoint_name is None:
            entrypoint_name = self.default_entrypoint

        # If still None, just pick the first one
        if entrypoint_name is None:
            return next(iter(self.entrypoints.values()))

        # Look up the entrypoint
        if entrypoint_name not in self.entrypoints:
            raise ValueError(
                f"Entrypoint '{entrypoint_name}' not found. "
                f"Available: {list(self.entrypoints.keys())}"
            )

        return self.entrypoints[entrypoint_name]

    def __repr__(self) -> str:
        return (
            f"EnvironmentSpec(name={self.name!r}, "
            f"coordinates={len(self.coordinates)} deps, "
            f"entrypoints={list(self.entrypoints.keys())})"
        )
