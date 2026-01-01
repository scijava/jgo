"""Tests for GlobalSettings class and settings file loading."""

from jgo.config import GlobalSettings


def test_xdg_config_precedence(monkeypatch, tmp_path):
    """Test that XDG config location takes precedence over legacy .jgorc."""
    # Mock home directory to return our test directory
    # Patch in constants module where it's imported and used
    monkeypatch.setattr("jgo.constants.get_user_home", lambda: tmp_path)
    # Unset XDG_CONFIG_HOME so it doesn't override our test HOME
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    # Unset JGO_CACHE_DIR to prevent env var override
    monkeypatch.delenv("JGO_CACHE_DIR", raising=False)

    # Create XDG config location
    xdg_config_dir = tmp_path / ".config"
    xdg_config_dir.mkdir(parents=True)
    xdg_config = xdg_config_dir / "jgo.conf"

    # Create legacy config location
    legacy_config = tmp_path / ".jgorc"

    # Use paths relative to tmp_path for platform independence
    xdg_cache_path = tmp_path / "xdg_cache"
    legacy_cache_path = tmp_path / "legacy_cache"

    # Write different values to each
    xdg_config.write_text(f"""[settings]
cache_dir = {xdg_cache_path}
links = soft

[repositories]
xdg_repo = https://xdg.example.com/maven2
""")

    legacy_config.write_text(f"""[settings]
cache_dir = {legacy_cache_path}
links = hard

[repositories]
legacy_repo = https://legacy.example.com/maven2
""")

    # Load config - should prefer XDG location
    config = GlobalSettings.load()

    # Verify XDG config was loaded
    assert config.cache_dir == xdg_cache_path
    assert config.links == "soft"
    assert "xdg_repo" in config.repositories
    assert config.repositories["xdg_repo"] == "https://xdg.example.com/maven2"

    # Verify legacy config was NOT loaded
    assert "legacy_repo" not in config.repositories


def test_legacy_config_fallback(monkeypatch, tmp_path):
    """Test that legacy .jgorc is used when XDG config doesn't exist."""
    # Mock home directory to return our test directory
    # Patch in constants module where it's imported and used
    monkeypatch.setattr("jgo.constants.get_user_home", lambda: tmp_path)
    # Unset XDG_CONFIG_HOME to ensure clean test environment
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    # Unset JGO_CACHE_DIR to prevent env var override
    monkeypatch.delenv("JGO_CACHE_DIR", raising=False)

    # Create only legacy config (no XDG config)
    legacy_config = tmp_path / ".jgorc"
    legacy_cache_path = tmp_path / "legacy_cache"

    legacy_config.write_text(f"""[settings]
cache_dir = {legacy_cache_path}
links = hard

[repositories]
legacy_repo = https://legacy.example.com/maven2
""")

    # Load config - should use legacy location
    config = GlobalSettings.load()

    # Verify legacy config was loaded
    assert config.cache_dir == legacy_cache_path
    assert config.links == "hard"
    assert "legacy_repo" in config.repositories
    assert config.repositories["legacy_repo"] == "https://legacy.example.com/maven2"


def test_no_config_file(monkeypatch, tmp_path):
    """Test that defaults are used when no config file exists."""
    # Mock home directory to return our test directory (no config files)
    # Patch in constants module where it's imported and used
    monkeypatch.setattr("jgo.constants.get_user_home", lambda: tmp_path)
    # Unset XDG_CONFIG_HOME to ensure clean test environment
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    # Unset environment variables that could override defaults
    monkeypatch.delenv("JGO_CACHE_DIR", raising=False)
    monkeypatch.delenv("M2_REPO", raising=False)
    monkeypatch.delenv("M2_HOME", raising=False)

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
    custom_cache_path = tmp_path / "custom_cache"

    custom_config.write_text(f"""[settings]
cache_dir = {custom_cache_path}

[repositories]
custom_repo = https://custom.example.com/maven2
""")

    # Load with explicit path
    config = GlobalSettings.load(settings_file=custom_config)

    # Verify custom config was loaded
    assert config.cache_dir == custom_cache_path
    assert "custom_repo" in config.repositories
    assert config.repositories["custom_repo"] == "https://custom.example.com/maven2"
