#!/usr/bin/env python3
"""
Unit tests for the Environment layer.
"""

import tempfile
from pathlib import Path

from jgo.env import Environment, EnvironmentBuilder, LinkStrategy
from jgo.maven import MavenContext


def test_environment_creation():
    """Test that Environment can be created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        env_path = Path(tmp_dir) / "test_env"
        env = Environment(env_path)
        assert env is not None
        assert env.path == env_path
        assert env.manifest_path == env_path / "manifest.json"


def test_environment_classpath():
    """Test classpath property."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        env_path = Path(tmp_dir) / "test_env"
        env = Environment(env_path)

        # Should return empty list when no jars directory exists
        assert env.classpath == []

        # Create jars directory and add a fake jar
        jars_dir = env_path / "jars"
        jars_dir.mkdir(parents=True)
        fake_jar = jars_dir / "fake.jar"
        fake_jar.touch()

        # Should return list of jar files
        classpath = env.classpath
        assert len(classpath) == 1
        assert classpath[0] == fake_jar


def test_environment_main_class():
    """Test main_class property."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        env_path = Path(tmp_dir) / "test_env"
        env = Environment(env_path)

        # Should return None when no main class file or manifest exists
        assert env.main_class is None

        # Set main class via manifest
        env.set_main_class("org.example.Main")
        assert env.main_class == "org.example.Main"

        # Test that main class is saved to manifest
        assert env.manifest.get("main_class") == "org.example.Main"


def test_environment_builder_creation():
    """Test that EnvironmentBuilder can be created."""
    maven = MavenContext()
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_dir = Path(tmp_dir) / "cache"
        builder = EnvironmentBuilder(maven_context=maven, cache_dir=cache_dir)
        assert builder is not None
        assert builder.maven_context == maven
        assert builder.cache_dir == cache_dir
        assert builder.link_strategy == LinkStrategy.AUTO


def test_cache_key_generation():
    """Test cache key generation."""
    maven = MavenContext()
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_dir = Path(tmp_dir) / "cache"
        builder = EnvironmentBuilder(maven_context=maven, cache_dir=cache_dir)

        # Create some test components
        project1 = maven.project("org.example", "artifact1")
        component1 = project1.at_version("1.0.0")
        project2 = maven.project("org.example", "artifact2")
        component2 = project2.at_version("2.0.0")

        components = [component1, component2]
        key = builder._cache_key(components)

        # Should generate a hash
        assert isinstance(key, str)
        assert len(key) == 16  # SHA256 hex digest truncated to 16 chars


def test_link_strategy_enum():
    """Test LinkStrategy enum values."""
    assert LinkStrategy.HARD.value == "hard"
    assert LinkStrategy.SOFT.value == "soft"
    assert LinkStrategy.COPY.value == "copy"
    assert LinkStrategy.AUTO.value == "auto"


def test_link_file():
    """Test link_file function."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        source_file = Path(tmp_dir) / "source.txt"
        source_file.write_text("test content")

        target_file = Path(tmp_dir) / "link.txt"

        # Test hard link
        try:
            from jgo.env.linking import link_file, LinkStrategy

            link_file(source_file, target_file, LinkStrategy.HARD)
            assert target_file.exists()
            assert target_file.is_file()
            # Hard links point to the same inode, not the same path
            assert target_file.stat().st_ino == source_file.stat().st_ino
        except OSError:
            # Hard link might not work on some filesystems
            pass


if __name__ == "__main__":
    test_environment_creation()
    test_environment_classpath()
    test_environment_main_class()
    test_environment_builder_creation()
    test_cache_key_generation()
    test_link_strategy_enum()
    test_link_file()
    print("All tests passed!")
