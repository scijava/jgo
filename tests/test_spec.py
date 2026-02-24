#!/usr/bin/env python3
"""
Unit tests for EnvironmentSpec and LockFile functionality.
"""

import tempfile
from pathlib import Path

import pytest

from jgo.env import EnvironmentSpec, LockedDependency, LockFile


def test_environment_spec_creation():
    """Test basic EnvironmentSpec creation."""
    spec = EnvironmentSpec(
        name="test-env",
        description="Test environment",
        coordinates=["org.example:artifact:1.0.0"],
    )
    assert spec.name == "test-env"
    assert spec.description == "Test environment"
    assert len(spec.coordinates) == 1
    assert spec.coordinates[0] == "org.example:artifact:1.0.0"


def test_environment_spec_save_and_load():
    """Test saving and loading jgo.toml files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Create and save spec
        spec = EnvironmentSpec(
            name="imagej-analysis",
            description="ImageJ with Python scripting",
            java_version="17",
            java_vendor="adoptium",
            repositories={"scijava": "https://maven.scijava.org/content/groups/public"},
            coordinates=[
                "net.imagej:imagej:2.15.0",
                "org.scijava:scripting-jython:1.0.0",
            ],
            exclusions=["org.scijava:scijava-common"],
            entrypoints={
                "imagej": "net.imagej.Main",
                "repl": "org.scijava.script.ScriptREPL",
            },
            default_entrypoint="imagej",
            link_strategy="hard",
            cache_dir=".jgo",
        )
        spec.save(spec_path)

        # Verify file was created
        assert spec_path.exists()

        # Load and verify
        loaded_spec = EnvironmentSpec.load(spec_path)
        assert loaded_spec.name == "imagej-analysis"
        assert loaded_spec.description == "ImageJ with Python scripting"
        assert loaded_spec.java_version == "17"
        assert loaded_spec.java_vendor == "adoptium"
        assert (
            loaded_spec.repositories["scijava"]
            == "https://maven.scijava.org/content/groups/public"
        )
        assert len(loaded_spec.coordinates) == 2
        assert "net.imagej:imagej:2.15.0" in loaded_spec.coordinates
        assert len(loaded_spec.exclusions) == 1
        assert loaded_spec.exclusions[0] == "org.scijava:scijava-common"
        assert loaded_spec.entrypoints["imagej"] == "net.imagej.Main"
        assert loaded_spec.default_entrypoint == "imagej"
        assert loaded_spec.link_strategy == "hard"
        assert loaded_spec.cache_dir == ".jgo"


def test_environment_spec_minimal():
    """Test minimal EnvironmentSpec with only required fields."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Create minimal spec (only coordinates required)
        spec = EnvironmentSpec(
            coordinates=["org.python:jython-standalone:2.7.3"],
        )
        spec.save(spec_path)

        # Load and verify
        loaded_spec = EnvironmentSpec.load(spec_path)
        assert loaded_spec.name is None
        assert loaded_spec.description is None
        assert loaded_spec.java_version == "auto"
        assert loaded_spec.java_vendor is None
        assert len(loaded_spec.coordinates) == 1
        assert loaded_spec.coordinates[0] == "org.python:jython-standalone:2.7.3"


def test_environment_spec_validation_missing_coordinates():
    """Test that EnvironmentSpec allows missing/empty coordinates (for bare envs)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Write TOML with no coordinates field — should load fine as an empty env
        spec_path.write_text("""
[environment]
name = "test"

[dependencies]
# No coordinates field
""")

        spec = EnvironmentSpec.load(spec_path)
        assert spec.coordinates == []

        # Also allow completely missing [dependencies] section
        spec_path.write_text("""
[environment]
name = "test"
""")
        spec = EnvironmentSpec.load(spec_path)
        assert spec.coordinates == []


def test_environment_spec_validation_invalid_coordinate():
    """Test that EnvironmentSpec validates coordinate format."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Write invalid TOML (bad coordinate format)
        spec_path.write_text("""
[dependencies]
coordinates = ["invalid"]  # Missing artifactId
""")

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid coordinate format"):
            EnvironmentSpec.load(spec_path)


