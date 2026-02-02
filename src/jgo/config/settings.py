"""
Global settings file parsing for jgo.

Supports jgo settings files with backward compatibility to jgo 1.x.
"""

from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path

from ..constants import default_jgo_cache, default_maven_repo
from .manager import get_settings_path

_log = logging.getLogger(__name__)


class GlobalSettings:
    """
    Global settings loaded from settings file and environment variables.

    Settings file locations (in order of precedence):
    1. ~/.config/jgo.conf (XDG Base Directory standard)
    2. ~/.jgorc (legacy location, for backward compatibility)

    The settings file is an INI file with sections:
    - [settings]: General settings (cache_dir, repo_cache, links, etc.)
    - [repositories]: Maven repositories (name = URL)
    - [shortcuts]: Coordinate shortcuts for the CLI
    - [jvm]: JVM configuration (gc, max_heap, min_heap, jvm_args, properties)
    - [styles]: Style mappings for coordinate output colors (g, a, v, p, c, s, etc.)
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        repo_cache: Path | None = None,
        links: str = "auto",
        repositories: dict[str, str] | None = None,
        shortcuts: dict[str, str] | None = None,
        jvm_config: dict | None = None,
        styles: dict[str, str] | None = None,
    ):
        """
        Initialize configuration.

        Args:
            cache_dir: jgo cache directory (defaults to ~/.cache/jgo)
            repo_cache: Maven repository cache (defaults to ~/.m2/repository)
            links: Link strategy (hard, soft, copy, auto)
            repositories: Maven repositories (name -> URL)
            shortcuts: Coordinate shortcuts
            jvm_config: JVM configuration (gc, max_heap, min_heap, jvm_args, properties)
            styles: Style mappings for coordinate output (key -> Rich color/style)
        """

        self.cache_dir = cache_dir or default_jgo_cache()
        self.repo_cache = repo_cache or default_maven_repo()
        self.links = links
        self.repositories = repositories or {}
        self.shortcuts = shortcuts or {}
        self.jvm_config = jvm_config or {}
        self.styles = styles or {}

    @classmethod
    def load(cls, settings_file: Path | None = None) -> "GlobalSettings":
        """
        Load global settings from file and environment variables.

        Args:
            settings_file: Path to settings file (defaults to ~/.config/jgo.conf, or ~/.jgorc as fallback)

        Returns:
            GlobalSettings instance
        """
        if settings_file is None:
            settings_file = get_settings_path()

        _log.debug(f"Loading settings from: {settings_file}")

        # Start with defaults
        settings = cls._default_config()

        # Load from file if it exists
        if settings_file.exists():
            _log.debug(f"Settings file exists, loading: {settings_file}")
            settings = cls._load_from_file(settings_file, settings)
        else:
            _log.debug(f"Settings file does not exist: {settings_file}")

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
            cache_dir=default_jgo_cache(),
            repo_cache=default_maven_repo(),
            links="auto",
            repositories={},
            shortcuts={},
            jvm_config={},
            styles={},
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

        _log.debug(f"Parsing settings file: {settings_file}")

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
                _log.debug(f"Loaded cache_dir from file: {cache_dir}")
            elif parser.has_option("settings", "cacheDir"):
                # Backward compatibility with jgo 1.x
                cache_dir = Path(parser.get("settings", "cacheDir")).expanduser()
                _log.debug(f"Loaded cacheDir (legacy) from file: {cache_dir}")

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

        # Parse [jvm] section
        jvm_config = dict(base_config.jvm_config)
        if parser.has_section("jvm"):
            for key, value in parser.items("jvm"):
                # Handle comma-separated lists for jvm_args
                if key == "jvm_args":
                    jvm_config[key] = [arg.strip() for arg in value.split(",")]
                # Handle properties subsection (key.subkey format)
                elif "." in key:
                    # properties.foo.bar -> nested dict
                    if "properties" not in jvm_config:
                        jvm_config["properties"] = {}
                    prop_key = key.split(".", 1)[1]
                    jvm_config["properties"][prop_key] = value
                else:
                    jvm_config[key] = value

        # Parse [styles] section
        styles = dict(base_config.styles)
        if parser.has_section("styles"):
            for key, value in parser.items("styles"):
                styles[key] = value

        _log.debug(
            f"Loaded settings: cache_dir={cache_dir}, links={links}, "
            f"repositories={list(repositories.keys())}"
        )

        return cls(
            cache_dir=cache_dir,
            repo_cache=repo_cache,
            links=links,
            repositories=repositories,
            shortcuts=shortcuts,
            jvm_config=jvm_config,
            styles=styles,
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
        jgo_cache_env = os.getenv("JGO_CACHE_DIR")
        if jgo_cache_env:
            cache_dir = Path(jgo_cache_env).expanduser()

        m2_repo_env = os.getenv("M2_REPO")
        if m2_repo_env:
            repo_cache = Path(m2_repo_env).expanduser()

        return cls(
            cache_dir=cache_dir,
            repo_cache=repo_cache,
            links=settings.links,
            repositories=settings.repositories,
            shortcuts=settings.shortcuts,
            jvm_config=settings.jvm_config,
            styles=settings.styles,
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
            "jvm": self.jvm_config,  # Note: key is "jvm" not "jvm_config" for consistency with INI file
            "styles": self.styles,
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

        # Write [styles] section
        if self.styles:
            parser.add_section("styles")
            for key, value in self.styles.items():
                parser.set("styles", key, value)

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


def parse_config_key(key: str, default_section: str = "settings") -> tuple[str, str]:
    """
    Parse a config key into section and key name.

    Args:
        key: Key in format "section.key" or just "key"
        default_section: Default section if not specified (default: "settings")

    Returns:
        Tuple of (section, key_name)

    Examples:
        >>> parse_config_key("cache_dir")
        ('settings', 'cache_dir')
        >>> parse_config_key("repositories.central")
        ('repositories', 'central')
    """
    if "." in key:
        return tuple(key.split(".", 1))
    return default_section, key
