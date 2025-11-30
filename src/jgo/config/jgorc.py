"""
Configuration file parsing for jgo 2.0.

Supports ~/.jgorc configuration files with backward compatibility to jgo 1.x.
"""

import configparser
import os
from pathlib import Path
from typing import Dict, Optional


class JgoConfig:
    """
    Configuration loaded from ~/.jgorc and environment variables.

    The .jgorc file is an INI file with sections:
    - [settings]: General settings (cache_dir, repo_cache, links, etc.)
    - [repositories]: Maven repositories (name = URL)
    - [shortcuts]: Coordinate shortcuts for the CLI
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        repo_cache: Optional[Path] = None,
        links: str = "auto",
        repositories: Optional[Dict[str, str]] = None,
        shortcuts: Optional[Dict[str, str]] = None,
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
        self.cache_dir = cache_dir or Path.home() / ".cache" / "jgo"
        self.repo_cache = repo_cache or Path.home() / ".m2" / "repository"
        self.links = links
        self.repositories = repositories or {}
        self.shortcuts = shortcuts or {}

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "JgoConfig":
        """
        Load configuration from file and environment variables.

        Args:
            config_file: Path to config file (defaults to ~/.jgorc)

        Returns:
            JgoConfig instance
        """
        if config_file is None:
            config_file = Path.home() / ".jgorc"

        # Start with defaults
        config = cls._default_config()

        # Load from file if it exists
        if config_file.exists():
            config = cls._load_from_file(config_file, config)

        # Override with environment variables
        config = cls._apply_environment_variables(config)

        return config

    @classmethod
    def _default_config(cls) -> "JgoConfig":
        """
        Create default configuration.

        Returns:
            JgoConfig with default values
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
        cls, config_file: Path, base_config: "JgoConfig"
    ) -> "JgoConfig":
        """
        Load configuration from INI file.

        Args:
            config_file: Path to .jgorc file
            base_config: Base configuration to build upon

        Returns:
            Updated JgoConfig
        """
        parser = configparser.ConfigParser()
        parser.read(config_file)

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
    def _apply_environment_variables(cls, config: "JgoConfig") -> "JgoConfig":
        """
        Apply environment variable overrides.

        Supports:
        - JGO_CACHE_DIR: Override cache directory
        - M2_REPO: Override Maven repository cache

        Args:
            config: Base configuration

        Returns:
            Updated JgoConfig
        """
        cache_dir = config.cache_dir
        repo_cache = config.repo_cache

        # Check environment variables
        if os.getenv("JGO_CACHE_DIR"):
            cache_dir = Path(os.getenv("JGO_CACHE_DIR")).expanduser()

        if os.getenv("M2_REPO"):
            repo_cache = Path(os.getenv("M2_REPO")).expanduser()

        return cls(
            cache_dir=cache_dir,
            repo_cache=repo_cache,
            links=config.links,
            repositories=config.repositories,
            shortcuts=config.shortcuts,
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

        Args:
            coordinate: Coordinate string (may contain shortcuts)

        Returns:
            Expanded coordinate string
        """
        if not self.shortcuts:
            return coordinate

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