def test_environment_spec_validation_invalid_exclusion():
    """Test that EnvironmentSpec validates exclusion format."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Write invalid TOML (exclusion with version)
        spec_path.write_text("""
[dependencies]
coordinates = ["org.example:artifact:1.0.0"]
exclusions = ["org.bad:excluded:1.0.0"]  # Should be G:A only
""")

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid exclusion format"):
            EnvironmentSpec.load(spec_path)


def test_environment_spec_validation_invalid_link_strategy():
    """Test that EnvironmentSpec validates link strategy."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Write invalid TOML (bad link strategy)
        spec_path.write_text("""
[dependencies]
coordinates = ["org.example:artifact:1.0.0"]

[settings]
links = "invalid"  # Should be hard, soft, copy, or auto
""")

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid link strategy"):
            EnvironmentSpec.load(spec_path)


def test_environment_spec_validation_invalid_default_entrypoint():
    """Test that EnvironmentSpec validates default entrypoint exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"

        # Write invalid TOML (default entrypoint doesn't exist)
        spec_path.write_text("""
[dependencies]
coordinates = ["org.example:artifact:1.0.0"]

[entrypoints]
main = "org.example.Main"
default = "nonexistent"  # This entrypoint doesn't exist
""")

        # Should raise ValueError
        with pytest.raises(ValueError, match="Default entrypoint .* not found"):
            EnvironmentSpec.load(spec_path)


def test_environment_spec_validation_reserved_entrypoint_name():
    """Test that EnvironmentSpec rejects 'default' as an entrypoint name."""
    # Using constructor should fail
    with pytest.raises(ValueError, match='Entrypoint name "default" is reserved'):
        EnvironmentSpec(
            coordinates=["org.example:artifact:1.0.0"],
            entrypoints={"default": "org.example.Main"},
            default_entrypoint="default",
        )

    # Loading from TOML should also fail
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_path = Path(tmp_dir) / "jgo.toml"
        spec_path.write_text("""
[dependencies]
coordinates = ["org.example:artifact:1.0.0"]

