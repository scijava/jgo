"""Tests for JgoConfig class and config file loading."""

import tempfile
from pathlib import Path

from jgo.config.jgorc import JgoConfig


def test_xdg_config_precedence():
    """Test that XDG config location takes precedence over legacy .jgorc."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create XDG config location
        xdg_config_dir = tmpdir / ".config" / "jgo"
        xdg_config_dir.mkdir(parents=True)
        xdg_config = xdg_config_dir / "config"

        # Create legacy config location
        legacy_config = tmpdir / ".jgorc"

        # Write different values to each
        xdg_config.write_text("""[settings]
cache_dir = /xdg/cache
links = soft

[repositories]
xdg_repo = https://xdg.example.com/maven2
""")

        legacy_config.write_text("""[settings]
cache_dir = /legacy/cache
links = hard

[repositories]
legacy_repo = https://legacy.example.com/maven2
""")

        # Temporarily override Path.home() to use our tmpdir
        original_home = Path.home
        Path.home = lambda: tmpdir

        try:
            # Load config - should prefer XDG location
            config = JgoConfig.load()

            # Verify XDG config was loaded
            assert str(config.cache_dir) == "/xdg/cache"
            assert config.links == "soft"
            assert "xdg_repo" in config.repositories
            assert config.repositories["xdg_repo"] == "https://xdg.example.com/maven2"

            # Verify legacy config was NOT loaded
            assert "legacy_repo" not in config.repositories
        finally:
            Path.home = original_home


def test_legacy_config_fallback():
    """Test that legacy .jgorc is used when XDG config doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create only legacy config (no XDG config)
        legacy_config = tmpdir / ".jgorc"
        legacy_config.write_text("""[settings]
cache_dir = /legacy/cache
links = hard

[repositories]
legacy_repo = https://legacy.example.com/maven2
""")

        # Temporarily override Path.home() to use our tmpdir
        original_home = Path.home
        Path.home = lambda: tmpdir

        try:
            # Load config - should use legacy location
            config = JgoConfig.load()

            # Verify legacy config was loaded
            assert str(config.cache_dir) == "/legacy/cache"
            assert config.links == "hard"
            assert "legacy_repo" in config.repositories
            assert (
                config.repositories["legacy_repo"]
                == "https://legacy.example.com/maven2"
            )
        finally:
            Path.home = original_home


def test_no_config_file():
    """Test that defaults are used when no config file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Don't create any config files

        # Temporarily override Path.home() to use our tmpdir
        original_home = Path.home
        Path.home = lambda: tmpdir

        try:
            # Load config - should use defaults
            config = JgoConfig.load()

            # Verify defaults
            assert config.cache_dir == tmpdir / ".cache" / "jgo"
            assert config.repo_cache == tmpdir / ".m2" / "repository"
            assert config.links == "auto"
            assert config.repositories == {}
            assert config.shortcuts == {}
        finally:
            Path.home = original_home


def test_explicit_config_file():
    """Test that explicit config file path works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a custom config file
        custom_config = tmpdir / "my-custom-config"
        custom_config.write_text("""[settings]
cache_dir = /custom/cache

[repositories]
custom_repo = https://custom.example.com/maven2
""")

        # Load with explicit path
        config = JgoConfig.load(config_file=custom_config)

        # Verify custom config was loaded
        assert str(config.cache_dir) == "/custom/cache"
        assert "custom_repo" in config.repositories
        assert config.repositories["custom_repo"] == "https://custom.example.com/maven2"
