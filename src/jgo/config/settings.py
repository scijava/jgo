"""
Global settings file parsing for jgo.

Supports jgo settings files with backward compatibility to jgo 1.x.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from .manager import get_settings_path


def config_file_path() -> Path:
    """
    Get the settings file path using XDG Base Directory standard.

    .. deprecated::
        Use :func:`~jgo.config.manager.get_settings_path` instead.

    Returns:
        Path to settings file (~/.config/jgo/config if exists, otherwise ~/.jgorc)
    """
    return get_settings_path()


class GlobalSettings:
    """
    Global settings loaded from settings file and environment variables.

    Settings file locations (in order of precedence):
    1. ~/.config/jgo/config (XDG Base Directory standard)
    2. ~/.jgorc (legacy location, for backward compatibility)

    The settings file is an INI file with sections:
    - [settings]: General settings (cache_dir, repo_cache, links, etc.)
    - [repositories]: Maven repositories (name = URL)
    - [shortcuts]: Coordinate shortcuts for the CLI
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        repo_cache: Path | None = None,
        links: str = "auto",
        repositories: dict[str, str] | None = None,
        shortcuts: dict[str, str] | None = None,
    ):
        """
        Initialize configuration.

        Args:
            cache_dir: jgo cache directory (defaults to ~/.cache/jgo)
            repo_cache: Maven repository cache (defaults to ~/.m2/repository)
            links: Link strategy (hard, soft, copy, auto)
            repositories: Maven repositories (name -> URL)
            shortcuts: Coordinate shortcuts
        """
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "jgo")
        self.repo_cache = repo_cache or (Path.home() / ".m2" / "repository")
        self.links = links
        self.repositories = repositories or {}
        self.shortcuts = shortcuts or {}

    @classmethod
    def load(cls, settings_file: Path | None = None) -> "GlobalSettings":
        """
        Load global settings from file and environment variables.

        Args:
            settings_file: Path to settings file (defaults to ~/.config/jgo/config, then ~/.jgorc)

        Returns:
            GlobalSettings instance
        """
        if settings_file is None:
            settings_file = get_settings_path()

        # Start with defaults
        settings = cls._default_config()

        # Load from file if it exists
        if settings_file.exists():
            settings = cls._load_from_file(settings_file, settings)

        # Override with environment variables
        settings = cls._apply_environment_variables(settings)

        return settings

    @classmethod
    def load_from_opts(cls, opts: dict) -> "GlobalSettings":
        """
        Load global settings based on command options.

        Args:
            opts: Options dictionary (e.g., from argparse Namespace.__dict__)

        Returns:
            GlobalSettings instance (empty if ignore_config is set, otherwise loaded)
        """
        if opts.get("ignore_config"):
            return cls()
        return cls.load()

    @classmethod
    def _default_config(cls) -> "GlobalSettings":
        """
        Create default settings.

        Returns:
            GlobalSettings with default values
        """
        return cls(
            cache_dir=Path.home() / ".cache" / "jgo",
            repo_cache=Path.home() / ".m2" / "repository",
            links="auto",
            repositories={},
            shortcuts={},
        )

    @classmethod
    def _load_from_file(
        cls, settings_file: Path, base_config: "GlobalSettings"
    ) -> "GlobalSettings":
        """
        Load global settings from INI file.

        Args:
            settings_file: Path to settings file
            base_config: Base settings to build upon

        Returns:
            Updated GlobalSettings
        """
        parser = configparser.ConfigParser()
        parser.read(settings_file)

        # Parse [settings] section
        cache_dir = base_config.cache_dir
        repo_cache = base_config.repo_cache
        links = base_config.links

        if parser.has_section("settings"):
            # Handle both old and new setting names
            # Old: cacheDir, m2Repo
            # New: cache_dir, repo_cache

            if parser.has_option("settings", "cache_dir"):
                cache_dir = Path(parser.get("settings", "cache_dir")).expanduser()
            elif parser.has_option("settings", "cacheDir"):
                # Backward compatibility with jgo 1.x
                cache_dir = Path(parser.get("settings", "cacheDir")).expanduser()

            if parser.has_option("settings", "repo_cache"):
                repo_cache = Path(parser.get("settings", "repo_cache")).expanduser()
            elif parser.has_option("settings", "m2Repo"):
                # Backward compatibility with jgo 1.x
                repo_cache = Path(parser.get("settings", "m2Repo")).expanduser()

            if parser.has_option("settings", "links"):
                links = parser.get("settings", "links")

        # Parse [repositories] section
        repositories = dict(base_config.repositories)
        if parser.has_section("repositories"):
            for name, url in parser.items("repositories"):
                repositories[name] = url

        # Parse [shortcuts] section
        shortcuts = dict(base_config.shortcuts)
        if parser.has_section("shortcuts"):
            for name, replacement in parser.items("shortcuts"):
                shortcuts[name] = replacement

        return cls(
            cache_dir=cache_dir,
            repo_cache=repo_cache,
            links=links,
            repositories=repositories,
            shortcuts=shortcuts,
        )

    @classmethod
    def _apply_environment_variables(
        cls, settings: "GlobalSettings"
    ) -> "GlobalSettings":
        """
        Apply environment variable overrides.

        Supports:
        - JGO_CACHE_DIR: Override cache directory
        - M2_REPO: Override Maven repository cache

        Args:
            settings: Base settings

        Returns:
            Updated GlobalSettings
        """
        cache_dir = settings.cache_dir
        repo_cache = settings.repo_cache

        # Check environment variables
        if os.getenv("JGO_CACHE_DIR"):
            cache_dir = Path(os.getenv("JGO_CACHE_DIR")).expanduser()

        if os.getenv("M2_REPO"):
            repo_cache = Path(os.getenv("M2_REPO")).expanduser()

        return cls(
            cache_dir=cache_dir,
            repo_cache=repo_cache,
            links=settings.links,
            repositories=settings.repositories,
            shortcuts=settings.shortcuts,
        )

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "cache_dir": self.cache_dir,
            "repo_cache": self.repo_cache,
            "links": self.links,
            "repositories": self.repositories,
            "shortcuts": self.shortcuts,
        }

    def expand_shortcuts(self, coordinate: str) -> str:
        """
        Expand shortcuts in a coordinate string.

        Supports composition with '+': shortcuts can be combined.
        Example: If shortcuts = {"repl": "org.scijava:scijava-common@ScriptREPL",
                                 "groovy": "org.scijava:scripting-groovy@GroovySh"}
                 Then "repl+groovy" expands to "org.scijava:scijava-common@ScriptREPL+org.scijava:scripting-groovy@GroovySh"

        Args:
            coordinate: Coordinate string (may contain shortcuts and '+' composition)

        Returns:
            Expanded coordinate string
        """
        if not self.shortcuts:
            return coordinate

        # Split on + for composition support
        parts = coordinate.split("+")
        expanded_parts = []

        for part in parts:
            # Expand each part individually
            expanded_part = self._expand_single_shortcut(part)
            expanded_parts.append(expanded_part)

        return "+".join(expanded_parts)

    def _expand_single_shortcut(self, coordinate: str) -> str:
        """
        Expand shortcuts in a single coordinate (no '+' composition).

        Args:
            coordinate: Single coordinate string (may contain shortcuts)

        Returns:
            Expanded coordinate string
        """
        # Apply shortcuts iteratively (in case shortcuts reference other shortcuts)
        max_iterations = 10  # Prevent infinite loops
        used_shortcuts = set()

        for _ in range(max_iterations):
            matched = False
            for shortcut, replacement in self.shortcuts.items():
                if shortcut not in used_shortcuts and coordinate.startswith(shortcut):
                    coordinate = replacement + coordinate[len(shortcut) :]
                    used_shortcuts.add(shortcut)
                    matched = True
                    break

            if not matched:
                break

        return coordinate

    def save(self, settings_file: Path | None = None) -> None:
        """
        Save settings to file.

        Args:
            settings_file: Path to save to (defaults to standard location)
        """
        if settings_file is None:
            settings_file = get_settings_path()

        # Ensure parent directory exists
        settings_file.parent.mkdir(parents=True, exist_ok=True)

        parser = configparser.ConfigParser()

        # Write [settings] section
        parser.add_section("settings")
        parser.set("settings", "cache_dir", str(self.cache_dir))
        parser.set("settings", "repo_cache", str(self.repo_cache))
        parser.set("settings", "links", self.links)

        # Write [repositories] section
        if self.repositories:
            parser.add_section("repositories")
            for name, url in self.repositories.items():
                parser.set("repositories", name, url)

        # Write [shortcuts] section
        if self.shortcuts:
            parser.add_section("shortcuts")
            for name, replacement in self.shortcuts.items():
                parser.set("shortcuts", name, replacement)

        # Write to file
        with open(settings_file, "w") as f:
            parser.write(f)

    def set_setting(self, key: str, value: str) -> None:
        """
        Set a value in the [settings] section.

        Args:
            key: Setting name (cache_dir, repo_cache, links)
            value: Setting value
        """
        if key == "cache_dir":
            self.cache_dir = Path(value).expanduser()
        elif key == "repo_cache":
            self.repo_cache = Path(value).expanduser()
        elif key == "links":
            self.links = value
        else:
            raise ValueError(f"Unknown setting: {key}")

    def set_repository(self, name: str, url: str) -> None:
        """
        Add or update a repository.

        Args:
            name: Repository name
            url: Repository URL
        """
        self.repositories[name] = url

    def set_shortcut(self, name: str, replacement: str) -> None:
        """
        Add or update a shortcut.

        Args:
            name: Shortcut name
            replacement: Replacement coordinate
        """
        self.shortcuts[name] = replacement

    def unset_setting(self, key: str) -> None:
        """
        Reset a setting to its default value.

        Args:
            key: Setting name (cache_dir, repo_cache, links)
        """
        defaults = self._default_config()
        if key == "cache_dir":
            self.cache_dir = defaults.cache_dir
        elif key == "repo_cache":
            self.repo_cache = defaults.repo_cache
        elif key == "links":
            self.links = defaults.links
        else:
            raise ValueError(f"Unknown setting: {key}")

    def unset_repository(self, name: str) -> None:
        """
        Remove a repository.

        Args:
            name: Repository name
        """
        if name in self.repositories:
            del self.repositories[name]

    def unset_shortcut(self, name: str) -> None:
        """
        Remove a shortcut.

        Args:
            name: Shortcut name
        """
        if name in self.shortcuts:
            del self.shortcuts[name]
