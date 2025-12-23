"""Tests for GlobalSettings class and settings file loading."""

from jgo.config import GlobalSettings


def test_xdg_config_precedence(monkeypatch, tmp_path):
    """Test that XDG config location takes precedence over legacy .jgorc."""
    # Set HOME to our test directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Create XDG config location
    xdg_config_dir = tmp_path / ".config"
    xdg_config_dir.mkdir(parents=True)
    xdg_config = xdg_config_dir / "jgo.conf"

    # Create legacy config location
    legacy_config = tmp_path / ".jgorc"

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

    # Load config - should prefer XDG location
    config = GlobalSettings.load()

    # Verify XDG config was loaded
    assert str(config.cache_dir) == "/xdg/cache"
    assert config.links == "soft"
    assert "xdg_repo" in config.repositories
    assert config.repositories["xdg_repo"] == "https://xdg.example.com/maven2"

    # Verify legacy config was NOT loaded
    assert "legacy_repo" not in config.repositories


def test_legacy_config_fallback(monkeypatch, tmp_path):
    """Test that legacy .jgorc is used when XDG config doesn't exist."""
    # Set HOME to our test directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Create only legacy config (no XDG config)
    legacy_config = tmp_path / ".jgorc"
    legacy_config.write_text("""[settings]
cache_dir = /legacy/cache
links = hard

[repositories]
legacy_repo = https://legacy.example.com/maven2
""")

    # Load config - should use legacy location
    config = GlobalSettings.load()

    # Verify legacy config was loaded
    assert str(config.cache_dir) == "/legacy/cache"
    assert config.links == "hard"
    assert "legacy_repo" in config.repositories
    assert config.repositories["legacy_repo"] == "https://legacy.example.com/maven2"


def test_no_config_file(monkeypatch, tmp_path):
    """Test that defaults are used when no config file exists."""
    # Set HOME to our test directory (no config files)
    monkeypatch.setenv("HOME", str(tmp_path))

    # Load config - should use defaults
    config = GlobalSettings.load()

    # Verify defaults
    assert config.cache_dir == tmp_path / ".cache" / "jgo"
    assert config.repo_cache == tmp_path / ".m2" / "repository"
    assert config.links == "auto"
    assert config.repositories == {}
    assert config.shortcuts == {}


def test_explicit_config_file(tmp_path):
    """Test that explicit config file path works."""
    # Create a custom config file
    custom_config = tmp_path / "my-custom-config"
    custom_config.write_text("""[settings]
cache_dir = /custom/cache

[repositories]
custom_repo = https://custom.example.com/maven2
""")

    # Load with explicit path
    config = GlobalSettings.load(settings_file=custom_config)

    # Verify custom config was loaded
    assert str(config.cache_dir) == "/custom/cache"
    assert "custom_repo" in config.repositories
    assert config.repositories["custom_repo"] == "https://custom.example.com/maven2"
