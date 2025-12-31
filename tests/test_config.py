"""Tests for GlobalSettings class and settings file loading."""

from jgo.config import GlobalSettings


def test_xdg_config_precedence(monkeypatch, tmp_path, caplog):
    """Test that XDG config location takes precedence over legacy .jgorc."""

    # FIXME: On GitHub Actions CI, this test fails with:
    #
    # monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7ff7f8bcb820>
    # tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_xdg_config_precedence0')
    #
    # >       assert str(config.cache_dir) == "/xdg/cache"
    # E       AssertionError: assert '/legacy/cache' == '/xdg/cache'
    # E
    # E         - /xdg/cache
    # E         + /legacy/cache
    #
    # tests/test_config.py:40: AssertionError
    import logging
    import os

    # Enable debug logging to diagnose CI issues
    caplog.set_level(logging.DEBUG)

    # Set HOME to our test directory
    monkeypatch.setenv("HOME", str(tmp_path))
    # Unset XDG_CONFIG_HOME so it doesn't override our test HOME
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

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

    # Print debug info for CI diagnostics
    if os.environ.get("GITHUB_REPOSITORY"):
        print("\n=== DEBUG INFO FOR CI ===")
        print(f"tmp_path: {tmp_path}")
        print(f"XDG file exists: {(tmp_path / '.config' / 'jgo.conf').exists()}")
        print(f"Legacy file exists: {(tmp_path / '.jgorc').exists()}")
        print(f"Loaded cache_dir: {config.cache_dir}")
        print(f"Loaded links: {config.links}")
        print(f"Loaded repositories: {config.repositories}")
        print("\n=== CAPLOG DEBUG OUTPUT ===")
        for record in caplog.records:
            if record.levelname == "DEBUG":
                print(f"{record.name}: {record.message}")
        print("=== END DEBUG INFO ===\n")

    # Verify XDG config was loaded
    assert str(config.cache_dir) == "/xdg/cache", (
        f"Expected XDG cache_dir '/xdg/cache' but got '{config.cache_dir}'. "
        f"Check debug logs above for path resolution details."
    )
    assert config.links == "soft"
    assert "xdg_repo" in config.repositories
    assert config.repositories["xdg_repo"] == "https://xdg.example.com/maven2"

    # Verify legacy config was NOT loaded
    assert "legacy_repo" not in config.repositories


def test_legacy_config_fallback(monkeypatch, tmp_path):
    """Test that legacy .jgorc is used when XDG config doesn't exist."""
    # Set HOME to our test directory
    monkeypatch.setenv("HOME", str(tmp_path))
    # Unset XDG_CONFIG_HOME to ensure clean test environment
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

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
    # Unset XDG_CONFIG_HOME to ensure clean test environment
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

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