[entrypoints]
default = "org.example.Main"
""")
        with pytest.raises(ValueError, match='Entrypoint name "default" is reserved'):
            EnvironmentSpec.load(spec_path)


def test_environment_spec_get_main_class():
    """Test get_main_class method."""
    spec = EnvironmentSpec(
        coordinates=["org.example:artifact:1.0.0"],
        entrypoints={
            "main": "org.example.Main",
            "repl": "org.example.REPL",
        },
        default_entrypoint="main",
    )

    # Get default entrypoint
    assert spec.get_main_class() == "org.example.Main"

    # Get specific entrypoint
    assert spec.get_main_class("repl") == "org.example.REPL"

    # Get non-existent entrypoint (should raise)
    with pytest.raises(ValueError, match="Entrypoint .* not found"):
        spec.get_main_class("nonexistent")

    # Spec with no entrypoints
    spec_no_eps = EnvironmentSpec(
        coordinates=["org.example:artifact:1.0.0"],
    )
    assert spec_no_eps.get_main_class() is None


def test_locked_dependency_creation():
    """Test LockedDependency creation."""
    dep = LockedDependency(
        groupId="org.example",
        artifactId="artifact",
        version="1.0.0",
        packaging="jar",
        sha256="abc123",
    )
    assert dep.groupId == "org.example"
    assert dep.artifactId == "artifact"
    assert dep.version == "1.0.0"
    assert dep.packaging == "jar"
    assert dep.sha256 == "abc123"


def test_locked_dependency_to_dict():
    """Test LockedDependency serialization to dict."""
    dep = LockedDependency(
        groupId="org.example",
        artifactId="artifact",
        version="1.0.0",
        packaging="jar",
        classifier="tests",
        sha256="abc123",
    )
    data = dep.to_dict()
    assert data["groupId"] == "org.example"
    assert data["artifactId"] == "artifact"
    assert data["version"] == "1.0.0"
    assert data["packaging"] == "jar"
    assert data["classifier"] == "tests"
    assert data["sha256"] == "abc123"


def test_locked_dependency_from_dict():
    """Test LockedDependency deserialization from dict."""
    data = {
        "groupId": "org.example",
        "artifactId": "artifact",
        "version": "1.0.0",
        "packaging": "jar",
        "classifier": "tests",
        "sha256": "abc123",
    }
    dep = LockedDependency.from_dict(data)
    assert dep.groupId == "org.example"
    assert dep.artifactId == "artifact"
    assert dep.version == "1.0.0"
    assert dep.packaging == "jar"
    assert dep.classifier == "tests"
    assert dep.sha256 == "abc123"


def test_lockfile_creation():
    """Test LockFile creation."""
    dep1 = LockedDependency(
        groupId="org.example",
        artifactId="artifact1",
        version="1.0.0",
    )
    dep2 = LockedDependency(
        groupId="org.example",
        artifactId="artifact2",
        version="2.0.0",
    )

    lockfile = LockFile(
        dependencies=[dep1, dep2],
        environment_name="test-env",
        min_java_version=17,
        entrypoints={"main": "org.example.Main"},
        default_entrypoint="main",
    )

    assert len(lockfile.dependencies) == 2
    assert lockfile.environment_name == "test-env"
    assert lockfile.min_java_version == 17
    assert lockfile.entrypoints["main"] == "org.example.Main"
    assert lockfile.default_entrypoint == "main"


def test_lockfile_save_and_load():
    """Test saving and loading jgo.lock.toml files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "jgo.lock.toml"

        # Create dependencies
        deps = [
            LockedDependency(
                groupId="net.imagej",
                artifactId="imagej",
                version="2.15.0",
                sha256="abc123def456",
            ),
            LockedDependency(
                groupId="org.scijava",
                artifactId="scijava-common",
                version="2.97.0",
                sha256="ghi789jkl012",
            ),
        ]

        # Create and save lockfile
        lockfile = LockFile(
            dependencies=deps,
            environment_name="imagej-analysis",
            min_java_version=17,
            entrypoints={
                "imagej": "net.imagej.Main",
                "repl": "org.scijava.script.ScriptREPL",
            },
            default_entrypoint="imagej",
        )
        lockfile.save(lock_path)

        # Verify file was created
        assert lock_path.exists()

        # Load and verify
        loaded_lockfile = LockFile.load(lock_path)
        assert len(loaded_lockfile.dependencies) == 2
        assert loaded_lockfile.environment_name == "imagej-analysis"
        assert loaded_lockfile.min_java_version == 17
        assert loaded_lockfile.entrypoints["imagej"] == "net.imagej.Main"
        assert loaded_lockfile.default_entrypoint == "imagej"

        # Verify dependencies
        dep0 = loaded_lockfile.dependencies[0]
        assert dep0.groupId == "net.imagej"
        assert dep0.artifactId == "imagej"
        assert dep0.version == "2.15.0"
        assert dep0.sha256 == "abc123def456"


def test_lockfile_metadata():
    """Test that lockfile includes metadata section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "jgo.lock.toml"

        lockfile = LockFile(
            dependencies=[],
            environment_name="test",
        )
        lockfile.save(lock_path)

        # Read the raw TOML to verify metadata
        content = lock_path.read_text()
        assert "[metadata]" in content
        assert "generated" in content
        assert "jgo_version" in content


def test_lockfile_validation_reserved_entrypoint_name():
    """Test that LockFile rejects 'default' as an entrypoint name."""
    # Using constructor should fail
    with pytest.raises(ValueError, match='Entrypoint name "default" is reserved'):
        LockFile(
            dependencies=[],
            entrypoints={"default": "org.example.Main"},
            default_entrypoint="default",
        )

    # Loading from TOML should also fail
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "jgo.lock.toml"
        lock_path.write_text("""
dependencies = []

[metadata]
generated = "2025-01-01T00:00:00+00:00"
jgo_version = "2.0.0"

[entrypoints]
default = "org.example.Main"
""")
        with pytest.raises(ValueError, match='Entrypoint name "default" is reserved'):
            LockFile.load(lock_path)
